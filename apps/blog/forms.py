from django import forms
from .models import Comment


class CommentForm(forms.ModelForm):
    """评论表单"""
    class Meta:
        model = Comment
        fields = ['content', 'name', 'email']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': '请输入评论内容...'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '您的姓名'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': '您的邮箱'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # 如果用户已登录，隐藏姓名和邮箱字段
        if self.user and self.user.is_authenticated:
            # 使用 del 安全删除字段
            if 'name' in self.fields:
                del self.fields['name']
            if 'email' in self.fields:
                del self.fields['email']
        else:
            # 游客评论，姓名和邮箱必填
            self.fields['name'].required = True
            self.fields['email'].required = True
