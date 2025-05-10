from rest_framework import serializers
from .models import TimeRecord, PauseRecord
from django.contrib.auth import get_user_model

User = get_user_model()

class PauseRecordSerializer(serializers.ModelSerializer):
    pause_time = serializers.DateTimeField(format='%I:%M %p', input_formats=['%I:%M %p', 'iso-8601'])

    class Meta:
        model = PauseRecord
        fields = ['user', 'reason', 'pause_time']
        read_only_fields = ['pause_time']

class TimeRecordSerializer(serializers.ModelSerializer):
    date = serializers.DateField(format='%m/%d/%Y', input_formats=['%m/%d/%Y', 'iso-8601'])
    check_in = serializers.DateTimeField(format='%I:%M %p', input_formats=['%I:%M %p', 'iso-8601'])
    check_out = serializers.DateTimeField(format='%I:%M %p', input_formats=['%I:%M %p', 'iso-8601'], required=False, allow_null=True)
    total_paused_time = serializers.FloatField(required=False)
    rate_per_hour = serializers.SerializerMethodField()
    biweekly_total_hours = serializers.SerializerMethodField()

    class Meta:
        model = TimeRecord
        fields = [
            'id',
            'user',
            'date',
            'check_in',
            'check_out',
            'hours_worked',
            'total_paused_time',
            'rate_per_hour',
            'biweekly_total_hours',
        ]
        read_only_fields = [
            'id',
            'hours_worked',
            'rate_per_hour',
            'biweekly_total_hours',
        ]

    def get_rate_per_hour(self, obj):
        return getattr(obj.user.work_profile, 'rate_per_hour', None)

    def get_biweekly_total_hours(self, obj):
        return getattr(obj.user.work_profile, 'biweekly_total_hours', None)

class UserTimeRecordSerializer(serializers.ModelSerializer):
    time_records = TimeRecordSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'time_records']

class ResumeRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PauseRecord
        fields = ['id', 'user', 'resume_time']
        read_only_fields = ['user', 'resume_time']
