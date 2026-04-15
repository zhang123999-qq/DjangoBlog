from django import forms
from .models import Topic, Reply

# 常量定义
TOPIC_TITLE_MIN_LENGTH = 5
TOPIC_TITLE_MAX_LENGTH = 200
TOPIC_CONTENT_MIN_LENGTH = 10
TOPIC_CONTENT_MAX_LENGTH = 10000
REPLY_CONTENT_MIN_LENGTH = 5
REPLY_CONTENT_MAX_LENGTH = 5000


class TopicForm(forms.ModelForm):
    """主题表单"""

    class Meta:
        model = Topic
        fields = ["title", "content"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "请输入主题标题"}),
            "content": forms.Textarea(attrs={"class": "form-control", "rows": 8, "placeholder": "请输入主题内容"}),
        }

    def clean_title(self):
        """验证主题标题"""
        title = self.cleaned_data.get("title", "").strip()
        if len(title) < TOPIC_TITLE_MIN_LENGTH:
            raise forms.ValidationError(f"主题标题至少需要 {TOPIC_TITLE_MIN_LENGTH} 个字符")
        if len(title) > TOPIC_TITLE_MAX_LENGTH:
            raise forms.ValidationError(f"主题标题不能超过 {TOPIC_TITLE_MAX_LENGTH} 个字符")
        return title

    def clean_content(self):
        """验证主题内容"""
        content = self.cleaned_data.get("content", "").strip()
        if len(content) < TOPIC_CONTENT_MIN_LENGTH:
            raise forms.ValidationError(f"主题内容至少需要 {TOPIC_CONTENT_MIN_LENGTH} 个字符")
        if len(content) > TOPIC_CONTENT_MAX_LENGTH:
            raise forms.ValidationError(f"主题内容不能超过 {TOPIC_CONTENT_MAX_LENGTH} 个字符")
        return content


class ReplyForm(forms.ModelForm):
    """回复表单"""

    class Meta:
        model = Reply
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "请输入回复内容"}),
        }

    def clean_content(self):
        """验证回复内容"""
        content = self.cleaned_data.get("content", "").strip()
        if len(content) < REPLY_CONTENT_MIN_LENGTH:
            raise forms.ValidationError(f"回复内容至少需要 {REPLY_CONTENT_MIN_LENGTH} 个字符")
        if len(content) > REPLY_CONTENT_MAX_LENGTH:
            raise forms.ValidationError(f"回复内容不能超过 {REPLY_CONTENT_MAX_LENGTH} 个字符")
        return content
