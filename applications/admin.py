from django.contrib import admin

from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'student',
        'job',
        'status',
        'expected_salary',
        'estimated_days',
        'applied_at',
    )
    list_filter = ('status', 'applied_at')
    search_fields = ('student__username', 'job__title')
    autocomplete_fields = ('student', 'job')
