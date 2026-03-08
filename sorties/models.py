from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

class Aircraft(models.Model):
    STATUS_CHOICES = [
        ('MC', 'Mission Capable'),
        ('GND', 'Grounded'),
        ('MAINT', 'In Maintenance'),
    ]
    tail_number = models.CharField(max_length=10, unique=True)
    status = models.CharField(max_length=5, choices=STATUS_CHOICES, default='MC')
    airframe_hours = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.tail_number} - {self.get_status_display()}"

class Pilot(models.Model):
    callsign = models.CharField(max_length=50, unique=True)
    rank = models.CharField(max_length=20)
    total_hours = models.DecimalField(max_digits=10, decimal_places=2)
    last_mission_end = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.rank} {self.callsign}"

class Sortie(models.Model):
    TYPE_CHOICES = [
        ('NIGHT', 'Night Flying'),
        ('FORM', 'Formation'),
        ('GH', 'General Handling'),
        ('IF', 'Instrument Flight'),
    ]

    mission_id = models.CharField(max_length=20, unique=True)
    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE, related_name='sorties')
    pilot = models.ForeignKey(Pilot, on_delete=models.CASCADE, related_name='sorties')
    sortie_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='GH')
    scheduled_at = models.DateTimeField(default=timezone.now)
    is_completed = models.BooleanField(default=False)
    is_instructional = models.BooleanField(default=False) # Added for currency bypass

    def clean(self):
        # 1. Check Aircraft Status
        if self.aircraft.status != 'MC':
            raise ValidationError(f"Cannot schedule: Aircraft {self.aircraft.tail_number} is {self.aircraft.get_status_display()}.")
        
        # 2. Check Pilot Rest Period
        if self.pilot.last_mission_end and self.scheduled_at:
            rest_duration = self.scheduled_at - self.pilot.last_mission_end
            if rest_duration.total_seconds() < 43200:
                raise ValidationError(f"Pilot {self.pilot.callsign} requires 12 hours rest. Last mission ended: {self.pilot.last_mission_end.strftime('%H:%M')}")

        # 3. Currency Rules Logic
        CURRENCY_RULES = {'NIGHT': 30, 'FORM': 30, 'GH': 90, 'IF': 60}
        days_allowed = CURRENCY_RULES.get(self.sortie_type, 30)
        cutoff_date = self.scheduled_at - timedelta(days=days_allowed)

        # Look for ANY completed flight of this type in the window before this mission
        recent_flight_exists = Sortie.objects.filter(
            pilot=self.pilot,
            sortie_type=self.sortie_type,
            is_completed=True,
            scheduled_at__gte=cutoff_date,
            scheduled_at__lt=self.scheduled_at
        ).exists()
        
        # BLOCKER: If not recent AND not instructional, block it.
        # This covers BOTH expired pilots AND brand new pilots.
        if not recent_flight_exists and not self.is_instructional:
            raise ValidationError(
                f"Pilot {self.pilot.callsign} is not current for {self.get_sortie_type_display()} "
                f"on {self.scheduled_at.date()}. An instructional flight is required."
            )
             
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

        