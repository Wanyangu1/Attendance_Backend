from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime, date
import pytz
from .models import Client, AttendanceRecord
from .serializers import ClientSerializer, AttendanceRecordSerializer


# --- CLIENT CRUD VIEWSET ---
class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'email']  # Adjust to your Client model fields
    ordering_fields = ['name', 'created_at']  # Adjust as needed


# --- ATTENDANCE RECORD CRUD VIEWSET ---
class AttendanceRecordViewSet(viewsets.ModelViewSet):
    queryset = AttendanceRecord.objects.all()
    serializer_class = AttendanceRecordSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['date', 'client', 'service', 'location']
    search_fields = ['client']
    ordering_fields = ['date', 'client', 'time_in']

    @action(detail=False, methods=['get'], url_path='today1')
    def today(self, request):
        """Get today's records in Arizona time"""
        az_timezone = pytz.timezone('America/Phoenix')
        today = datetime.now(az_timezone).date()
        records = self.queryset.filter(date=today)
        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='date/(?P<date_str>[^/.]+)')
    def by_date(self, request, date_str=None):
        """Get records for a specific date (format: YYYY-MM-DD)"""
        try:
            target_date = date.fromisoformat(date_str)
            records = self.queryset.filter(date=target_date)
            serializer = self.get_serializer(records, many=True)
            return Response(serializer.data)
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD"}, status=400)