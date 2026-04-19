from django.db import models

from jobs.models import Job
from users.models import User


class Application(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Chờ duyệt'),
        ('accepted', 'Đã chấp nhận'),
        ('rejected', 'Đã từ chối'),
        ('withdrawn', 'Đã rút đơn'),
    )

    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='applications'
    )
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    candidate_email = models.EmailField(blank=True)
    candidate_phone = models.CharField(max_length=20, blank=True)
    cover_letter = models.TextField(blank=True)
    bid_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    expected_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    available_date = models.DateField(null=True, blank=True)
    cv_file = models.FileField(upload_to='cvs/applications/', blank=True, null=True)
    portfolio_url = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        unique_together = ('student', 'job')
        ordering = ['-applied_at']

    def __str__(self):
        return f'{self.student.username} -> {self.job.title}'

    @staticmethod
    def format_currency(value):
        if value is None:
            return "0"
        return f"{int(value):,}".replace(",", ".")

    @property
    def display_salary(self):
        if not self.expected_salary:
            return "Thỏa thuận"
        return f"{self.format_currency(self.expected_salary)} VNĐ"
