import logging
from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.shortcuts import render
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic

from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend

from .models import Aircraft, Pilot, Sortie
from .serializers import AircraftSerializer, PilotSerializer, SortieSerializer

# 1. Initialize Logger
logger = logging.getLogger('sorties')

# --- USER VIEWS ---
class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

# --- API VIEWSETS ---

class AircraftViewSet(viewsets.ModelViewSet):
    queryset = Aircraft.objects.all()
    serializer_class = AircraftSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status']
    search_fields = ['tail_number']

    @action(detail=False, methods=['get'], url_path='readiness-report')
    def readiness_report(self, request):
        """Quick summary of fleet readiness for the dashboard."""
        total = self.get_queryset().count()
        ready = self.get_queryset().filter(status='Mision Capable').count()
        maintenance = self.get_queryset().filter(status='In Maintenance').count()
        grounded = self.get_queryset().filter(status='Grounded').count()
        return Response({
            "total_aircraft": total,
            "ready_for_flight": ready,
            "in_maintenance": maintenance,
            "grounded": grounded,
            "readiness_rate": f"{(ready/total)*100:.1f}%" if total > 0 else "0%"
        })

class PilotViewSet(viewsets.ModelViewSet):
    queryset = Pilot.objects.all()
    serializer_class = PilotSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['rank']
    search_fields = ['callsign']

    @action(detail=False, methods=['get'], url_path='currency-status')
    def currency_status(self, request):
        """Returns a list of all pilots and their current flight currency."""
        pilots = Pilot.objects.all()
        report = []
        RULES = {'NIGHT': 30, 'FORM': 30, 'GH': 90, 'IF': 60}

        for pilot in pilots:
            pilot_data = {"callsign": pilot.callsign, "status": {}}
            for s_type, days in RULES.items():
                cutoff = timezone.now() - timedelta(days=days)
                is_current = Sortie.objects.filter(
                    pilot=pilot,
                    sortie_type=s_type,
                    is_completed=True,
                    scheduled_at__gte=cutoff
                ).exists()
                pilot_data["status"][s_type] = "CURRENT" if is_current else "EXPIRED"
            report.append(pilot_data)
        return Response(report)

class SortieViewSet(viewsets.ModelViewSet):
    queryset = Sortie.objects.all()
    serializer_class = SortieSerializer

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except ValidationError as e:
            logger.warning(f"BLOCKED SORTIE: User {request.user} failed validation. Error: {e.messages}")
            return Response(
                {"error": "Mission Validation Failed", "details": e.messages},
                status=status.HTTP_400_BAD_REQUEST
            )