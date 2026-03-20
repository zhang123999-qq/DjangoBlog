"""
邮箱格式验证工具
"""
from django import forms
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from apps.tools.base_tool import BaseTool
import re


class EmailValidatorForm(forms.Form):
    """邮箱验证表单"""
    email = forms.CharField(
        label='输入邮箱地址',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '例如：example@domain.com'
        }),
        required=True
    )


class EmailValidatorTool(BaseTool):
    """邮箱格式验证工具"""
    name = "邮箱验证"
    slug = "email-validator"
    description = "验证邮箱地址格式是否正确"
    icon = "fa fa-envelope"
    form_class = EmailValidatorForm

    def handle(self, request, form):
        email = form.cleaned_data['email'].strip()
        
        # 基本格式检查
        is_valid = True
        message = ''
        
        # 正则检查
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            is_valid = False
            message = '邮箱格式不正确'
        else:
            # Django验证
            try:
                validate_email(email)
                is_valid = True
                message = '邮箱格式正确'
            except ValidationError:
                is_valid = False
                message = '邮箱格式不正确'
        
        # 提取邮箱各部分
        parts = email.split('@') if '@' in email else ['', '']
        
        return {
            'email': email,
            'is_valid': is_valid,
            'message': message,
            'username': parts[0] if len(parts) > 0 else '',
            'domain': parts[1] if len(parts) > 1 else '',
        }
