"""
RSA 加密解密工具
"""

from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool


class RSAForm(forms.Form):
    """RSA表单"""

    mode = forms.ChoiceField(
        label="操作",
        choices=[
            ("encrypt", "加密"),
            ("decrypt", "解密"),
        ],
        initial="encrypt",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    text = forms.CharField(
        label="文本内容", widget=forms.Textarea(attrs={"rows": 4, "class": "form-control"}), required=True
    )
    key = forms.CharField(
        label="密钥（PEM格式）",
        widget=forms.Textarea(attrs={"rows": 10, "class": "form-control", "placeholder": "输入PEM格式的密钥"}),
        required=True,
    )


class RSATool(BaseTool):
    """RSA加密解密工具"""

    name = "RSA加密"
    slug = "rsa"
    description = "RSA非对称加密解密工具"
    icon = "fa fa-lock"
    category = ToolCategory.ENCRYPT
    form_class = RSAForm

    def handle(self, request, form):
        try:
            from cryptography.hazmat.primitives import serialization, hashes
            from cryptography.hazmat.primitives.asymmetric import padding
            import base64
        except ImportError:
            return {"error": "请安装 cryptography: pip install cryptography"}

        mode = form.cleaned_data["mode"]
        text = form.cleaned_data["text"]
        key_pem = form.cleaned_data["key"]

        try:
            if mode == "encrypt":
                # 加载公钥
                public_key = serialization.load_pem_public_key(key_pem.encode("utf-8"))
                # 加密
                ciphertext = public_key.encrypt(
                    text.encode("utf-8"),
                    padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
                )
                result = base64.b64encode(ciphertext).decode("utf-8")
                return {"mode": "encrypt", "result": result}
            else:
                # 加载私钥
                private_key = serialization.load_pem_private_key(key_pem.encode("utf-8"), password=None)
                # 解密
                ciphertext = base64.b64decode(text)
                plaintext = private_key.decrypt(
                    ciphertext,
                    padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
                )
                return {"mode": "decrypt", "result": plaintext.decode("utf-8")}
        except Exception as e:
            return {"error": str(e)}
