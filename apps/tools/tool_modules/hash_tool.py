"""
哈希工具 - MD5, SHA1, SHA256, SHA512
"""

import hashlib
from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool


class HashForm(forms.Form):
    """哈希表单"""

    text = forms.CharField(
        label="输入文本", widget=forms.Textarea(attrs={"rows": 4, "class": "form-control"}), required=True
    )
    algorithm = forms.ChoiceField(
        label="算法",
        choices=[
            ("md5", "MD5"),
            ("sha1", "SHA-1"),
            ("sha256", "SHA-256"),
            ("sha512", "SHA-512"),
        ],
        initial="md5",
        widget=forms.Select(attrs={"class": "form-control"}),
    )


class HashTool(BaseTool):
    """哈希工具"""

    name = "哈希计算"
    slug = "hash"
    description = "计算文本的MD5、SHA-1、SHA-256、SHA-512哈希值"
    icon = "fa fa-lock"
    category = ToolCategory.ENCRYPT
    form_class = HashForm

    def handle(self, request, form):
        """处理哈希计算"""
        text = form.cleaned_data["text"]
        algorithm = form.cleaned_data["algorithm"]

        algorithms = {
            "md5": hashlib.md5,
            "sha1": hashlib.sha1,
            "sha256": hashlib.sha256,
            "sha512": hashlib.sha512,
        }

        hash_obj = algorithms[algorithm](text.encode("utf-8"))
        result = hash_obj.hexdigest()

        return {
            "original": text,
            "algorithm": algorithm.upper(),
            "hash": result,
            "length": len(result),
        }
