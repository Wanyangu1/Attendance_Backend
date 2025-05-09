from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import date
from .models import TimeRecord, PauseRecord
from .serializers import TimeRecordSerializer, PauseRecordSerializer, ResumeRecordSerializer

class CheckInView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        today = date.today()
        if TimeRecord.objects.filter(user=request.user, date=today).exists():
            return Response({'error': 'You have already checked in today'}, status=status.HTTP_400_BAD_REQUEST)

        time_record = TimeRecord(user=request.user, date=today, check_in=timezone.now())
        time_record.full_clean()
        time_record.save()
        serializer = TimeRecordSerializer(time_record)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class CheckOutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        today = date.today()
        try:
            time_record = TimeRecord.objects.get(user=request.user, date=today, check_out__isnull=True)
            time_record.check_out = timezone.now()
            time_record.save()
            serializer = TimeRecordSerializer(time_record)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except TimeRecord.DoesNotExist:
            return Response({'error': 'No active check-in found for today or already checked out'}, status=status.HTTP_400_BAD_REQUEST)

class PauseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Check if there's already an active pause for the user
        active_pause = PauseRecord.objects.filter(
            user=request.user,
            resume_time__isnull=True  # Look for paused records with no resume time
        ).exists()

        if active_pause:
            return Response({'error': 'You already have an active pause. Please resume first.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PauseRecordSerializer(data=request.data)
        if serializer.is_valid():
            PauseRecord.objects.create(
                user=request.user,
                reason=serializer.validated_data['reason'],
                pause_time=timezone.now()
            )
            return Response({'message': 'Pause recorded successfully.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResumeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Retrieve the user's most recent PauseRecord that hasn't been resumed yet
        pause_record = PauseRecord.objects.filter(
            user=request.user,
            resume_time__isnull=True  # Only consider paused records that haven't been resumed
        ).last()

        if not pause_record:
            return Response({'error': 'No pause record found to resume.'}, status=status.HTTP_400_BAD_REQUEST)

        pause_record.resume_time = timezone.now()
        pause_record.save()

        # Serialize the updated record and return the response
        serializer = ResumeRecordSerializer(pause_record)
        return Response({'message': 'Resume recorded successfully.', 'data': serializer.data}, status=status.HTTP_200_OK)

class TimeHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        time_records = TimeRecord.objects.filter(user=request.user).order_by('-date', '-check_in')
        serializer = TimeRecordSerializer(time_records, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class TodayStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = date.today()
        try:
            time_record = TimeRecord.objects.get(user=request.user, date=today)
            serializer = TimeRecordSerializer(time_record)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except TimeRecord.DoesNotExist:
            return Response({'status': 'Not checked in today'}, status=status.HTTP_200_OK)
