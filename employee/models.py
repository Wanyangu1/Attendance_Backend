from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

User = get_user_model()

class TimeRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='time_records')
    date = models.DateField()
    check_in = models.DateTimeField()
    check_out = models.DateTimeField(null=True, blank=True)
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_paused_time = models.FloatField(default=0)
    
    # New fields
    rate_per_hour = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    biweekly_total_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

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
            time_difference = self.check_out - self.check_in
            self.hours_worked = round(time_difference.total_seconds() / 3600, 2)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} - {self.date}: {self.hours_worked} hours"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='time_records')
    date = models.DateField()
    check_in = models.DateTimeField()
    check_out = models.DateTimeField(null=True, blank=True)
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date', '-check_in']
    
    def clean(self):
        # Ensure check_out is after check_in if both exist
        if self.check_out and self.check_out <= self.check_in:
            raise ValidationError("Check-out time must be after check-in time")
        
        # Ensure only one record per user per day
        if not self.pk:  # Only for new records
            if TimeRecord.objects.filter(user=self.user, date=self.date).exists():
                raise ValidationError("Only one time record per day allowed")
    
    def save(self, *args, **kwargs):
        # Calculate hours worked if checking out
        if self.check_out:
            time_difference = self.check_out - self.check_in
            self.hours_worked = round(time_difference.total_seconds() / 3600, 2)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} - {self.date}: {self.hours_worked} hours"
    
class PauseRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.CharField(max_length=255)
    pause_time = models.DateTimeField(auto_now_add=True)
    resume_time = models.DateTimeField(null=True, blank=True) 

    def __str__(self):
        return f"{self.user.username} paused: {self.reason}"
