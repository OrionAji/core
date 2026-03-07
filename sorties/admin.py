from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Aircraft, Pilot, Sortie

@admin.register(Aircraft)
class AircraftAdmin(admin.ModelAdmin):
    list_display = ('tail_number', 'status', 'airframe_hours')
    list_filter = ('status',)
    search_fields = ('tail_number',)

@admin.register(Pilot)
class PilotAdmin(admin.ModelAdmin):
    list_display = ('callsign', 'rank', 'total_hours')
    search_fields = ('callsign', 'rank')

@admin.register(Sortie)
class SortieAdmin(admin.ModelAdmin):
    list_display = ('mission_id', 'aircraft', 'pilot', 'scheduled_at', 'is_completed')
    list_filter = ('is_completed', 'scheduled_at')