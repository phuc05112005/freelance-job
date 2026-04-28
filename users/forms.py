import os
import uuid

from django import forms
from django.conf import settings
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm, UserCreationForm
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

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            raise ValidationError('Vui lòng nhập email.')
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Email này đã tồn tại. Vui lòng dùng email khác.')
        return email


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

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            raise ValidationError('Vui lòng nhập email.')

        duplicate_qs = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            duplicate_qs = duplicate_qs.exclude(pk=self.instance.pk)

        if duplicate_qs.exists():
            raise ValidationError('Email này đã được dùng cho tài khoản khác.')
        return email

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


class CustomPasswordResetForm(PasswordResetForm):
    username = forms.CharField(
        required=True,
        label='Tên đăng nhập',
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Nhập tên đăng nhập'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        email = (cleaned_data.get('email') or '').strip().lower()
        username = (cleaned_data.get('username') or '').strip()

        if not email or not username:
            return cleaned_data

        user = User.objects.filter(username__iexact=username).first()
        if user is None:
            self.add_error('email', 'Tên đăng nhập và email không khớp. Vui lòng kiểm tra lại.')
            return cleaned_data

        user_email = (user.email or '').strip().lower()
        if user_email != email:
            self.add_error('email', 'Tên đăng nhập và email không khớp. Vui lòng kiểm tra lại.')
            return cleaned_data

        self.user_cache = user
        cleaned_data['email'] = email
        cleaned_data['username'] = username
        return cleaned_data

    def get_users(self, email):
        user = getattr(self, 'user_cache', None)
        if user is None:
            return []
        if not user.is_active:
            return []
        if not user.has_usable_password():
            return []
        return [user]
