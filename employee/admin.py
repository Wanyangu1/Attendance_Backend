from django.contrib import admin
from django.db.models import Sum
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.utils import timezone
from datetime import timedelta
from import_export import resources
from import_export.admin import ExportMixin
from import_export.formats import base_formats
from .models import TimeRecord, PauseRecord

User = get_user_model()


class TimeRecordResource(resources.ModelResource):
    class Meta:
        model = TimeRecord
        fields = (
            'user__email',  # changed from user__username
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
        'user', 'date', 'check_in_time', 'check_out_time',
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

    def check_in_time(self, obj):
        return obj.check_in.time() if obj.check_in else '-'
    check_in_time.short_description = 'Check In Time'

    def check_out_time(self, obj):
        return obj.check_out.time() if obj.check_out else '-'
    check_out_time.short_description = 'Check Out Time'

    def status(self, obj):
        if obj.check_out:
            return 'Completed'
        return 'In Progress' if obj.check_in else 'Not Checked In'
    status.short_description = 'Status'

    def user_summary(self, obj):
        user_records = TimeRecord.objects.filter(user=obj.user)
        total_hours = 0

        for record in user_records:
            if record.check_in and record.check_out:
                work_duration = record.check_out - record.check_in

                # Get pause records during this time
                pauses = PauseRecord.objects.filter(
                    user=record.user,
                    pause_time__gte=record.check_in,
                    resume_time__lte=record.check_out,
                    resume_time__isnull=False
                )

                total_pause_duration = timedelta()
                for pause in pauses:
                    total_pause_duration += pause.resume_time - pause.pause_time

                adjusted_duration = work_duration - total_pause_duration
                total_hours += adjusted_duration.total_seconds() / 3600

        days_worked = user_records.values('date').distinct().count()
        avg_hours = total_hours / days_worked if days_worked > 0 else 0
        return f"Total: {total_hours:.2f}h | Days: {days_worked} | Avg: {avg_hours:.2f}h/day"
    user_summary.short_description = 'User Summary'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user' and not request.user.is_superuser:
            kwargs['queryset'] = User.objects.filter(id=request.user.id)
            kwargs['initial'] = request.user.id
            return db_field.formfield(**kwargs)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        update_fields = {}
        if obj.rate_per_hour is not None:
            update_fields['rate_per_hour'] = obj.rate_per_hour
        if obj.biweekly_total_hours is not None:
            update_fields['biweekly_total_hours'] = obj.biweekly_total_hours
        if update_fields:
            updated_count = TimeRecord.objects.filter(user=obj.user).exclude(pk=obj.pk).update(**update_fields)
            self.message_user(request, f"Updated {updated_count} other records for this user with the new values.")


class PauseRecordAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'reason',
        'formatted_pause_time',
        'formatted_resume_time',
        'duration_away',
        'pause_status'
    )
    list_filter = ('user', 'pause_time', 'resume_time')
    search_fields = ('user__username', 'reason')
    readonly_fields = (
        'duration_away',
        'pause_status',
        'formatted_pause_time',
        'formatted_resume_time'
    )
    date_hierarchy = 'pause_time'
    ordering = ('-pause_time',)

    fieldsets = (
        (None, {
            'fields': ('user', 'reason')
        }),
        ('Time Information', {
            'fields': (
                'formatted_pause_time',
                'resume_time',
                'formatted_resume_time',
                'duration_away',
                'pause_status'
            )
        }),
    )

    def formatted_pause_time(self, obj):
        if obj.pause_time:
            return timezone.localtime(obj.pause_time).strftime('%Y-%m-%d %H:%M:%S')
        return "-"
    formatted_pause_time.short_description = "Pause Time"

    def formatted_resume_time(self, obj):
        if obj.resume_time:
            return timezone.localtime(obj.resume_time).strftime('%Y-%m-%d %H:%M:%S')
        return "-"
    formatted_resume_time.short_description = "Resume Time"

    def duration_away(self, obj):
        if obj.resume_time and obj.pause_time:
            delta = obj.resume_time - obj.pause_time
            hours, remainder = divmod(delta.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        return "Ongoing"
    duration_away.short_description = "Duration"

    def pause_status(self, obj):
        if obj.resume_time:
            return "Completed"
        if obj.pause_time and obj.pause_time.date() == timezone.now().date():
            return "Active (Today)"
        return "Active (Older)"
    pause_status.short_description = "Status"

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('user')
        if not request.user.is_superuser:
            qs = qs.filter(user=request.user)
        return qs

    def has_add_permission(self, request):
        if request.method == "POST":
            user_id = request.POST.get('user')
            if user_id and PauseRecord.objects.filter(
                user_id=user_id,
                resume_time__isnull=True
            ).exists():
                return False
        return super().has_add_permission(request)

    def save_model(self, request, obj, form, change):
        if not obj.resume_time:
            existing_pauses = PauseRecord.objects.filter(
                user=obj.user,
                resume_time__isnull=True
            ).exclude(pk=obj.pk if obj.pk else None)
            if existing_pauses.exists():
                self.message_user(
                    request,
                    "User already has an active pause. Cannot create another one.",
                    level='ERROR'
                )
                return
        super().save_model(request, obj, form, change)

        if obj.resume_time and obj.pause_time and obj.resume_time < obj.pause_time:
            obj.resume_time = obj.pause_time + timedelta(seconds=1)
            obj.save()
            self.message_user(
                request,
                "Resume time was before pause time. Adjusted to be 1 second after pause time.",
                level='WARNING'
            )

admin.site.register(TimeRecord, TimeRecordAdmin)
admin.site.register(PauseRecord, PauseRecordAdmin)