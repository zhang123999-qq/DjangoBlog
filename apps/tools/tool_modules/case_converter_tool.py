"""
大小写转换工具
"""

from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool


class CaseConverterForm(forms.Form):
    """大小写转换表单"""

    text = forms.CharField(
        label="输入文本",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 6, "placeholder": "请输入要转换的文本..."}),
        required=True,
    )


class CaseConverterTool(BaseTool):
    """大小写转换工具"""

    name = "大小写转换"
    slug = "case-converter"
    description = "文本大小写转换（英文）"
    icon = "fa fa-font"
    category = ToolCategory.ENCODE
    form_class = CaseConverterForm

    def handle(self, request, form):
        text = form.cleaned_data["text"]

        return {
            "original": text,
            "uppercase": text.upper(),
            "lowercase": text.lower(),
            "title_case": text.title(),
            "capitalize": text.capitalize(),
            "swap_case": text.swapcase(),
            "char_count": len(text),
            "word_count": len(text.split()) if text.strip() else 0,
        }
