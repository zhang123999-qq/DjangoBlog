"""
安装向导表单
"""
from django import forms
from django.core.exceptions import ValidationError
import re


class Step1EnvironmentForm(forms.Form):
    """环境检查表单"""
    confirm = forms.BooleanField(
        label='我已确认环境满足要求',
        required=True,
        error_messages={'required': '请确认环境满足要求'}
    )


class Step2SiteForm(forms.Form):
    """网站配置表单"""
    site_name = forms.CharField(
        label='网站名称',
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '例如：我的博客',
            'autocomplete': 'off'
        }),
        help_text='显示在浏览器标签上的名称'
    )
    site_title = forms.CharField(
        label='网站标题',
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '例如：我的个人博客',
            'autocomplete': 'off'
        }),
        help_text='显示在网站首页的标题'
    )
    site_description = forms.CharField(
        label='网站描述',
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': '简短描述您的网站...'
        }),
        help_text='用于SEO和网站介绍'
    )
    site_keywords = forms.CharField(
        label='网站关键词',
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '例如：博客,技术,Python',
            'autocomplete': 'off'
        }),
        help_text='用逗号分隔的关键词'
    )
    allowed_hosts = forms.CharField(
        label='允许访问的主机',
        max_length=500,
        required=False,
        initial='localhost,127.0.0.1,0.0.0.0,*',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'localhost,127.0.0.1,0.0.0.0,*',
            'autocomplete': 'off'
        }),
        help_text='允许访问网站的域名或IP，用逗号分隔。* 表示允许所有'
    )
    
    def clean_site_name(self):
        name = self.cleaned_data['site_name']
        if len(name) < 2:
            raise ValidationError('网站名称至少2个字符')
        return name


class Step3AdminForm(forms.Form):
    """管理员配置表单"""
    admin_username = forms.CharField(
        label='管理员用户名',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'admin',
            'autocomplete': 'off'
        }),
        help_text='用于登录管理后台'
    )
    admin_email = forms.EmailField(
        label='管理员邮箱',
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'admin@example.com',
            'autocomplete': 'off'
        })
    )
    admin_password1 = forms.CharField(
        label='管理员密码',
        min_length=8,
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '至少8个字符',
            'autocomplete': 'new-password'
        }),
        help_text='至少8个字符，建议包含大小写字母、数字和特殊符号'
    )
    admin_password2 = forms.CharField(
        label='确认密码',
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '再次输入密码',
            'autocomplete': 'new-password'
        })
    )

    def clean_admin_username(self):
        username = self.cleaned_data['admin_username']
        if not re.match(r'^[\w.@+-]+$', username):
            raise ValidationError('用户名只能包含字母、数字和@.+-_符号')
        if len(username) < 3:
            raise ValidationError('用户名至少3个字符')
        return username

    def clean_admin_password1(self):
        password = self.cleaned_data['admin_password1']
        if len(password) < 8:
            raise ValidationError('密码至少8个字符')
        if password.isdigit():
            raise ValidationError('密码不能全是数字')
        return password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('admin_password1')
        password2 = cleaned_data.get('admin_password2')
        
        if password1 and password2 and password1 != password2:
            self.add_error('admin_password2', '两次输入的密码不一致')
        
        return cleaned_data


class Step4DatabaseForm(forms.Form):
    """数据库配置表单"""
    db_engine = forms.ChoiceField(
        label='数据库类型',
        choices=[
            ('django.db.backends.sqlite3', 'SQLite（推荐用于开发测试）'),
            ('django.db.backends.mysql', 'MySQL（推荐用于生产环境）'),
            ('django.db.backends.postgresql', 'PostgreSQL（推荐用于生产环境）')
        ],
        initial='django.db.backends.sqlite3',
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'db-engine-select'})
    )
    db_name = forms.CharField(
        label='数据库名称',
        max_length=100,
        required=True,
        initial='djangoblog',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'djangoblog'
        })
    )
    db_user = forms.CharField(
        label='数据库用户名',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control db-mysql-field',
            'placeholder': 'root'
        })
    )
    db_password = forms.CharField(
        label='数据库密码',
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control db-mysql-field',
            'placeholder': '输入密码',
            'autocomplete': 'new-password'
        })
    )
    db_host = forms.CharField(
        label='数据库主机',
        max_length=100,
        required=False,
        initial='localhost',
        widget=forms.TextInput(attrs={
            'class': 'form-control db-mysql-field',
            'placeholder': 'localhost'
        })
    )
    db_port = forms.CharField(
        label='数据库端口',
        max_length=10,
        required=False,
        initial='3306',
        widget=forms.TextInput(attrs={
            'class': 'form-control db-mysql-field',
            'placeholder': '3306'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        db_engine = cleaned_data.get('db_engine')
        
        # 如果是MySQL或PostgreSQL，检查必填字段
        if db_engine and 'mysql' in db_engine:
            if not cleaned_data.get('db_user'):
                self.add_error('db_user', 'MySQL需要填写数据库用户名')
            if not cleaned_data.get('db_host'):
                self.add_error('db_host', 'MySQL需要填写数据库主机')
        
        return cleaned_data


class Step5RedisForm(forms.Form):
    """Redis配置表单"""
    use_redis = forms.BooleanField(
        label='启用Redis缓存',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'use-redis-check'})
    )
    redis_host = forms.CharField(
        label='Redis主机',
        max_length=100,
        required=False,
        initial='localhost',
        widget=forms.TextInput(attrs={
            'class': 'form-control redis-field',
            'placeholder': 'localhost'
        })
    )
    redis_port = forms.CharField(
        label='Redis端口',
        max_length=10,
        required=False,
        initial='6379',
        widget=forms.TextInput(attrs={
            'class': 'form-control redis-field',
            'placeholder': '6379'
        })
    )
    redis_password = forms.CharField(
        label='Redis密码',
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control redis-field',
            'placeholder': '如果未设置密码请留空',
            'autocomplete': 'new-password'
        })
    )
    redis_db = forms.IntegerField(
        label='Redis数据库',
        required=False,
        initial=0,
        min_value=0,
        max_value=15,
        widget=forms.NumberInput(attrs={
            'class': 'form-control redis-field',
            'placeholder': '0'
        })
    )


class QuickInstallForm(forms.Form):
    """快速安装表单"""
    site_name = forms.CharField(
        label='网站名称',
        max_length=100,
        initial='Django Blog',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    admin_username = forms.CharField(
        label='管理员用户名',
        max_length=150,
        initial='admin',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    admin_email = forms.EmailField(
        label='管理员邮箱',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    admin_password = forms.CharField(
        label='管理员密码',
        min_length=8,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    allowed_hosts = forms.CharField(
        label='允许访问的主机',
        max_length=500,
        required=False,
        initial='localhost,127.0.0.1,0.0.0.0,*',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'localhost,127.0.0.1,0.0.0.0,*'
        }),
        help_text='允许局域网访问请保持默认，或填写*允许所有'
    )
