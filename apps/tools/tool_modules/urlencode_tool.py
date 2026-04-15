"""
URL 编码解码工具
"""

from urllib.parse import quote, unquote
from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool


class URLEncodeForm(forms.Form):
    """URL编码表单"""

    mode = forms.ChoiceField(
        label="操作",
        choices=[
            ("encode", "编码"),
            ("decode", "解码"),
        ],
        initial="encode",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    text = forms.CharField(
        label="文本内容", widget=forms.Textarea(attrs={"rows": 4, "class": "form-control"}), required=True
    )
    safe = forms.CharField(
        label="保留字符",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "默认: /"}),
        initial="/",
    )


class URLEncodeTool(BaseTool):
    """URL编码解码工具"""

    name = "URL编码"
    slug = "urlencode"
    description = "URL编码和解码工具"
    icon = "fa fa-link"
    category = ToolCategory.ENCODE
    form_class = URLEncodeForm

    def handle(self, request, form):
        mode = form.cleaned_data["mode"]
        text = form.cleaned_data["text"]
        safe = form.cleaned_data["safe"] or ""

        try:
            if mode == "encode":
                result = quote(text, safe=safe)
            else:
                result = unquote(text)

            return {
                "mode": mode,
                "original": text,
                "result": result,
            }
        except Exception as e:
            return {"error": str(e)}
