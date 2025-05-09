from django.contrib import admin
from .models import UserSettings

@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'manager_name', 'city', 'state', 'zip_code')
    list_filter = ('state', 'city')
    search_fields = ('user__email', 'manager_name', 'city', 'state', 'zip_code')

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['user']
        return []
