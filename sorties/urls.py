from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AircraftViewSet, PilotViewSet, SortieViewSet

# 1. Initialize the Router
router = DefaultRouter()

# 2. Register your ViewSets
# The router automatically builds the 'currency-status' and 'readiness-report' URLs
router.register(r'aircraft', AircraftViewSet)
router.register(r'pilots', PilotViewSet)
router.register(r'sorties', SortieViewSet)

# 3. Wire up the URL patterns
urlpatterns = [
    path('', include(router.urls)),
]