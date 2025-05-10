from django.contrib import admin
from django.db.models import Sum
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.html import format_html
from datetime import timedelta
from import_export import resources
from import_export.admin import ExportMixin
from import_export.formats import base_formats
from .models import TimeRecord, PauseRecord
from decimal import Decimal

User = get_user_model()


class TimeRecordResource(resources.ModelResource):
    class Meta:
        model = TimeRecord
        fields = (
            'user__email',
            'date', 'check_in', 'check_out',
            'hours_worked', 'rate_per_hour', 'biweekly_total_hours',
            'status'
        )
        export_order = fields

    def dehydrate_status(self, record):
        if record.check_out:
            return 'Completed'
        return 'In Progress' if record.check_in else 'Not Checked In'


class TimeRecordAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = TimeRecordResource
    list_display = (
        'user', 'date', 'check_in', 'check_out',
        'hours_worked', 'rate_per_hour', 'biweekly_total_hours',
        'status', 'user_summary'
    )
    list_filter = ('date', 'user', 'check_out')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('hours_worked', 'user_summary')
    date_hierarchy = 'date'
    ordering = ('-date', '-check_in')

    fieldsets = (
        (None, {
            'fields': ('user', 'date')
        }),
        ('Time Information', {
            'fields': ('check_in', 'check_out', 'hours_worked', 'user_summary')
        }),
        ('Payroll Info (Admin Only)', {
            'fields': ('rate_per_hour', 'biweekly_total_hours'),
        }),
    )

    def get_export_formats(self):
        return [base_formats.XLSX, base_formats.CSV]

    def status(self, obj):
        if obj.check_out:
            return 'Completed'
        return 'In Progress' if obj.check_in else 'Not Checked In'
    status.short_description = 'Status'

    def user_summary(self, obj):
        user_records = TimeRecord.objects.filter(user=obj.user)
        total_hours = sum([Decimal(record.hours_worked or 0) for record in user_records], Decimal(0))
        days_worked = user_records.values('date').distinct().count()
        avg_hours = total_hours / Decimal(days_worked) if days_worked else Decimal(0)
        return f"Total: {total_hours:.2f}h | Days: {days_worked} | Avg: {avg_hours:.2f}h/day"

    user_summary.short_description = 'User Summary'

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('user')
        return qs if request.user.is_superuser else qs.filter(user=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user' and not request.user.is_superuser:
            kwargs['queryset'] = User.objects.filter(id=request.user.id)
            kwargs['initial'] = request.user.id
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        # Auto-fill check-in/check-out if missing
        if not obj.check_in or not obj.check_out:
            pauses = PauseRecord.objects.filter(
                user=obj.user,
                pause_time__date=obj.date,
                resume_time__isnull=False
            ).order_by('pause_time')
            if pauses.exists():
                if not obj.check_in:
                    obj.check_in = pauses.first().pause_time
                if not obj.check_out:
                    obj.check_out = pauses.last().resume_time

        # Calculate total_paused_time in hours using duration field
        total_pause_duration = PauseRecord.objects.filter(
            user=obj.user,
            pause_time__date=obj.date,
            resume_time__isnull=False
        ).aggregate(total=Sum('duration'))['total'] or timedelta()
        obj.total_paused_time = total_pause_duration.total_seconds() / 3600

        # Calculate hours worked
        if obj.check_in and obj.check_out:
            net_work_time = obj.check_out - obj.check_in - total_pause_duration
            obj.hours_worked = round(net_work_time.total_seconds() / 3600, 2)

        super().save_model(request, obj, form, change)

        # Propagate biweekly/hourly values to related records
        updates = {}
        if obj.rate_per_hour is not None:
            updates['rate_per_hour'] = obj.rate_per_hour
        if obj.biweekly_total_hours is not None:
            updates['biweekly_total_hours'] = obj.biweekly_total_hours
        if updates:
            updated_count = TimeRecord.objects.filter(user=obj.user).exclude(pk=obj.pk).update(**updates)
            self.message_user(request, f"Updated {updated_count} other records for this user with new values.")


class PauseRecordAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'reason', 'formatted_pause_time',
        'formatted_resume_time', 'formatted_duration',
        'pause_status'
    )
    list_filter = ('user', 'pause_time', 'resume_time')
    search_fields = ('user__username', 'reason')
    readonly_fields = (
        'formatted_pause_time', 'formatted_resume_time',
        'formatted_duration', 'pause_status'
    )
    date_hierarchy = 'pause_time'
    ordering = ('-pause_time',)

    fieldsets = (
        (None, {'fields': ('user', 'reason')}),
        ('Timing Info', {
            'fields': (
                'formatted_pause_time', 'resume_time',
                'formatted_resume_time', 'formatted_duration', 'pause_status'
            )
        }),
    )

    def formatted_pause_time(self, obj):
        return timezone.localtime(obj.pause_time).strftime('%Y-%m-%d %H:%M:%S') if obj.pause_time else "-"
    formatted_pause_time.short_description = "Pause Time"

    def formatted_resume_time(self, obj):
        return timezone.localtime(obj.resume_time).strftime('%Y-%m-%d %H:%M:%S') if obj.resume_time else "-"
    formatted_resume_time.short_description = "Resume Time"

    def formatted_duration(self, obj):
        if obj.duration:
            total_sec = obj.duration.total_seconds()
            hours, rem = divmod(total_sec, 3600)
            minutes, seconds = divmod(rem, 60)
            return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        return "Ongoing"
    formatted_duration.short_description = "Duration"

    def pause_status(self, obj):
        if obj.resume_time:
            return "Completed"
        elif obj.pause_time.date() == timezone.now().date():
            return "Active (Today)"
        return "Active (Older)"
    pause_status.short_description = "Status"

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('user')
        return qs if request.user.is_superuser else qs.filter(user=request.user)

    def has_add_permission(self, request):
        if request.method == "POST":
            user_id = request.POST.get('user')
            if user_id and PauseRecord.objects.filter(user_id=user_id, resume_time__isnull=True).exists():
                return False
        return super().has_add_permission(request)

    def save_model(self, request, obj, form, change):
        if obj.resume_time and obj.pause_time and obj.resume_time < obj.pause_time:
            obj.resume_time = obj.pause_time + timedelta(seconds=1)
            self.message_user(request, "Resume time was earlier than pause time. Auto-corrected.", level='WARNING')

        if obj.pause_time and obj.resume_time:
            obj.duration = obj.resume_time - obj.pause_time

        if not obj.resume_time:
            existing = PauseRecord.objects.filter(user=obj.user, resume_time__isnull=True).exclude(pk=obj.pk)
            if existing.exists():
                self.message_user(request, "User already has an active pause.", level='ERROR')
                return

        super().save_model(request, obj, form, change)


admin.site.register(TimeRecord, TimeRecordAdmin)
admin.site.register(PauseRecord, PauseRecordAdmin)
