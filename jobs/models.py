from django.db import models
from django.utils import timezone

from users.models import User
from .rich_text import sanitize_rich_text


class JobCategory(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=150, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Lĩnh vực'
        verbose_name_plural = 'Lĩnh vực'

    def __str__(self):
        return self.name


class ExperienceLevel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Mức kinh nghiệm'

    def __str__(self):
        return self.name


class WorkMode(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = 'Hình thức làm việc'

    def __str__(self):
        return self.name


class EmploymentType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = 'Loại việc làm'

    def __str__(self):
        return self.name


class Job(models.Model):
    STATUS_CHOICES = (
        ('open', 'Đang tuyển'),
        ('in_progress', 'Đang thực hiện'),
        ('completed', 'Đã hoàn thành'),
        ('cancelled', 'Đã hủy'),
    )

    SALARY_TYPE_CHOICES = (
        ('negotiable', 'Thỏa thuận'),
        ('range', 'Khoảng lương'),
        ('fixed', 'Lương cố định'),
    )

    employer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='posted_jobs'
    )
    title = models.CharField(max_length=255)
    brand_image = models.FileField(
        upload_to='jobs/brands/',
        blank=True,
        null=True,
        help_text='Anh thuong hieu/cong ty (khong bat buoc)',
    )
    description = models.TextField(default='', blank=True)
    categories = models.ManyToManyField(JobCategory, related_name='jobs', blank=True)
    required_skills = models.TextField(
        blank=True,
        help_text='Các kỹ năng yêu cầu, phân tách bằng dấu phẩy',
    )
    
    # Updated to ForeignKeys
    employment_type_obj = models.ForeignKey(
        EmploymentType, on_delete=models.SET_NULL, null=True, blank=True, related_name='jobs'
    )
    experience_level_obj = models.ForeignKey(
        ExperienceLevel, on_delete=models.SET_NULL, null=True, blank=True, related_name='jobs'
    )
    work_mode_obj = models.ForeignKey(
        WorkMode, on_delete=models.SET_NULL, null=True, blank=True, related_name='jobs'
    )

    city = models.CharField(max_length=120, blank=True)
    address = models.CharField(max_length=255, blank=True)
    salary_type = models.CharField(
        max_length=20,
        choices=SALARY_TYPE_CHOICES,
        default='negotiable',
    )
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    vacancies = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.description = sanitize_rich_text(self.description)
        self.required_skills = sanitize_rich_text(self.required_skills)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return self.status == 'open' and self.deadline is not None and self.deadline < timezone.localdate()

    @property
    def is_receiving_applications(self):
        return self.status == 'open' and not self.is_expired

    @property
    def display_status_key(self):
        if self.is_expired:
            return 'expired'
        return self.status

    @property
    def display_status_label(self):
        if self.is_expired:
            return 'Hết hạn'
        return self.get_status_display()

    def format_currency(self, value):
        if value is None:
            return "0"
        return f"{int(value):,}".replace(",", ".")

    @property
    def display_salary(self):
        if self.salary_type == 'negotiable':
            return "Thỏa thuận"

        elif self.salary_type == 'fixed':
            if not self.salary_min:
                return "Chưa cập nhật"
            return f"{self.format_currency(self.salary_min)} VNĐ"

        else:
            min_salary = self.format_currency(self.salary_min) if self.salary_min else "0"
            max_salary = self.format_currency(self.salary_max) if self.salary_max else "0"
            return f"{min_salary} - {max_salary} VNĐ"

class FavoriteJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_jobs')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} ?? {self.job.title}'
