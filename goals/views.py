from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Goal, Trial, DailyProgress
from .serializers import GoalSerializer, TrialSerializer, DailyProgressSerializer
from clients.models import Client

class GoalViewSet(viewsets.ModelViewSet):
    queryset = Goal.objects.all()
    serializer_class = GoalSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        client_id = self.request.query_params.get('client_id')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        return queryset

    @action(detail=True, methods=['post'])
    def add_trial(self, request, pk=None):
        goal = self.get_object()
        serializer = TrialSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(goal=goal)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DailyProgressViewSet(viewsets.ModelViewSet):
    queryset = DailyProgress.objects.all()
    serializer_class = DailyProgressSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        client_id = self.request.query_params.get('client_id')
        date = self.request.query_params.get('date')
        
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        if date:
            queryset = queryset.filter(date=date)
            
        return queryset

class TrialViewSet(viewsets.ModelViewSet):
    queryset = Trial.objects.all()
    serializer_class = TrialSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        daily_progress_id = self.request.query_params.get('daily_progress_id')
        if daily_progress_id:
            queryset = queryset.filter(daily_progress_id=daily_progress_id)
        return queryset
