"""
JWT 工具 - 解码和生成
"""

import json
import base64
from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool


class JWTForm(forms.Form):
    """JWT表单"""

    mode = forms.ChoiceField(
        label="操作",
        choices=[
            ("decode", "解码JWT"),
            ("encode", "生成JWT"),
        ],
        initial="decode",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    token = forms.CharField(
        label="JWT Token",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "class": "form-control", "placeholder": "粘贴JWT Token"}),
    )
    header = forms.CharField(
        label="Header (JSON)",
        required=False,
        widget=forms.Textarea(
            attrs={"rows": 2, "class": "form-control", "placeholder": '{"alg": "HS256", "typ": "JWT"}'}
        ),
        initial='{"alg": "HS256", "typ": "JWT"}',
    )
    payload = forms.CharField(
        label="Payload (JSON)",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "class": "form-control", "placeholder": '{"sub": "1234567890"}'}),
    )


class JWTTool(BaseTool):
    """JWT工具"""

    name = "JWT工具"
    slug = "jwt"
    description = "JWT解码和生成工具"
    icon = "fa fa-id-card"
    category = ToolCategory.ENCRYPT
    form_class = JWTForm

    def base64url_decode(self, data):
        """Base64URL解码"""
        padding = 4 - len(data) % 4
        if padding != 4:
            data += "=" * padding
        return base64.urlsafe_b64decode(data)

    def base64url_encode(self, data):
        """Base64URL编码"""
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

    def handle(self, request, form):
        mode = form.cleaned_data["mode"]

        try:
            if mode == "decode":
                token = form.cleaned_data.get("token", "")
                if not token:
                    return {"error": "请输入JWT Token"}

                parts = token.split(".")
                if len(parts) != 3:
                    return {"error": "无效的JWT格式"}

                # 解码各部分
                header = json.loads(self.base64url_decode(parts[0]))
                payload = json.loads(self.base64url_decode(parts[1]))
                signature = parts[2]

                return {
                    "mode": "decode",
                    "header": header,
                    "payload": payload,
                    "signature": signature,
                    "header_json": json.dumps(header, indent=2),
                    "payload_json": json.dumps(payload, indent=2),
                }
            else:
                # 生成JWT（仅作演示，不验证签名）
                header_str = form.cleaned_data.get("header", "{}")
                payload_str = form.cleaned_data.get("payload", "{}")

                header = json.loads(header_str) if header_str else {}
                payload = json.loads(payload_str) if payload_str else {}

                # 编码
                header_b64 = self.base64url_encode(json.dumps(header).encode())
                payload_b64 = self.base64url_encode(json.dumps(payload).encode())
                signature_b64 = self.base64url_encode(b"fake-signature")

                token = f"{header_b64}.{payload_b64}.{signature_b64}"

                return {
                    "mode": "encode",
                    "token": token,
                    "header": header,
                    "payload": payload,
                    "note": "注意：此工具生成的JWT签名无效，仅用于测试",
                }
        except Exception as e:
            return {"error": str(e)}
