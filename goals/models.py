from django.db import models
from django.conf import settings
from clients.models import Client  

class Goal(models.Model):
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='goals'
    )
    description = models.TextField()
    activities = models.TextField()
    outcome = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Goal for {self.client}: {self.description[:50]}..."

class Trial(models.Model):
    PERCENTAGE_CHOICES = [
        ('0%', '0%'),
        ('25%', '25%'),
        ('50%', '50%'),
        ('75%', '75%'),
        ('100%', '100%'),
    ]

    VALUE_CHOICES = [
        ('Barriers', 'Barriers'),
        ('HH', 'HH-Hand over hand'),
        ('I', 'I-Independent'),
        ('M', 'M-Modelling'),
        ('P', 'P-Physical prompt'),
        ('R', 'R-Refused'),
        ('S', 'S-Visual (sight) prompt'),
        ('G', 'G-Gesture prompt'),
        ('VP', 'VP-Verbal prompt'),
    ]

    daily_progress = models.ForeignKey(
    'DailyProgress',
    on_delete=models.CASCADE,
    related_name='trials',
    null=True,  # allows null during initial migration
    blank=True
    )

    trial_number = models.PositiveIntegerField(default=1)
    percentage = models.CharField(
        max_length=10,
        choices=PERCENTAGE_CHOICES,
        default='0%'
    )
    value = models.CharField(
        max_length=20,
        choices=VALUE_CHOICES,
        blank=True
    )
    initials = models.CharField(max_length=10, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['trial_number']
        unique_together = ['daily_progress', 'trial_number']  # Prevent duplicates

    def __str__(self):
        return f"Trial {self.trial_number} for {self.daily_progress.client} on {self.daily_progress.date}"

class DailyProgress(models.Model):
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='daily_progress'
    )
    date = models.DateField()
    location = models.CharField(max_length=255)
    general_notes = models.TextField(blank=True)
    provider_initials = models.CharField(max_length=10, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Daily Progress"
        unique_together = ['client', 'date']

    def __str__(self):
        return f"Progress for {self.client} on {self.date}"