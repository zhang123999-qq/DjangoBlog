"""
字符串反转工具
"""

from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool


class StringReverseForm(forms.Form):
    """字符串反转表单"""

    text = forms.CharField(
        label="输入字符串", widget=forms.Textarea(attrs={"rows": 4, "class": "form-control"}), required=True
    )


class StringReverseTool(BaseTool):
    """字符串反转工具"""

    name = "字符串反转"
    slug = "string-reverse"
    description = "将输入的字符串反转"
    icon = "fa fa-arrows-rotate"
    category = ToolCategory.ENCODE
    form_class = StringReverseForm

    def handle(self, request, form):
        text = form.cleaned_data["text"]

        try:
            result = text[::-1]

            return {"original": text, "result": result}
        except Exception as e:
            return {"error": str(e)}
