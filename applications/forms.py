from django import forms

from .models import Application


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = (
            'cover_letter',
            'expected_salary',
            'estimated_days',
            'portfolio_url',
            'cv_file',
        )
        widgets = {
            'cover_letter': forms.Textarea(
                attrs={'rows': 5, 'placeholder': 'Giới thiệu ngắn gọn lý do bạn phù hợp với dự án...'}
            ),
            'portfolio_url': forms.URLInput(
                attrs={'placeholder': 'Ví dụ: https://github.com/yourname/portfolio'}
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['cv_file'].required = False

    def clean(self):
        cleaned_data = super().clean()
        cv_file = cleaned_data.get('cv_file')
        user_default_cv = getattr(self.user, 'default_cv', None)

        if not cv_file and not user_default_cv:
            self.add_error('cv_file', 'Vui lòng tải CV để ứng tuyển.')
        return cleaned_data


class ApplicationStatusForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ('status',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = (
            ('accepted', 'Chấp nhận'),
            ('rejected', 'Từ chối'),
        )
