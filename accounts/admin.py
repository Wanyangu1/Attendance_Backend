from django.contrib import admin
from accounts.models import UserProfile, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "email",
        "is_staff",
        "is_superuser",
        "is_active",
    ]

    list_filter = [
        "is_staff",
        "is_superuser",
        "is_active",
    ]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "phone_number"]
