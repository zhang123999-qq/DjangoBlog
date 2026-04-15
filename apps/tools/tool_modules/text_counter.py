"""
文本统计工具（综合版：英文 + 中文 + 标点符号）
"""

from ..categories import ToolCategory
from django import forms
from ..base_tool import BaseTool
import re


class TextCounterForm(forms.Form):
    """文本统计表单"""

    text = forms.CharField(
        label="文本内容",
        widget=forms.Textarea(attrs={"rows": 10, "class": "form-control", "placeholder": "请输入要统计的文本..."}),
        required=True,
    )


class TextCounterTool(BaseTool):
    """文本统计工具（综合版）"""

    name = "文本统计"
    slug = "text-counter"
    description = "综合统计文本的字符数、中英文、数字、标点、行数等信息"
    icon = "fa fa-calculator"
    category = ToolCategory.TEXT
    form_class = TextCounterForm

    def handle(self, request, form):
        """处理文本统计"""
        text = form.cleaned_data["text"]

        # === 基础统计 ===
        total_chars = len(text)
        # 统计字符数（不包括空白）
        non_space_chars = len(re.sub(r"[\s]", "", text))
        # 单词数（英文）
        words = text.split()
        word_count = len(words)
        # 行数
        lines = text.split("\n")
        line_count = len(lines)
        # 段落数（非空段落）
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        paragraph_count = len(paragraphs) or (1 if text.strip() else 0)

        # === 中文统计 ===
        chinese_chars = re.findall(r"[\u4e00-\u9fff]", text)
        chinese_count = len(chinese_chars)

        # === 英文单词统计 ===
        english_words = re.findall(r"[a-zA-Z]+", text)
        english_count = len(english_words)

        # === 数字统计 ===
        numbers = re.findall(r"\d+", text)
        number_count = len("".join(numbers))

        # === 标点符号统计（中文标点 + 英文标点）===
        cn_punctuation = re.findall(r"[\u3000-\u303f\uff00-\uffef]", text)
        en_punctuation = re.findall(r'[.,!?;:"\'()-]', text)
        punctuation_count = len(cn_punctuation) + len(en_punctuation)

        # === 空白字符统计 ===
        space_count = len(re.findall(r"\s", text))
        newline_count = text.count("\n")
        tab_count = text.count("\t")

        return {
            # 基础统计
            "total_chars": total_chars,
            "non_space_chars": non_space_chars,
            "word_count": word_count,
            "line_count": line_count,
            "paragraph_count": paragraph_count,
            # 中文统计
            "chinese_count": chinese_count,
            # 英文统计
            "english_word_count": english_count,
            # 数字统计
            "number_digit_count": number_count,
            # 标点统计
            "punctuation_count": punctuation_count,
            "cn_punctuation_count": len(cn_punctuation),
            "en_punctuation_count": len(en_punctuation),
            # 空白统计
            "space_count": space_count,
            "newline_count": newline_count,
            "tab_count": tab_count,
        }
