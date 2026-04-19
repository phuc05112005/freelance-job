from rest_framework import serializers

from .models import Application


class ApplicationSerializer(serializers.ModelSerializer):
    student_username = serializers.CharField(source='student.username', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)
    cv_file_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Application
        fields = (
            'id',
            'student',
            'student_username',
            'job',
            'job_title',
            'candidate_email',
            'candidate_phone',
            'cover_letter',
            'bid_amount',
            'expected_salary',
            'available_date',
            'cv_file',
            'cv_file_url',
            'status',
            'applied_at',
            'updated_at',
        )
        read_only_fields = ('id', 'student', 'job', 'status', 'applied_at', 'updated_at')

    def get_cv_file_url(self, obj):
        request = self.context.get('request')
        if not obj.cv_file:
            return None
        url = obj.cv_file.url
        return request.build_absolute_uri(url) if request else url


class ApplicationStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ('status',)

    def validate_status(self, value):
        if value not in {'accepted', 'rejected'}:
            raise serializers.ValidationError('Trạng thái chỉ được là accepted hoặc rejected.')
        return value
