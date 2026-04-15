import os
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from .models import User, Profile
from .captcha import validate_captcha

# 常量定义
MAX_AVATAR_SIZE = 1024 * 1024  # 1MB
ALLOWED_AVATAR_CONTENT_TYPES = ['image/jpeg', 'image/png', 'image/gif']
ALLOWED_AVATAR_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif']


class CustomLoginForm(AuthenticationForm):
    """自定义登录表单，添加 Bootstrap 样式和验证码"""
    captcha = forms.CharField(
        label='验证码',
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入验证码'})
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

    def clean_captcha(self):
        """验证验证码"""
        captcha = self.cleaned_data.get('captcha')
        is_valid, error_msg = validate_captcha(self.request, captcha)
        if not is_valid:
            raise forms.ValidationError(error_msg or '验证码错误')
        return captcha


class UserRegisterForm(UserCreationForm):
    """用户注册表单"""
    email = forms.EmailField(required=True)
    captcha = forms.CharField(
        label='验证码',
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入验证码'})
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

    def clean_captcha(self):
        """验证验证码"""
        captcha = self.cleaned_data.get('captcha')
        is_valid, error_msg = validate_captcha(self.request, captcha)
        if not is_valid:
            raise forms.ValidationError(error_msg or '验证码错误')
        return captcha

    class Meta:
        model = User
        fields = ['username', 'email', 'nickname', 'password1', 'password2', 'captcha']


class UserUpdateForm(UserChangeForm):
    """用户资料更新表单"""
    password = None  # 不包含密码字段

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = User
        fields = ['username', 'email', 'nickname']


class ProfileUpdateForm(forms.ModelForm):
    """Profile 更新表单"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == 'avatar':
                field.widget.attrs.update({'class': 'form-control form-control-file'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = Profile
        fields = ['avatar', 'bio', 'website']

    def clean_avatar(self):
        """验证头像上传限制"""
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            # 大小限制
            if avatar.size > MAX_AVATAR_SIZE:
                raise forms.ValidationError(f'头像大小不能超过 {MAX_AVATAR_SIZE // 1024 // 1024}MB')
            
            # 文件类型白名单
            if hasattr(avatar, 'content_type') and avatar.content_type not in ALLOWED_AVATAR_CONTENT_TYPES:
                raise forms.ValidationError('仅支持 JPG、PNG、GIF 格式的图片')
            
            # 文件扩展名验证
            ext = os.path.splitext(avatar.name)[1].lower()
            if ext not in ALLOWED_AVATAR_EXTENSIONS:
                raise forms.ValidationError('不支持的文件格式，请上传 JPG、PNG 或 GIF 图片')
        return avatar
