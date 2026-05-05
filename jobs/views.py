from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError

from applications.models import Application
from applications.serializers import ApplicationSerializer

from .models import Job, JobCategory
from .serializers import JobCategorySerializer, JobSerializer

class JobCategoryListView(generics.ListAPIView):
    queryset = JobCategory.objects.all()
    serializer_class = JobCategorySerializer
    permission_classes = [permissions.AllowAny]


class JobListCreateView(generics.ListCreateAPIView):
    queryset = Job.objects.select_related('employer').prefetch_related('categories').all()
    serializer_class = JobSerializer

    def get_queryset(self):
        queryset = self.queryset
        category_id = self.request.query_params.get('category')
        work_mode = self.request.query_params.get('work_mode')
        salary_type = self.request.query_params.get('salary_type')
        city = self.request.query_params.get('city')
        keyword = self.request.query_params.get('q')
        status = self.request.query_params.get('status')
        today = timezone.localdate()

        if category_id and category_id.isdigit():
            queryset = queryset.filter(categories__id=int(category_id))
        if work_mode:
            queryset = queryset.filter(work_mode_obj__code=work_mode)
        if salary_type in {'negotiable', 'range', 'fixed'}:
            queryset = queryset.filter(salary_type=salary_type)
        if city:
            queryset = queryset.filter(city__icontains=city)
        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword)
                | Q(description__icontains=keyword)
                | Q(required_skills__icontains=keyword)
                | Q(categories__name__icontains=keyword)
            )
        if status == 'open':
            queryset = queryset.filter(status='open').filter(
                Q(deadline__isnull=True) | Q(deadline__gte=today)
            )
        elif status == 'expired':
            queryset = queryset.filter(status='open', deadline__lt=today)
        elif status in {'in_progress', 'completed', 'cancelled'}:
            queryset = queryset.filter(status=status)
        return queryset.distinct()

    def perform_create(self, serializer):
        if self.request.user.role not in {'employer', 'admin'}:
            raise PermissionDenied('Chỉ nhà tuyển dụng mới có thể đăng việc.')
        serializer.save(employer=self.request.user)


class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Job.objects.select_related('employer').prefetch_related('categories').all()
    serializer_class = JobSerializer

    def perform_update(self, serializer):
        job = self.get_object()
        if self.request.user != job.employer and self.request.user.role != 'admin':
            raise PermissionDenied('Bạn không được phép cập nhật việc này.')
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user != instance.employer and self.request.user.role != 'admin':
            raise PermissionDenied('Bạn không được phép xóa việc này.')
        instance.delete()


class ApplyJobView(generics.CreateAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if self.request.user.role != 'student':
            raise PermissionDenied('Chỉ sinh viên mới có thể ứng tuyển.')

        job = Job.objects.filter(pk=self.kwargs['pk']).first()
        if not job:
            raise ValidationError('Không tìm thấy việc.')
        if not job.is_receiving_applications:
            raise ValidationError('Việc này hiện không mở ứng tuyển.')

        if Application.objects.filter(student=self.request.user, job=job).exists():
            raise ValidationError('Bạn đã ứng tuyển việc này.')

        cv_file = serializer.validated_data.get('cv_file')
        if not cv_file and not self.request.user.default_cv:
            raise ValidationError('Vui lòng tải CV để ứng tuyển.')

        saved_application = serializer.save(student=self.request.user, job=job)
        if not saved_application.candidate_email:
            saved_application.candidate_email = self.request.user.email or ''
        if not saved_application.candidate_phone:
            saved_application.candidate_phone = getattr(self.request.user, 'phone', '') or ''
        if not saved_application.cv_file and self.request.user.default_cv:
            saved_application.cv_file = self.request.user.default_cv
        saved_application.save(update_fields=['candidate_email', 'candidate_phone', 'cv_file'])

    