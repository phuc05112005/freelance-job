from django.contrib import admin

from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'student',
        'job',
        'candidate_email',
        'candidate_phone',
        'status',
        'available_date',
        'applied_at',
    )
    list_filter = ('status', 'applied_at')
    search_fields = ('student__username', 'job__title', 'candidate_email', 'candidate_phone')
    autocomplete_fields = ('student', 'job')
