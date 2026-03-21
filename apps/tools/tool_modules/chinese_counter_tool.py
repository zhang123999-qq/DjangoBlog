"""
中文字数统计工具
"""
from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool
import re


class ChineseCounterForm(forms.Form):
    """中文字数统计表单"""
    text = forms.CharField(
        label='输入文本',
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'rows': 8,
            'placeholder': '请输入要统计的中文文本...'
        }),
        required=True
    )


class ChineseCounterTool(BaseTool):
    """中文字数统计工具"""
    name = "中文字数统计"
    slug = "chinese-counter"
    description = "精确统计中文字数、行数、段落数"
    icon = "fa fa-calculator"
    category = ToolCategory.TEXT
    form_class = ChineseCounterForm

    def handle(self, request, form):
        text = form.cleaned_data['text']
        
        # 统计中文字符
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        chinese_count = len(chinese_chars)
        
        # 统计英文单词
        english_words = re.findall(r'[a-zA-Z]+', text)
        english_count = len(english_words)
        
        # 统计数字
        numbers = re.findall(r'\d+', text)
        number_count = len(''.join(numbers))
        
        # 总字符数
        total_chars = len(text)
        
        # 去除空白后的字符数
        non_space_chars = len(text.replace(' ', '').replace('\n', '').replace('\t', ''))
        
        # 行数
        lines = text.split('\n')
        line_count = len(lines)
        
        # 段落数（非空段落）
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        paragraph_count = len(paragraphs) or (1 if text.strip() else 0)
        
        # 标点符号统计
        punctuation = re.findall(r'[，。、！？；：""''（）【】《》…—]', text)
        punctuation_count = len(punctuation)
        
        return {
            'text': text,
            'chinese_count': chinese_count,
            'english_count': english_count,
            'number_count': number_count,
            'total_chars': total_chars,
            'non_space_chars': non_space_chars,
            'line_count': line_count,
            'paragraph_count': paragraph_count,
            'punctuation_count': punctuation_count,
            'word_count': chinese_count + english_count,  # 混合计词
        }
