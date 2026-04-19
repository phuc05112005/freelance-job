import os
import uuid

from django import forms
from django.conf import settings
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage

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
        self.fields['skills'].widget = forms.Textarea(attrs={'rows': 3})


class ProfileUpdateForm(forms.ModelForm):
    avatar_upload = forms.FileField(
        required=False,
        label='Ảnh đại diện',
        widget=forms.FileInput(attrs={'accept': 'image/*'}),
    )
    remove_avatar = forms.BooleanField(required=False, label='Xóa ảnh hiện tại')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone')
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Nhập tên đăng nhập'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'Nhập họ'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Nhập tên'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Nhập email'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Nhập số điện thoại'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True

    def clean_avatar_upload(self):
        avatar = self.cleaned_data.get('avatar_upload')
        if not avatar:
            return avatar

        allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
        filename = avatar.name.lower()
        if '.' not in filename or filename[filename.rfind('.'):].lower() not in allowed_extensions:
            raise ValidationError('Ảnh không hợp lệ. Chỉ hỗ trợ JPG, PNG, WEBP, GIF.')
        if avatar.size > 5 * 1024 * 1024:
            raise ValidationError('Dung lượng ảnh tối đa là 5MB.')
        return avatar

    def save(self, commit=True):
        user = super().save(commit=False)
        uploaded_avatar = self.cleaned_data.get('avatar_upload')
        remove_avatar = self.cleaned_data.get('remove_avatar')

        if remove_avatar and not uploaded_avatar:
            self._delete_local_avatar(user.avatar_url)
            user.avatar_url = ''

        if uploaded_avatar:
            self._delete_local_avatar(user.avatar_url)

            ext = os.path.splitext(uploaded_avatar.name)[1].lower() or '.jpg'
            file_name = f'avatars/{uuid.uuid4().hex}{ext}'
            saved_path = default_storage.save(file_name, uploaded_avatar)
            media_url = settings.MEDIA_URL if settings.MEDIA_URL.endswith('/') else f'{settings.MEDIA_URL}/'
            user.avatar_url = f"{media_url}{saved_path.replace('\\', '/')}"

        if commit:
            user.save()
        return user

    @staticmethod
    def _delete_local_avatar(avatar_url):
        if not avatar_url:
            return

        media_url = settings.MEDIA_URL if settings.MEDIA_URL.endswith('/') else f'{settings.MEDIA_URL}/'
        if not avatar_url.startswith(media_url):
            return

        relative_path = avatar_url[len(media_url):].lstrip('/').replace('\\', '/')
        if not relative_path.startswith('avatars/'):
            return

        if default_storage.exists(relative_path):
            default_storage.delete(relative_path)


class AccountPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update(
            {'placeholder': 'Nhập mật khẩu hiện tại'}
        )
        self.fields['new_password1'].widget.attrs.update(
            {'placeholder': 'Nhập mật khẩu mới'}
        )
        self.fields['new_password2'].widget.attrs.update(
            {'placeholder': 'Nhập lại mật khẩu mới'}
        )
