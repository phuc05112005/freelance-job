from rest_framework import serializers

from .models import Job, JobCategory


class JobCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = JobCategory
        fields = ('id', 'name', 'slug')


class JobSerializer(serializers.ModelSerializer):
    employer_username = serializers.CharField(source='employer.username', read_only=True)
    categories = serializers.PrimaryKeyRelatedField(
        many=True, queryset=JobCategory.objects.all(), required=False
    )
    category_names = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Job
        fields = (
            'id',
            'employer',
            'employer_username',
            'title',
            'description',
            'categories',
            'category_names',
            'required_skills',
            'employment_type_obj',
            'experience_level_obj',
            'work_mode_obj',
            'city',
            'address',
            'salary_type',
            'salary_min',
            'salary_max',
            'deadline',
            'vacancies',
            'status',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'employer', 'created_at', 'updated_at')

    def get_category_names(self, obj):
        return [category.name for category in obj.categories.all()]
