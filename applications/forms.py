from datetime import date

from django import forms

from .models import Application


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = (
            'candidate_email',
            'candidate_phone',
            'cover_letter',
            'available_date',
            'cv_file',
        )
        widgets = {
            'candidate_email': forms.EmailInput(
                attrs={'placeholder': 'Ví dụ: nguyenvana@gmail.com'}
            ),
            'candidate_phone': forms.TextInput(
                attrs={'placeholder': 'Ví dụ: 09xxxxxxxx'}
            ),
            'cover_letter': forms.Textarea(
                attrs={
                    'rows': 5,
                    'placeholder': 'Giới thiệu ngắn gọn lý do bạn phù hợp với công việc này...',
                }
            ),
            'available_date': forms.DateInput(
                attrs={'type': 'date'}
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['cv_file'].required = False
        self.fields['candidate_email'].required = True
        self.fields['candidate_phone'].required = True
        if self.user:
            self.fields['candidate_email'].initial = getattr(self.user, 'email', '')
            self.fields['candidate_phone'].initial = getattr(self.user, 'phone', '')

    def clean(self):
        cleaned_data = super().clean()
        cv_file = cleaned_data.get('cv_file')
        user_default_cv = getattr(self.user, 'default_cv', None)

        if not cv_file and not user_default_cv:
            self.add_error('cv_file', 'Vui lòng tải CV để ứng tuyển.')
        return cleaned_data

    def clean_available_date(self):
        date_val = self.cleaned_data.get('available_date')
        if date_val and date_val < date.today():
            raise forms.ValidationError('Ngày phải từ hôm nay trở đi.')
        return date_val

    def clean_candidate_phone(self):
        phone = (self.cleaned_data.get('candidate_phone') or '').strip()
        if len(phone) < 8:
            raise forms.ValidationError('Số điện thoại không hợp lệ.')
        return phone


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
