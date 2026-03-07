from django.db import models

# Create your models here.
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

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
    mission_id = models.CharField(max_length=20, unique=True)
    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE, related_name='sorties')
    pilot = models.ForeignKey(Pilot, on_delete=models.CASCADE, related_name='sorties')
    scheduled_at = models.DateTimeField()
    is_completed = models.BooleanField(default=False)

    # Logic to satisfy your "Block" requirement (Criterion 8)
    def clean(self):
        if self.aircraft.status != 'MC':
            raise ValidationError(f"Cannot schedule: Aircraft {self.aircraft.tail_number} is currently {self.aircraft.get_status_display()}.")
        
        # Add basic pilot rest check logic
        if self.pilot.last_mission_end and (timezone.now() - self.pilot.last_mission_end).total_seconds() < 43200: # 12 hours
             raise ValidationError("Pilot has not met the mandatory 12-hour rest period.")

    def save(self, *args, **kwargs):
        self.full_clean() # Ensures validation runs before saving
        super().save(*args, **kwargs)
        
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError

class Sortie(models.Model):
    # Your existing fields (aircraft, pilot, etc.)
    
    TYPE_CHOICES = [
        ('NIGHT', 'Night Flying'),
        ('FORM', 'Formation'),
        ('GH', 'General Handling'),
        ('IF', 'Instrument Flight'),
    ]
    sortie_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    scheduled_at = models.DateTimeField(default=timezone.now)

    def clean(self):
        super().clean()
        
        # Define currency rules (in days)
        CURRENCY_RULES = {
            'NIGHT': 30,  # Must have flown Night in the last 30 days
            'FORM': 30,   # Formation is high-risk, needs 30-day currency
            'GH': 90,     # General handling is more lenient
            'IF': 60,     # Instrument flight
        }

        days_allowed = CURRENCY_RULES.get(self.sortie_type, 30)
        cutoff_date = timezone.now() - timedelta(days=days_allowed)

        # Check if the pilot has a COMPLETED sortie of this type recently
        recent_flight_exists = Sortie.objects.filter(
            pilot=self.pilot,
            sortie_type=self.sortie_type,
            scheduled_at__gte=cutoff_date,
            is_completed=True
        ).exists()

        # If this isn't their very first flight of this type, check currency
        # (We allow the first one assuming it's an instructor-led checkout)
        total_flights = Sortie.objects.filter(pilot=self.pilot, sortie_type=self.sortie_type).count()

        if total_flights > 0 and not recent_flight_exists:
            raise ValidationError(
                f"Pilot {self.pilot.callsign} is out of currency for {self.get_sortie_type_display()}. "
                f"Last flight was more than {days_allowed} days ago."
            )
            
        if not recent_flight_exists and not self.is_instructional:
            raise ValidationError("Pilot is out of currency. This must be an Instructional flight.")