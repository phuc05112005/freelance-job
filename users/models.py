from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Sinh viên'),
        ('employer', 'Nhà tuyển dụng'),
        ('admin', 'Quản trị viên'),
    )

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    skills = models.TextField(blank=True, help_text='Các kỹ năng, phân tách bằng dấu phẩy')
    university = models.CharField(max_length=255, blank=True)
    major = models.CharField(max_length=255, blank=True)
    related_category = models.ForeignKey(
        'jobs.JobCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
    )
    academic_year = models.PositiveSmallIntegerField(null=True, blank=True)
    avatar_url = models.URLField(blank=True)
    default_cv = models.FileField(upload_to='cvs/default/', blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True)
    company_tax_code = models.CharField(max_length=50, blank=True)
    company_website = models.URLField(blank=True)
    company_address = models.CharField(max_length=255, blank=True)
    province = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    ward = models.CharField(max_length=100, blank=True)
    employer_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return f'{self.username} ({self.role})'


class CV(models.Model):
    GENDER_CHOICES = [
        ('Nam', 'Nam'),
        ('Nữ', 'Nữ'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tieude = models.CharField(max_length=255)
    avatar = models.ImageField(upload_to='avatars', null=True, blank=True)
    hoten = models.CharField(max_length=255)
    gioitinh = models.CharField(max_length=10, choices=GENDER_CHOICES, default='Nam')
    ngaysinh = models.CharField(max_length=20, null=True, blank=True)
    email = models.CharField(max_length=254, null=True, blank=True)
    sdt = models.TextField(max_length=20, null=True, blank=True)
    diachi = models.CharField(max_length=100)
    muctieu = models.TextField(null=True, blank=True)
    kynang = models.TextField(null=True, blank=True)


class KINHNGHIEM(models.Model):
    cv = models.ForeignKey(CV, on_delete=models.CASCADE)
    congty = models.CharField(max_length=255)
    vitri = models.CharField(max_length=255)
    batdau = models.CharField(max_length=50)
    ketthuc = models.CharField(max_length=50)
    mota = models.TextField(null=True, blank=True)


class HocVan(models.Model):
    cv = models.ForeignKey(CV, on_delete=models.CASCADE)
    truong = models.CharField(max_length=255)
    nganh = models.CharField(max_length=255)
    batdau = models.CharField(max_length=50)
    ketthuc = models.CharField(max_length=50)
