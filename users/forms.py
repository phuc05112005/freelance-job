from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'university',
            'major',
            'academic_year',
            'skills',
            'default_cv',
            'password1',
            'password2',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = (
            ('student', 'Sinh viên'),
            ('employer', 'Nhà tuyển dụng/Khách hàng'),
        )
        self.fields['email'].required = True
        self.fields['skills'].widget = forms.Textarea(
            attrs={'rows': 3}
        )
