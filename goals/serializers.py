from rest_framework import serializers
from .models import Goal, Trial, DailyProgress

class TrialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trial
        fields = '__all__'
        read_only_fields = ['created_at']

class GoalSerializer(serializers.ModelSerializer):
    trials = TrialSerializer(many=True, read_only=True)
    
    class Meta:
        model = Goal
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class DailyProgressSerializer(serializers.ModelSerializer):
    trials = TrialSerializer(many=True, read_only=True)

    class Meta:
        model = DailyProgress
        fields = '__all__'
        read_only_fields = ['created_at', 'created_by']
