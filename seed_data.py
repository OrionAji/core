import os
import django
import random
from django.utils import timezone
from datetime import timedelta

# 1. Setup Django environment
# Change 'core.settings' to 'settings' if your settings.py is in the root
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from sorties.models import Aircraft, Pilot, Sortie

def seed():
    print("🛫 Starting database seed on Desktop...")

    # 2. Create Aircraft
   
    aircraft_data = [
        ('AF-101', 'MC'),    # Mission Capable
        ('AF-102', 'MC'),    # Mission Capable
        ('AF-103', 'MAINT'), # In Maintenance
        ('AF-104', 'GND')    # Grounded
    ]
    
    for tail, stat in aircraft_data:
        obj, created = Aircraft.objects.get_or_create(
            tail_number=tail, 
            defaults={'status': stat, 'airframe_hours': random.randint(100, 500)}
        )
        if created:
            print(f"  + Created Aircraft {tail}")

    # 3. Create Pilots
    pilot_list = [
        ('Maverick', 'CAPT'), 
        ('Rooster', 'LT'), 
        ('Iceman', 'ADM'), 
        ('Phoenix', 'LT')
    ]
    for call, rnk in pilot_list:
        obj, created = Pilot.objects.get_or_create(
            callsign=call, 
            defaults={'rank': rnk, 'total_hours': random.randint(500, 2000)}
        )
        if created:
            print(f"  + Created Pilot {call}")

    # 4. Generate Test Sorties for Maverick
    mav = Pilot.objects.get(callsign='Maverick')
    ac = Aircraft.objects.filter(status='Ready').first()

    if mav and ac:
        # Create a CURRENT Night Flight (5 days ago)
        Sortie.objects.create(
            mission_id="NIGHT-01",
            aircraft=ac,
            pilot=mav,
            sortie_type='NIGHT',
            is_completed=True,
            is_instructional=False,
            scheduled_at=timezone.now() - timedelta(days=5)
        )

        # Create an EXPIRED Formation Flight (45 days ago)
        Sortie.objects.create(
            mission_id="FORM-01",
            aircraft=ac,
            pilot=mav,
            sortie_type='FORM',
            is_completed=True,
            is_instructional=False,
            scheduled_at=timezone.now() - timedelta(days=45)
        )
        print("✅ Maverick's flight history generated.")

    print("\n🚀 Seed complete! Your local database is now healthy.")

if __name__ == '__main__':
    seed()