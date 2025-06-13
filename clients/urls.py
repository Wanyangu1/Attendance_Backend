from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientViewSet, AttendanceRecordViewSet

# Create the router and register viewsets
router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'attendance', AttendanceRecordViewSet, basename='attendance')

# Include all routes registered to the router
urlpatterns = [
    path('api/', include(router.urls)),
]
