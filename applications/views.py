from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from .models import Application
from .serializers import ApplicationSerializer, ApplicationStatusUpdateSerializer


class MyApplicationListView(generics.ListAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        base_qs = Application.objects.select_related('job', 'student')
        if user.role == 'student':
            return base_qs.filter(student=user)
        if user.role == 'employer':
            return base_qs.filter(job__employer=user)
        if user.role == 'admin':
            return base_qs.all()
        return Application.objects.none()


class ApplicationStatusUpdateView(generics.UpdateAPIView):
    queryset = Application.objects.select_related('job', 'student').all()
    serializer_class = ApplicationStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        application = self.get_object()
        user = self.request.user
        if user != application.job.employer and user.role != 'admin':
            raise PermissionDenied('Chỉ nhà tuyển dụng của việc này mới có thể cập nhật trạng thái.')
        serializer.save()
