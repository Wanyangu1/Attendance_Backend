from django.conf import settings
from django.db import models

class UserSettings(models.Model):
    LOCATION_CHOICES = [
        ('guadalupe_dta', 'Guadalupe DTA'),
        ('guadalupe_dtt', 'Guadalupe DTT'),
        ('guadalupe_special_dta', 'Guadalupe Special DTA'),
        ('hcbs', 'HCBS'),
    ]

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    MARITAL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
    ]

    RACE_CHOICES = [
    ('american_indian', 'American Indian or Alaska Native'),
    ('asian', 'Asian'),
    ('African American', 'Black or African American'),
    ('native_hawaiian', 'Native Hawaiian or Other Pacific Islander'),
    ('white', 'White'),
    ('two_or_more', 'Two or More Races'),
    ('not_disclosed', 'Prefer Not to Disclose'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="settings"
    )
    street_address = models.CharField(max_length=255)
    address2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=20)
    manager_name = models.CharField(max_length=255)

    # New fields with default values for backward compatibility
    provider_id = models.CharField(max_length=100, default='N/A')
    payroll_id = models.CharField(max_length=100, default='N/A')
    location = models.CharField(
        max_length=50,
        choices=LOCATION_CHOICES,
        default='guadalupe_dta'
    )
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        default='other'
    )
    race = models.CharField(max_length=50, choices=RACE_CHOICES, default='not_disclosed')
    marital_status = models.CharField(
        max_length=10,
        choices=MARITAL_STATUS_CHOICES,
        default='single'
    )
    services_provided = models.TextField(
        help_text="List of services provided, separated by commas",
        default='None'
    )
    additional_info = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s settings"


class Document(models.Model):
    user_settings = models.ForeignKey(
        UserSettings,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    name = models.CharField(max_length=255)
    effective_start = models.DateField()
    effective_end = models.DateField()

    def __str__(self):
        return f"{self.name} for {self.user_settings.user.username}"
