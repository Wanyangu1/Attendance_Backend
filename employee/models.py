from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from datetime import timedelta

User = get_user_model()


class UserWorkProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='work_profile')
    rate_per_hour = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    biweekly_total_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Payment Profile"


class TimeRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='time_records')
    date = models.DateField()
    check_in = models.DateTimeField()
    check_in_time = models.TimeField(null=True, blank=True) 
    check_out = models.DateTimeField(null=True, blank=True)
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_paused_time = models.FloatField(default=0)  # in hours
    is_paused = models.BooleanField(default=False)


    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date', '-check_in']

    def clean(self):
        if self.check_out and self.check_out <= self.check_in:
            raise ValidationError("Check-out time must be after check-in time")
        if not self.pk and TimeRecord.objects.filter(user=self.user, date=self.date).exists():
            raise ValidationError("Only one time record per day allowed")

    def save(self, *args, **kwargs):
        if self.check_out:
            total_seconds_worked = (self.check_out - self.check_in).total_seconds()

            pauses = PauseRecord.objects.filter(
                user=self.user,
                pause_time__gte=self.check_in,
                resume_time__lte=self.check_out,
                duration__isnull=False
            )

            total_pause_seconds = sum((pause.duration.total_seconds() for pause in pauses), 0)
            self.total_paused_time = round(total_pause_seconds / 3600, 2)

            net_seconds_worked = total_seconds_worked - total_pause_seconds
            net_hours_worked = max(net_seconds_worked / 3600, 0)
            self.hours_worked = round(net_hours_worked, 2)

            # Optional: log or use user profile info
            user_profile = getattr(self.user, 'work_profile', None)
            if user_profile:
                hourly_rate = user_profile.rate_per_hour
                biweekly_hours = user_profile.biweekly_total_hours
                # You can use these values as needed, e.g., for calculations or logging

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.date}: {self.hours_worked} hours"


class PauseRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.CharField(max_length=255)
    pause_time = models.DateTimeField(auto_now_add=True)
    resume_time = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.resume_time:
            self.duration = self.resume_time - self.pause_time
        else:
            self.duration = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} paused: {self.reason}"

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_work_profile(sender, instance, created, **kwargs):
    if created and not hasattr(instance, 'work_profile'):
        UserWorkProfile.objects.create(user=instance)
