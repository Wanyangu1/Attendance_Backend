from django.contrib import admin
from .models import Client

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        'clientId', 'firstName', 'lastName', 'user',
        'dob', 'location', 'phone', 'guardian',
        'billType', 'status'
    )
    list_filter = ('billType', 'status', 'location', 'dob')
    search_fields = ('firstName', 'lastName', 'clientId', 'phone', 'guardian')
    ordering = ('-dob', 'lastName')
    list_editable = ('status', 'billType', 'location', 'phone', 'guardian')
    autocomplete_fields = ('user',)
    date_hierarchy = 'dob'

    fieldsets = (
        ('Client Identification', {
            'fields': ('clientId', 'user', 'status')
        }),
        ('Personal Information', {
            'fields': ('firstName', 'lastName', 'dob', 'guardian')
        }),
        ('Contact and Billing', {
            'fields': ('phone', 'location', 'billType')
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset by selecting related user"""
        return super().get_queryset(request).select_related('user')

from django.contrib import admin
from .models import AttendanceRecord

class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('client', 'date', 'time_in', 'time_out', 'service', 'location', 'one_on_one')
    list_filter = ('date', 'service', 'location', 'one_on_one')
    search_fields = ('client',)
    date_hierarchy = 'date'
    ordering = ('-date', 'client')
    
    fieldsets = (
        ('Client Information', {
            'fields': ('client', 'date')
        }),
        ('Attendance Details', {
            'fields': ('time_in', 'time_out', 'service', 'location')
        }),
        ('Additional Information', {
            'fields': ('one_on_one', 'documentation'),
            'classes': ('collapse',)
        }),
    )

admin.site.register(AttendanceRecord, AttendanceRecordAdmin)