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