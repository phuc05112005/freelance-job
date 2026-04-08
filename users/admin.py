from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ('id', 'username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('id',)

    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            'Profile',
            {
                'fields': (
                    'role',
                    'phone',
                    'bio',
                    'skills',
                    'university',
                    'major',
                    'academic_year',
                    'avatar_url',
                    'default_cv',
                )
            },
        ),
    )
