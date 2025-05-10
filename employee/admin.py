from django.contrib import admin
from django.db.models import Sum, F, ExpressionWrapper, DurationField
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.html import format_html
from datetime import timedelta
from import_export import resources
from import_export.admin import ExportMixin
from import_export.formats import base_formats
from .models import TimeRecord, PauseRecord, UserWorkProfile
from decimal import Decimal

User = get_user_model()

class TimeRecordResource(resources.ModelResource):
    class Meta:
        model = TimeRecord
        fields = (
            'user__email', 'date', 'check_in', 'check_out',
            'hours_worked', 'total_paused_time', 'status'
        )
        export_order = fields

    def dehydrate_status(self, record):
        if record.check_out:
            return 'Completed'
        return 'In Progress' if record.check_in else 'Not Checked In'

    def dehydrate_rate_per_hour(self, record):
        return record.user.work_profile.rate_per_hour if hasattr(record.user, 'work_profile') else None

    def dehydrate_biweekly_total_hours(self, record):
        return record.user.work_profile.biweekly_total_hours if hasattr(record.user, 'work_profile') else None

class TimeRecordAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = TimeRecordResource
    list_display = (
        'user', 'date', 'check_in_time', 'check_out_time',
        'hours_worked_display', 'paused_time_display', 'status', 'user_summary'
    )
    list_filter = ('date', 'user', 'check_out')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('hours_worked', 'total_paused_time', 'user_summary', 'status')
    date_hierarchy = 'date'
    ordering = ('-date', '-check_in')

    fieldsets = (
        (None, {
            'fields': ('user', 'date', 'status')
        }),
        ('Time Information', {
            'fields': ('check_in', 'check_out', 'hours_worked', 'total_paused_time')
        }),
        ('Summary', {
            'fields': ('user_summary',),
            'classes': ('collapse',)
        }),
    )

    def check_in_time(self, obj):
        return obj.check_in.time() if obj.check_in else '-'
    check_in_time.short_description = 'Check In'
    check_in_time.admin_order_field = 'check_in'

    def check_out_time(self, obj):
        return obj.check_out.time() if obj.check_out else '-'
    check_out_time.short_description = 'Check Out'
    check_out_time.admin_order_field = 'check_out'

    def hours_worked_display(self, obj):
        return f"{obj.hours_worked:.2f}h" if obj.hours_worked else '-'
    hours_worked_display.short_description = 'Hours Worked'

    def paused_time_display(self, obj):
        return f"{obj.total_paused_time:.2f}h" if obj.total_paused_time else '-'
    paused_time_display.short_description = 'Paused Time'

    def status(self, obj):
        if obj.check_out:
            return format_html('<span style="color: green;">✓ Completed</span>')
        return format_html('<span style="color: orange;">↻ In Progress</span>') if obj.check_in else 'Not Checked In'
    status.short_description = 'Status'

    def user_summary(self, obj):
        user_records = TimeRecord.objects.filter(user=obj.user)
        total_hours = sum([Decimal(record.hours_worked or 0) for record in user_records], Decimal(0))
        days_worked = user_records.values('date').distinct().count()
        avg_hours = total_hours / Decimal(days_worked) if days_worked else Decimal(0)
        
        profile = getattr(obj.user, 'work_profile', None)
        rate = profile.rate_per_hour if profile else None
        estimated_pay = total_hours * Decimal(rate) if rate else None
        
        summary = [
            f"<b>Total:</b> {total_hours:.2f}h",
            f"<b>Days:</b> {days_worked}",
            f"<b>Avg:</b> {avg_hours:.2f}h/day"
        ]
        
        if estimated_pay is not None:
            summary.append(f"<b>Est. Pay:</b> ${estimated_pay:.2f}")
            
        return format_html(" | ".join(summary))
    user_summary.short_description = 'User Summary'
    user_summary.allow_tags = True

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('user')
        if not request.user.is_superuser:
            qs = qs.filter(user=request.user)
        return qs.annotate(
            work_duration=ExpressionWrapper(
                F('check_out') - F('check_in'),
                output_field=DurationField()
            )
        )

    def save_model(self, request, obj, form, change):
        # Calculate hours worked if both check_in and check_out exist
        if obj.check_in and obj.check_out:
            # Get all pauses that fall within the work period
            pauses = PauseRecord.objects.filter(
                user=obj.user,
                pause_time__gte=obj.check_in,
                resume_time__lte=obj.check_out
            ).aggregate(
                total_pause=Sum('duration')
            )
            
            total_pause = pauses['total_pause'] or timedelta()
            obj.total_paused_time = total_pause.total_seconds() / 3600
            
            total_work_time = obj.check_out - obj.check_in
            net_work_time = total_work_time - total_pause
            obj.hours_worked = max(net_work_time.total_seconds() / 3600, 0)
        
        super().save_model(request, obj, form, change)

class PauseRecordAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'reason', 'pause_date', 'pause_time',
        'resume_time', 'duration_display', 'pause_status'
    )
    list_filter = ('user', 'pause_time', 'resume_time')
    search_fields = ('user__username', 'reason')
    readonly_fields = ('duration', 'pause_status')
    date_hierarchy = 'pause_time'
    ordering = ('-pause_time',)

    fieldsets = (
        (None, {'fields': ('user', 'reason')}),
        ('Timing Info', {
            'fields': ('pause_time', 'resume_time', 'duration', 'pause_status')
        }),
    )

    def pause_date(self, obj):
        return obj.pause_time.date() if obj.pause_time else "-"
    pause_date.short_description = "Date"
    pause_date.admin_order_field = 'pause_time'

    def pause_time(self, obj):
        return obj.pause_time.time() if obj.pause_time else "-"
    pause_time.short_description = "Pause Time"

    def duration_display(self, obj):
        if obj.duration:
            total_sec = obj.duration.total_seconds()
            hours, rem = divmod(total_sec, 3600)
            minutes, seconds = divmod(rem, 60)
            return f"{int(hours)}h {int(minutes)}m"
        return "Ongoing"
    duration_display.short_description = "Duration"

    def pause_status(self, obj):
        if obj.resume_time:
            return format_html('<span style="color: green;">✓ Completed</span>')
        elif obj.pause_time.date() == timezone.now().date():
            return format_html('<span style="color: orange;">⏸ Active (Today)</span>')
        return format_html('<span style="color: red;">⏸ Active (Older)</span>')
    pause_status.short_description = "Status"
    pause_status.allow_tags = True

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('user')
        if not request.user.is_superuser:
            qs = qs.filter(user=request.user)
        return qs

    def save_model(self, request, obj, form, change):
        # Prevent resume time before pause time
        if obj.resume_time and obj.pause_time and obj.resume_time < obj.pause_time:
            obj.resume_time = obj.pause_time + timedelta(seconds=1)
        
        # Calculate duration if both times exist
        if obj.pause_time and obj.resume_time:
            obj.duration = obj.resume_time - obj.pause_time
        
        # Prevent multiple active pauses
        if not obj.resume_time:
            existing = PauseRecord.objects.filter(
                user=obj.user, 
                resume_time__isnull=True
            ).exclude(pk=obj.pk if obj.pk else None)
            if existing.exists():
                self.message_user(
                    request, 
                    "User already has an active pause record.", 
                    level='ERROR'
                )
                return
        
        super().save_model(request, obj, form, change)

class UserWorkProfileAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'rate_per_hour', 'biweekly_total_hours', 'estimated_pay')
    search_fields = ('user__email', 'user__username')
    list_editable = ('rate_per_hour', 'biweekly_total_hours')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'

    def estimated_pay(self, obj):
        if not obj.rate_per_hour or not obj.biweekly_total_hours:
            return "-"
        return f"${obj.rate_per_hour * obj.biweekly_total_hours:.2f}"
    estimated_pay.short_description = 'Est. Biweekly Pay'

admin.site.register(TimeRecord, TimeRecordAdmin)
admin.site.register(PauseRecord, PauseRecordAdmin)
admin.site.register(UserWorkProfile, UserWorkProfileAdmin)