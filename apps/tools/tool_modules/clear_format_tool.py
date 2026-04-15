"""
清除文本格式工具
"""

from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool
import re
import html


class ClearFormatForm(forms.Form):
    """清除文本格式表单"""

    text = forms.CharField(
        label="文本内容",
        widget=forms.Textarea(attrs={"rows": 15, "class": "form-control", "placeholder": "粘贴带格式的文本..."}),
        required=True,
    )
    remove_html = forms.BooleanField(
        label="移除HTML标签",
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    remove_markdown = forms.BooleanField(
        label="移除Markdown格式",
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    decode_entities = forms.BooleanField(
        label="解码HTML实体",
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    normalize_whitespace = forms.BooleanField(
        label="规范化空白字符",
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    remove_urls = forms.BooleanField(
        label="移除URL链接",
        initial=False,
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    remove_emails = forms.BooleanField(
        label="移除邮箱地址",
        initial=False,
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )


class ClearFormatTool(BaseTool):
    """清除文本格式工具"""

    name = "清除文本格式"
    slug = "clear-format"
    description = "一键去除富文本格式，得到纯文本"
    icon = "fa fa-eraser"
    category = ToolCategory.TEXT
    form_class = ClearFormatForm

    def handle(self, request, form):
        text = form.cleaned_data["text"]
        remove_html = form.cleaned_data["remove_html"]
        remove_markdown = form.cleaned_data["remove_markdown"]
        decode_entities = form.cleaned_data["decode_entities"]
        normalize_whitespace = form.cleaned_data["normalize_whitespace"]
        remove_urls = form.cleaned_data["remove_urls"]
        remove_emails = form.cleaned_data["remove_emails"]

        original_length = len(text)

        try:
            result = text

            # 移除HTML标签
            if remove_html:
                result = self._remove_html(result)

            # 解码HTML实体
            if decode_entities:
                result = html.unescape(result)

            # 移除Markdown格式
            if remove_markdown:
                result = self._remove_markdown(result)

            # 移除URL
            if remove_urls:
                result = re.sub(r'https?://[^\s<>"{}|\\^`\[\]]+', "", result)
                result = re.sub(r'www\.[^\s<>"{}|\\^`\[\]]+', "", result)

            # 移除邮箱
            if remove_emails:
                result = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "", result)

            # 规范化空白字符
            if normalize_whitespace:
                # 将多个空白字符替换为单个空格
                result = re.sub(r"[ \t]+", " ", result)
                # 将多个换行替换为单个换行
                result = re.sub(r"\n{3,}", "\n\n", result)
                # 去除每行首尾空白
                lines = [line.strip() for line in result.split("\n")]
                result = "\n".join(lines)

            result = result.strip()
            result_length = len(result)

            return {
                "result": result,
                "stats": {
                    "original_length": original_length,
                    "result_length": result_length,
                    "removed_chars": original_length - result_length,
                    "compression": (
                        f"{((original_length - result_length) / original_length * 100):.1f}%"
                        if original_length > 0
                        else "0%"
                    ),
                },
            }

        except Exception as e:
            return {"error": f"处理失败: {str(e)}"}

    def _remove_html(self, text):
        """移除HTML标签"""
        # 移除style标签及其内容
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        # 移除script标签及其内容
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
        # 移除注释
        text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
        # 将br、p、div等块级标签转换为换行
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</p>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</div>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</li>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</tr>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</td>", " ", text, flags=re.IGNORECASE)
        text = re.sub(r"</th>", " ", text, flags=re.IGNORECASE)
        # 移除所有其他HTML标签
        text = re.sub(r"<[^>]+>", "", text)
        return text

    def _remove_markdown(self, text):
        """移除Markdown格式"""
        # 移除代码块
        text = re.sub(r"```[\s\S]*?```", "", text)
        text = re.sub(r"`([^`]+)`", r"\1", text)
        # 移除标题标记
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
        # 移除粗体和斜体
        text = re.sub(r"\*\*\*([^*]+)\*\*\*", r"\1", text)
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"\*([^*]+)\*", r"\1", text)
        text = re.sub(r"___([^_]+)___", r"\1", text)
        text = re.sub(r"__([^_]+)__", r"\1", text)
        text = re.sub(r"_([^_]+)_", r"\1", text)
        # 移除删除线
        text = re.sub(r"~~([^~]+)~~", r"\1", text)
        # 移除链接，保留文本
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        # 移除图片
        text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
        # 移除引用标记
        text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)
        # 移除列表标记
        text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
        # 移除水平线
        text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
        return text
