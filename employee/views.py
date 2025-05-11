from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import date
import pytz
from .models import TimeRecord, PauseRecord
from .serializers import TimeRecordSerializer, PauseRecordSerializer, ResumeRecordSerializer

# Set the timezone to Arizona (doesn't observe DST)
ARIZONA_TZ = pytz.timezone('US/Arizona')

class CheckInView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Get current time in Arizona
        now_arizona = timezone.now().astimezone(ARIZONA_TZ)
        today_arizona = now_arizona.date()
        
        if TimeRecord.objects.filter(user=request.user, date=today_arizona).exists():
            return Response({'error': 'You have already checked in today'}, status=status.HTTP_400_BAD_REQUEST)

        time_record = TimeRecord(user=request.user, date=today_arizona, check_in=now_arizona)
        time_record.full_clean()
        time_record.save()
        serializer = TimeRecordSerializer(time_record)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class CheckOutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Get current time in Arizona
        now_arizona = timezone.now().astimezone(ARIZONA_TZ)
        today_arizona = now_arizona.date()
        
        try:
            time_record = TimeRecord.objects.get(user=request.user, date=today_arizona, check_out__isnull=True)
            time_record.check_out = now_arizona
            time_record.save()
            serializer = TimeRecordSerializer(time_record)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except TimeRecord.DoesNotExist:
            return Response({'error': 'No active check-in found for today or already checked out'}, status=status.HTTP_400_BAD_REQUEST)

class PauseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        active_pause = PauseRecord.objects.filter(
            user=request.user,
            resume_time__isnull=True
        ).exists()

        if active_pause:
            return Response({'error': 'You already have an active pause. Please resume first.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PauseRecordSerializer(data=request.data)
        if serializer.is_valid():
            # Use Arizona time for pause
            pause_time = timezone.now().astimezone(ARIZONA_TZ)
            PauseRecord.objects.create(
                user=request.user,
                reason=serializer.validated_data['reason'],
                pause_time=pause_time
            )
            return Response({'message': 'Pause recorded successfully.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResumeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        pause_record = PauseRecord.objects.filter(
            user=request.user,
            resume_time__isnull=True
        ).last()

        if not pause_record:
            return Response({'error': 'No pause record found to resume.'}, status=status.HTTP_400_BAD_REQUEST)

        # Use Arizona time for resume
        resume_time = timezone.now().astimezone(ARIZONA_TZ)
        pause_record.resume_time = resume_time
        pause_record.save()

        serializer = ResumeRecordSerializer(pause_record)
        return Response({'message': 'Resume recorded successfully.', 'data': serializer.data}, status=status.HTTP_200_OK)

    def get(self, request):
        pause_record = PauseRecord.objects.filter(
            user=request.user,
            resume_time__isnull=True
        ).last()

        if pause_record:
            serializer = ResumeRecordSerializer(pause_record)
            return Response({'paused': True, 'data': serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({'paused': False}, status=status.HTTP_200_OK)

class TimeHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        time_records = TimeRecord.objects.filter(user=request.user).order_by('-date', '-check_in')
        serializer = TimeRecordSerializer(time_records, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class TodayStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get current date in Arizona
        today_arizona = timezone.now().astimezone(ARIZONA_TZ).date()
        try:
            time_record = TimeRecord.objects.get(user=request.user, date=today_arizona)
            serializer = TimeRecordSerializer(time_record)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except TimeRecord.DoesNotExist:
            return Response({'status': 'Not checked in today'}, status=status.HTTP_200_OK)