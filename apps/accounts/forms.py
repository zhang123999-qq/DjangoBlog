from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from .models import User, Profile
from .captcha import validate_captcha


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
        if not validate_captcha(self.request, captcha):
            raise forms.ValidationError('验证码错误')
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
        if not validate_captcha(self.request, captcha):
            raise forms.ValidationError('验证码错误')
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
            if avatar.size > 1024 * 1024:  # 限制 1MB
                raise forms.ValidationError('头像大小不能超过 1MB')
        return avatar