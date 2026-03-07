from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AircraftViewSet, PilotViewSet, SortieViewSet

# Using a router automatically creates RESTful paths like /aircraft/ and /aircraft/1/
router = DefaultRouter()
router.register(r'aircraft', AircraftViewSet)
router.register(r'pilots', PilotViewSet)
router.register(r'sorties', SortieViewSet)

urlpatterns = [
    path('', include(router.urls)),
]