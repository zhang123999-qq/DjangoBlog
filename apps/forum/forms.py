from django import forms
from .models import Topic, Reply


class TopicForm(forms.ModelForm):
    """主题表单"""
    class Meta:
        model = Topic
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入主题标题'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 8, 'placeholder': '请输入主题内容'}),
        }


class ReplyForm(forms.ModelForm):
    """回复表单"""
    class Meta:
        model = Reply
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '请输入回复内容'}),
        }
