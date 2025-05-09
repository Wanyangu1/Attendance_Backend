from django.conf import settings
from django.db import models

class UserSettings(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # use dynamic reference
        on_delete=models.CASCADE,
        related_name="settings"
    )
    street_address = models.CharField(max_length=255)
    address2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=20)
    manager_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.user.username}'s settings"
