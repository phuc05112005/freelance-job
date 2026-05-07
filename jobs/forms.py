from django import forms

from .models import EmploymentType, ExperienceLevel, Job, JobCategory, WorkMode
from .rich_text import sanitize_rich_text


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = (
            'title',
            'brand_image',
            'description',
            'categories',
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
        )
        widgets = {
            'brand_image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'description': forms.Textarea(
                attrs={
                    'rows': 8,
                    'class': 'js-rich-text-source',
                    'data-placeholder': 'Mô tả công việc, trách nhiệm, quyền lợi...',
                }
            ),
            'categories': forms.CheckboxSelectMultiple(),
            'required_skills': forms.Textarea(
                attrs={
                    'rows': 6,
                    'class': 'js-rich-text-source',
                    'data-placeholder': 'Yêu cầu ứng viên, kỹ năng bắt buộc, kỹ năng ưu tiên...',
                }
            ),
            'deadline': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.TextInput(attrs={'placeholder': 'Ví dụ: 268 Lý Thường Kiệt, Quận 10'}),
            'city': forms.Select(choices=[('', 'Ch?n T?nh/Th?nh ph?')]),
            'salary_min': forms.NumberInput(attrs={
                'placeholder': 'Có thể để trống nếu lương: Thỏa thuận'
            }),
            'salary_max': forms.NumberInput(attrs={
                'placeholder': 'Có thể để trống nếu lương: Thỏa thuận'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            if self.instance.salary_min is not None:
                self.initial['salary_min'] = int(self.instance.salary_min)

            if self.instance.salary_max is not None:
                self.initial['salary_max'] = int(self.instance.salary_max)
        self.fields['employment_type_obj'].label = "Loại việc làm"
        self.fields['experience_level_obj'].label = "Mức kinh nghiệm"
        self.fields['work_mode_obj'].label = "Hình thức làm việc"
        
        # Make them required if you want
        self.fields['employment_type_obj'].empty_label = "Chọn loại việc làm"
        self.fields['experience_level_obj'].empty_label = "Chọn mức kinh nghiệm"
        self.fields['work_mode_obj'].empty_label = "Chọn hình thức làm việc"

    def clean(self):
        cleaned_data = super().clean()
        salary_type = cleaned_data.get('salary_type')
        salary_min = cleaned_data.get('salary_min')
        salary_max = cleaned_data.get('salary_max')
        work_mode_obj = cleaned_data.get('work_mode_obj')
        city = (cleaned_data.get('city') or '').strip()

        if salary_type == 'negotiable':
            cleaned_data['salary_min'] = None
            cleaned_data['salary_max'] = None
        elif salary_type == 'fixed':
            if salary_min is None:
                self.add_error('salary_min', 'Vui lòng nhập mức lương cố định.')
            cleaned_data['salary_max'] = salary_min
        elif salary_type == 'range':
            if salary_min is None or salary_max is None:
                self.add_error('salary_min', 'Vui lòng nhập đầy đủ khoảng lương.')
                self.add_error('salary_max', 'Vui lòng nhập đầy đủ khoảng lương.')
            elif salary_min > salary_max:
                self.add_error('salary_max', 'Lương tối đa phải lớn hơn hoặc bằng lương tối thiểu.')

        if work_mode_obj and work_mode_obj.code in {'office', 'hybrid'} and not city:
            self.add_error('city', 'Vui lòng nhập địa điểm làm việc cho hình thức này.')

        return cleaned_data

    def clean_description(self):
        return sanitize_rich_text(self.cleaned_data.get('description'))

    def clean_required_skills(self):
        return sanitize_rich_text(self.cleaned_data.get('required_skills'))


class JobCategoryForm(forms.ModelForm):
    class Meta:
        model = JobCategory
        fields = ('name', 'slug')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ví dụ: Công nghệ thông tin'}),
            'slug': forms.TextInput(attrs={'placeholder': 'vi-du: cong-nghe-thong-tin'}),
        }


class ExperienceLevelForm(forms.ModelForm):
    class Meta:
        model = ExperienceLevel
        fields = ('name', 'code', 'order')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ví dụ: Junior (1-2 năm)'}),
            'code': forms.TextInput(attrs={'placeholder': 'vi-du: junior'}),
            'order': forms.NumberInput(attrs={'placeholder': 'Ví dụ: 1'}),
        }


class WorkModeForm(forms.ModelForm):
    class Meta:
        model = WorkMode
        fields = ('name', 'code')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ví dụ: Làm tại văn phòng'}),
            'code': forms.TextInput(attrs={'placeholder': 'vi-du: office'}),
        }


class EmploymentTypeForm(forms.ModelForm):
    class Meta:
        model = EmploymentType
        fields = ('name', 'code')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ví dụ: Toàn thời gian'}),
            'code': forms.TextInput(attrs={'placeholder': 'vi-du: fulltime'}),
        }
