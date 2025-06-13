from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Client, AttendanceRecord

User = get_user_model()

class ClientSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Client
        fields = '__all__'


class AttendanceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceRecord
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
    
    def validate(self, data):
        if data['time_out'] <= data['time_in']:
            raise serializers.ValidationError("Time Out must be after Time In")
        return data
