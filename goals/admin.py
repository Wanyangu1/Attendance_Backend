from django.contrib import admin
from .models import Goal, Trial, DailyProgress

class TrialInline(admin.TabularInline):
    model = Trial
    extra = 1
    fields = ('trial_number', 'percentage', 'value', 'initials')
    ordering = ('trial_number',)

@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('client', 'description_short', 'is_active')
    list_filter = ('is_active', 'client')
    search_fields = ('description', 'client__firstName', 'client__lastName')

    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'

@admin.register(DailyProgress)
class DailyProgressAdmin(admin.ModelAdmin):
    list_display = ('client', 'date', 'location')
    list_filter = ('date', 'client')
    search_fields = ('client__firstName', 'client__lastName', 'location')
    inlines = [TrialInline]
