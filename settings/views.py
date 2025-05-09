from rest_framework import generics, permissions
from .models import UserSettings
from .serializers import UserSettingsSerializer

class UserSettingsDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Ensures only one settings instance per user
        obj, created = UserSettings.objects.get_or_create(user=self.request.user)
        return obj

class UserSettingsCreate(generics.CreateAPIView):
    serializer_class = UserSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
