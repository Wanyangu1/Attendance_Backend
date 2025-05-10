from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from accounts.models import User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Displayed columns in user list
    list_display = [
        "name",
        "email",
        "is_staff",
        "is_superuser",
        "is_active",
    ]

    # Filters on the right
    list_filter = [
        "is_staff",
        "is_superuser",
        "is_active",
    ]

    # Fields to be used in displaying the User model
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('name',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )

    # Fields used when creating a user via admin
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2'),
        }),
    )

    search_fields = ('email', 'name')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "phone_number"]
