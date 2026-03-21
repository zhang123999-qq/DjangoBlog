from django import forms
from .models import Comment, Post, Category, Tag


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


class PostForm(forms.ModelForm):
    """文章编辑表单"""
    class Meta:
        model = Post
        fields = ['title', 'summary', 'content', 'category', 'tags', 'status', 'allow_comments']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': '请输入文章标题',
                'data-editor': 'none'
            }),
            'summary': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '请输入文章摘要（可选，用于SEO和列表显示）'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 20,
                'data-editor': 'tinymce',
                'data-height': '500'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tags': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': 5
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'allow_comments': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置分类和标签选项
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].empty_label = '请选择分类'
        self.fields['tags'].queryset = Tag.objects.all()
        
        # 可选字段提示
        self.fields['summary'].required = False
        self.fields['category'].required = False
        self.fields['tags'].required = False
