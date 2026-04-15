"""
HMAC 生成验证工具
"""

from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool
import hmac
import hashlib
import base64


class HMACForm(forms.Form):
    """HMAC表单"""

    key = forms.CharField(
        label="密钥",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "输入HMAC密钥"}),
        required=True,
    )
    message = forms.CharField(
        label="消息", widget=forms.Textarea(attrs={"rows": 3, "class": "form-control"}), required=True
    )
    algorithm = forms.ChoiceField(
        label="哈希算法",
        choices=[
            ("md5", "MD5"),
            ("sha1", "SHA1"),
            ("sha256", "SHA256"),
            ("sha512", "SHA512"),
        ],
        initial="sha256",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    output_format = forms.ChoiceField(
        label="输出格式",
        choices=[
            ("hex", "十六进制"),
            ("base64", "Base64"),
        ],
        initial="hex",
        widget=forms.Select(attrs={"class": "form-control"}),
    )


class HMACTool(BaseTool):
    """HMAC生成验证工具"""

    name = "HMAC生成"
    slug = "hmac"
    description = "基于哈希函数生成消息认证码"
    icon = "fa fa-shield"
    category = ToolCategory.ENCRYPT
    form_class = HMACForm

    def handle(self, request, form):
        key = form.cleaned_data["key"].encode("utf-8")
        message = form.cleaned_data["message"].encode("utf-8")
        algorithm = form.cleaned_data["algorithm"]
        output_format = form.cleaned_data["output_format"]

        try:
            # 选择哈希算法
            if algorithm == "md5":
                hash_func = hashlib.md5
            elif algorithm == "sha1":
                hash_func = hashlib.sha1
            elif algorithm == "sha256":
                hash_func = hashlib.sha256
            elif algorithm == "sha512":
                hash_func = hashlib.sha512
            else:
                return {"error": "不支持的哈希算法"}

            # 生成HMAC
            h = hmac.new(key, message, hash_func)
            digest = h.digest()

            # 格式化输出
            if output_format == "hex":
                result = digest.hex()
            else:
                result = base64.b64encode(digest).decode("utf-8")

            return {
                "key": form.cleaned_data["key"],
                "message": form.cleaned_data["message"],
                "algorithm": algorithm.upper(),
                "result": result,
            }
        except Exception as e:
            return {"error": str(e)}
