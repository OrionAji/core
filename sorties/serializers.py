from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
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
    # These read-only fields show details in GET requests
    aircraft_detail = AircraftSerializer(source='aircraft', read_only=True)
    pilot_detail = PilotSerializer(source='pilot', read_only=True)

    class Meta:
        model = Sortie
        fields = [
            'id', 'mission_id', 'aircraft', 'pilot', 'sortie_type', 
            'scheduled_at', 'is_completed', 'is_instructional',
            'aircraft_detail', 'pilot_detail'
        ]

    def validate(self, data):
        pilot = data.get('pilot')
        sortie_type = data.get('sortie_type')
        scheduled_at = data.get('scheduled_at', timezone.now())
        is_instructional = data.get('is_instructional', False)

        # 1. Currency Rules
        CURRENCY_RULES = {'NIGHT': 30, 'FORM': 30, 'GH': 90, 'IF': 60}
        days_allowed = CURRENCY_RULES.get(sortie_type, 30)
        cutoff_date = scheduled_at - timedelta(days=days_allowed)

        # 2. Check History
        last_flight = Sortie.objects.filter(
            pilot=pilot,
            sortie_type=sortie_type,
            is_completed=True,
            scheduled_at__lt=scheduled_at
        ).order_by('-scheduled_at').first()

        # 3. Apply Validation (Bypass if it's an instructional flight)
        if last_flight and not is_instructional:
            if last_flight.scheduled_at < cutoff_date:
                raise serializers.ValidationError({
                    "pilot": f"Safety Violation: {pilot.callsign} is out of currency for {sortie_type}. "
                             f"Limit is {days_allowed} days."
                })
        
        return data