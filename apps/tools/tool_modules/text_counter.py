from ..categories import ToolCategory
from django import forms
from ..base_tool import BaseTool


class TextCounterForm(forms.Form):
    """文本统计表单"""
    text = forms.CharField(label='文本内容', widget=forms.Textarea(attrs={'rows': 10}), required=True)


class TextCounterTool(BaseTool):
    """文本统计工具"""
    name = "文本统计"
    slug = "text-counter"
    description = "统计文本的字符数、单词数、行数等信息"
    icon = "file-text"
    category = ToolCategory.TEXT
    form_class = TextCounterForm

    def handle(self, request, form):
        """处理文本统计"""
        text = form.cleaned_data['text']

        # 统计字符数（包括空格）
        char_count = len(text)
        # 统计字符数（不包括空格）
        char_count_no_space = len(text.replace(' ', ''))
        # 统计单词数
        words = text.split()
        word_count = len(words)
        # 统计行数
        lines = text.split('\n')
        line_count = len(lines)
        # 统计段落数
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        paragraph_count = len(paragraphs)

        return {
            "char_count": char_count,
            "char_count_no_space": char_count_no_space,
            "word_count": word_count,
            "line_count": line_count,
            "paragraph_count": paragraph_count,
        }
