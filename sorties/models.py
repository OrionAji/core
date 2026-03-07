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