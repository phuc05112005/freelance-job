from django.contrib import admin

from .models import Job, JobCategory, ExperienceLevel, WorkMode, EmploymentType


@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ExperienceLevel)
class ExperienceLevelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'order')
    search_fields = ('name', 'code')


@admin.register(WorkMode)
class WorkModeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code')
    search_fields = ('name', 'code')


@admin.register(EmploymentType)
class EmploymentTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code')
    search_fields = ('name', 'code')


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'employer',
        'work_mode_obj',
        'salary_type',
        'status',
        'deadline',
        'created_at',
    )
    list_filter = (
        'status',
        'work_mode_obj',
        'salary_type',
        'employment_type_obj',
        'experience_level_obj',
        'created_at',
    )
    search_fields = ('title', 'description', 'required_skills', 'employer__username', 'city')
    autocomplete_fields = ('employer',)
    filter_horizontal = ('categories',)
