from django.contrib import admin
from django.db.models import Sum, F, ExpressionWrapper, DurationField, DecimalField
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
            'hours_worked', 'total_paused_time', 'rate_per_hour',
             'status'
        )
        export_order = fields

    def dehydrate_status(self, record):
        if record.check_out:
            return 'Completed'
        return 'In Progress' if record.check_in else 'Not Checked In'

    def dehydrate_rate_per_hour(self, record):
        return record.user.work_profile.rate_per_hour if hasattr(record.user, 'work_profile') else None

    def dehydrate_payment_amount(self, record):
        if hasattr(record.user, 'work_profile') and record.user.work_profile.rate_per_hour and record.hours_worked:
            return Decimal(record.hours_worked) * record.user.work_profile.rate_per_hour
        return None

class TimeRecordAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = TimeRecordResource
    list_display = (
        'user', 'date', 'check_in', 'check_out',
        'paused_time_display', 
        'rate_per_hour_display',
        'status', 'user_summary'
    )
    list_filter = ('date', 'user', 'check_out')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('hours_worked', 'total_paused_time', 'user_summary', 'status', 'rate_per_hour_info', 'payment_amount_info')
    date_hierarchy = 'date'
    ordering = ('-date', '-check_in')

    fieldsets = (
        (None, {
            'fields': ('user', 'date', 'status')
        }),
        ('Time Information', {
            'fields': ('check_in', 'check_out', 'hours_worked', 'total_paused_time')
        }),
        ('Payment Information', {
            'fields': ('rate_per_hour_info', 'payment_amount_info'),
            'classes': ('collapse',)
        }),
        ('Summary', {
            'fields': ('user_summary',),
            'classes': ('collapse',)
        }),
    )

    def get_payment_amount(self, obj):
        """Centralized payment calculation"""
        if hasattr(obj.user, 'work_profile') and obj.user.work_profile.rate_per_hour and obj.hours_worked:
            return Decimal(obj.hours_worked) * obj.user.work_profile.rate_per_hour
        return Decimal(0)

    def date_display(self, obj):
        return obj.check_in.date() if obj.check_in else "-"
    date_display.short_description = 'Date'
    date_display.admin_order_field = 'check_in'

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

    def rate_per_hour_display(self, obj):
        if hasattr(obj.user, 'work_profile') and obj.user.work_profile.rate_per_hour:
            return f"${obj.user.work_profile.rate_per_hour:.2f}/h"
        return '-'
    rate_per_hour_display.short_description = 'Rate/Hour'
    rate_per_hour_display.admin_order_field = 'user__work_profile__rate_per_hour'

    def payment_amount_display(self, obj):
        payment = self.get_payment_amount(obj)
        return f"${payment:.2f}" if payment > 0 else '-'
    payment_amount_display.short_description = 'Payment'

    def rate_per_hour_info(self, obj):
        return self.rate_per_hour_display(obj)
    rate_per_hour_info.short_description = 'Rate per Hour'

    def payment_amount_info(self, obj):
        return self.payment_amount_display(obj)
    payment_amount_info.short_description = 'Payment Amount'

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
        
        current_payment = self.get_payment_amount(obj)
        profile = getattr(obj.user, 'work_profile', None)
        total_payment = total_hours * profile.rate_per_hour if profile and profile.rate_per_hour else Decimal(0)
        
        summary = [
            f"<b>Hours:</b> {total_hours:.2f}h",
            f"<b>Days:</b> {days_worked}",
            f"<b>Avg/Day:</b> {avg_hours:.2f}h",
            f"<b>Total:</b> ${total_payment:.2f}"
        ]
            
        return format_html(" | ".join(summary))
    user_summary.short_description = 'User Summary'
    user_summary.allow_tags = True

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('user__work_profile')
        if not request.user.is_superuser:
            qs = qs.filter(user=request.user)
        return qs.annotate(
            work_duration=ExpressionWrapper(
                F('check_out') - F('check_in'),
                output_field=DurationField()
            )
        )

    def save_model(self, request, obj, form, change):
        if obj.check_in and obj.check_out:
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
        'user', 'reason', 'pause_datetime_display',
        'resume_datetime_display', 'duration_display', 'pause_status'
    )
    list_filter = ('user', 'pause_time', 'resume_time')
    search_fields = ('user__username', 'reason')
    readonly_fields = ('pause_time', 'resume_time', 'duration', 'pause_status', 
                      'pause_datetime_info', 'resume_datetime_info')
    date_hierarchy = 'pause_time'
    ordering = ('-pause_time',)

    fieldsets = (
        (None, {'fields': ('user', 'reason')}),
        ('Timing Info', {
            'fields': ('pause_datetime_info', 'resume_datetime_info', 'duration', 'pause_status'),
            'classes': ('collapse',)
        }),
    )

    def _convert_to_arizona_time(self, dt):
        """Convert datetime to Arizona timezone (MST, no DST)"""
        if not dt:
            return None
        arizona_tz = timezone.get_fixed_timezone(-420)  # UTC-7 (MST)
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.utc)
        return dt.astimezone(arizona_tz)

    def pause_datetime_display(self, obj):
        if obj.pause_time:
            az_time = self._convert_to_arizona_time(obj.pause_time)
            return az_time.strftime("%Y-%m-%d %I:%M:%S %p")
        return "-"
    pause_datetime_display.short_description = "Pause Date & Time (Arizona)"
    pause_datetime_display.admin_order_field = 'pause_time'

    def resume_datetime_display(self, obj):
        if obj.resume_time:
            az_time = self._convert_to_arizona_time(obj.resume_time)
            return az_time.strftime("%Y-%m-%d %I:%M:%S %p")
        return "-"
    resume_datetime_display.short_description = "Resume Date & Time (Arizona)"
    resume_datetime_display.admin_order_field = 'resume_time'

    def pause_datetime_info(self, obj):
        return self.pause_datetime_display(obj)
    pause_datetime_info.short_description = "Pause Date & Time (Arizona)"

    def resume_datetime_info(self, obj):
        return self.resume_datetime_display(obj)
    resume_datetime_info.short_description = "Resume Date & Time (Arizona)"

    def duration_display(self, obj):
        if obj.duration:
            total_sec = obj.duration.total_seconds()
            hours, rem = divmod(total_sec, 3600)
            minutes, seconds = divmod(rem, 60)
            return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        return "Ongoing"
    duration_display.short_description = "Duration"

    def pause_status(self, obj):
        if obj.resume_time:
            return format_html('<span style="color: green;">✓ Completed</span>')
        elif obj.pause_time:
            az_time = self._convert_to_arizona_time(obj.pause_time)
            if az_time.date() == self._convert_to_arizona_time(timezone.now()).date():
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
        if not obj.pk and not obj.pause_time:
            obj.pause_time = timezone.now()
        
        if obj.resume_time and obj.pause_time and obj.resume_time < obj.pause_time:
            obj.resume_time = obj.pause_time + timedelta(seconds=1)
        
        if obj.pause_time and obj.resume_time:
            obj.duration = obj.resume_time - obj.pause_time
        
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
    list_display = ('user', 'rate_per_hour', 'biweekly_total_hours', 'estimated_pay', 'recent_hours_worked')
    search_fields = ('user__email', 'user_')
    list_editable = ('rate_per_hour', 'biweekly_total_hours')

    def user(self, obj):
        return obj.user.username
    user.short_description = 'Username'
    user.admin_order_field = 'user_'

    def estimated_pay(self, obj):
        if not obj.rate_per_hour or not obj.biweekly_total_hours:
            return "-"
        return f"${obj.rate_per_hour * obj.biweekly_total_hours:.2f}"
    estimated_pay.short_description = 'Est. Biweekly Pay'

    def recent_hours_worked(self, obj):
        records = TimeRecord.objects.filter(
            user=obj.user,
            date__gte=timezone.now().date() - timedelta(days=14)
        )
        total_hours = sum([Decimal(record.hours_worked or 0) for record in records], Decimal(0))
        return f"{total_hours:.2f}h"
    recent_hours_worked.short_description = 'Recent Hours (14d)'


admin.site.register(TimeRecord, TimeRecordAdmin)
admin.site.register(PauseRecord, PauseRecordAdmin)
admin.site.register(UserWorkProfile, UserWorkProfileAdmin)