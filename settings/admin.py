from django.contrib import admin
from .models import UserSettings, Document


class DocumentInline(admin.TabularInline):
    model = Document
    extra = 1  # Number of empty forms to display by default
    fields = ('name', 'effective_start', 'effective_end')
    show_change_link = True


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'provider_id', 'payroll_id', 'location',
        'gender', 'race', 'marital_status'
    )
    list_filter = (
        'location', 'gender', 'marital_status', 'race'
    )
    search_fields = (
        'user__username', 'provider_id', 'payroll_id',
        'race', 'manager_name'
    )
    inlines = [DocumentInline]

    fieldsets = (
        ('User Association', {
            'fields': ('user',)
        }),
        ('Address Information', {
            'fields': ('street_address', 'address2', 'city', 'state', 'zip_code')
        }),
        ('Employment Details', {
            'fields': ('manager_name', 'provider_id', 'payroll_id', 'location')
        }),
        ('Personal Details', {
            'fields': ('gender', 'race', 'marital_status')
        }),
        ('Services and Additional Info', {
            'fields': ('services_provided', 'additional_info')
        }),
    )


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('name', 'user_settings', 'effective_start', 'effective_end')
    list_filter = ('effective_start', 'effective_end')
    search_fields = ('name', 'user_settings__user__username')
