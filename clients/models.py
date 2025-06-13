from django.db import models
from django.conf import settings  # Use the custom user model reference

class Client(models.Model):
    BILL_TYPE_CHOICES = [
        ('DDD only', 'DDD only'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='clients'
    )
    clientId = models.CharField(max_length=100, unique=True)
    firstName = models.CharField(max_length=100)
    lastName = models.CharField(max_length=100)
    dob = models.DateField()
    location = models.CharField(max_length=255)
    billType = models.CharField(max_length=20, choices=BILL_TYPE_CHOICES)
    phone = models.CharField(max_length=20)
    guardian = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return f"{self.firstName} {self.lastName} ({self.clientId})"
    
from django.db import models
from django.utils import timezone
import pytz

class AttendanceRecord(models.Model):
    SERVICE_CHOICES = [
        ('DTA1', 'DTA - Day Program (Adult) - 1'),
        ('DTA2', 'DTA - Day Program (Adult) - 2'),
        ('DTT', 'DTT - Day Treatment Training'),
        ('SDTA', 'Special DTA - Special Day Program'),
    ]
    
    LOCATION_CHOICES = [
        ('GUADALUPE_DTA', 'GUADALUPE DTA'),
        ('GUADALUPE_DTT', 'GUADALUPE DTT'),
        ('GUADALUPE_SPECIAL', 'GUADALUPE SPECIAL DTA'),
    ]
    
    client = models.CharField(max_length=100)
    time_in = models.TimeField()
    time_out = models.TimeField()
    service = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    location = models.CharField(max_length=50, choices=LOCATION_CHOICES)
    date = models.DateField()
    one_on_one = models.BooleanField(default=False)
    documentation = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', 'client']
        unique_together = ['client', 'date']  # Prevent duplicate entries for same client on same day
    
    def __str__(self):
        return f"{self.client} - {self.date} - {self.service}"
    
    def save(self, *args, **kwargs):
        # Ensure date is in Arizona time (MST, no DST)
        if not self.date:
            az_timezone = pytz.timezone('America/Phoenix')
            self.date = timezone.now().astimezone(az_timezone).date()
        super().save(*args, **kwargs)
