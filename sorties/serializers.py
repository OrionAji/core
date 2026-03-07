from rest_framework import serializers
from .models import Aircraft, Pilot, Sortie

class AircraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aircraft
        fields = '__all__'

class PilotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pilot
        fields = '__all__'

class SortieSerializer(serializers.ModelSerializer):
    # These read-only fields help the user see names instead of IDs
    aircraft_detail = AircraftSerializer(source='aircraft', read_only=True)
    pilot_detail = PilotSerializer(source='pilot', read_only=True)

    class Meta:
        model = Sortie
        fields = ['id', 'mission_id', 'aircraft', 'pilot', 'scheduled_at', 'is_completed', 'aircraft_detail', 'pilot_detail']
        
from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import Sortie

class SortieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sortie
        fields = '__all__'

    def validate(self, data):
        pilot = data.get('pilot')
        sortie_type = data.get('sortie_type')
        scheduled_at = data.get('scheduled_at', timezone.now())

        # 1. Define the safety windows (Currency)
        CURRENCY_RULES = {
            'NIGHT': 30,   # 30 days for Night Ops
            'FORM': 30,    # 30 days for Formation (High Risk)
            'GH': 90,      # 90 days for General Handling
            'IF': 60,      # 60 days for Instrument Flight
        }

        days_allowed = CURRENCY_RULES.get(sortie_type, 30)
        cutoff_date = scheduled_at - timedelta(days=days_allowed)

        # 2. Check the Pilot's Flight Log
        # Look for the last COMPLETED sortie of this EXACT type
        last_flight = Sortie.objects.filter(
            pilot=pilot,
            sortie_type=sortie_type,
            is_completed=True,
            scheduled_at__lt=scheduled_at # Look at flights BEFORE this one
        ).order_by('-scheduled_at').first()

        # 3. Apply the Logic
        if last_flight:
            if last_flight.scheduled_at < cutoff_date:
                raise serializers.ValidationError({
                    "pilot": f"Safety Violation: {pilot.callsign} is out of currency for {sortie_type}. "
                             f"Last qualified flight was on {last_flight.scheduled_at.date()}. "
                             f"Limit is {days_allowed} days."
                })
        
        # If no last_flight exists, we assume it's their first time 
        # (or you could force an instructor check here too!)

        return data