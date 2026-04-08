from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Sinh viên'),
        ('employer', 'Nhà tuyển dụng'),
        ('admin', 'Quản trị viên'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    skills = models.TextField(blank=True, help_text='Các kỹ năng, phân tách bằng dấu phẩy')
    university = models.CharField(max_length=255, blank=True)
    major = models.CharField(max_length=255, blank=True)
    academic_year = models.PositiveSmallIntegerField(null=True, blank=True)
    avatar_url = models.URLField(blank=True)
    default_cv = models.FileField(upload_to='cvs/default/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return f'{self.username} ({self.role})'
