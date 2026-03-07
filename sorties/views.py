from django.shortcuts import render

# Create your views here.
import logging  # 1. Add this import

logger = logging.getLogger('sorties')  # 2. Add this initialization

from rest_framework import viewsets, status
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from .models import Aircraft, Pilot, Sortie
from .serializers import AircraftSerializer, PilotSerializer, SortieSerializer

from rest_framework import filters # Add this import
from django_filters.rest_framework import DjangoFilterBackend # Add this import

class AircraftViewSet(viewsets.ModelViewSet):
    queryset = Aircraft.objects.all()
    serializer_class = AircraftSerializer
    
    # Adding Filter and Search capabilities
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status']
    search_fields = ['tail_number']

    # Keep your readiness_report action here too...
    
class PilotViewSet(viewsets.ModelViewSet):
    queryset = Pilot.objects.all()
    serializer_class = PilotSerializer
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['rank']
    search_fields = ['callsign']

class SortieViewSet(viewsets.ModelViewSet):
    queryset = Sortie.objects.all()
    serializer_class = SortieSerializer

    # Combined Create method: Handles Logging AND 400 Responses
    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except ValidationError as e:
            # 1. Log the error for the squadron's safety audit
            # Using str(request.user) ensures it works even if the user is anonymous
            logger.warning(f"BLOCKED SORTIE: User {request.user} failed validation. Error: {e.messages}")
            
            # 2. Return a clean 400 response to the API user
            return Response(
                {"error": "Mission Validation Failed", "details": e.messages},
                status=status.HTTP_400_BAD_REQUEST
            )
            
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic

class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'
    
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from .models import Pilot, Sortie

class PilotViewSet(viewsets.ModelViewSet):
    queryset = Pilot.objects.all()
    serializer_class = PilotSerializer

    @action(detail=False, methods=['get'], url_path='currency-status')
    def currency_status(self, request):
        """
        Returns a list of all pilots and their current flight currency 
        across different sortie types.
        """
        pilots = Pilot.objects.all()
        report = []

        # Define our safety windows again
        RULES = {'NIGHT': 30, 'FORM': 30, 'GH': 90, 'IF': 60}

        for pilot in pilots:
            pilot_data = {
                "callsign": pilot.callsign,
                "status": {}
            }
            
            for s_type, days in RULES.items():
                cutoff = timezone.now() - timedelta(days=days)
                
                # Check if they have a recent completed flight
                is_current = Sortie.objects.filter(
                    pilot=pilot,
                    sortie_type=s_type,
                    is_completed=True,
                    scheduled_at__gte=cutoff
                ).exists()

                pilot_data["status"][s_type] = "CURRENT" if is_current else "EXPIRED"
            
            report.append(pilot_data)

        return Response(report)