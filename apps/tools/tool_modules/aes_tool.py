"""
AES 加密解密工具
"""

from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool

import base64

try:
    # 仅用于探测依赖是否安装
    import Crypto  # type: ignore[import-untyped]  # noqa: F401

    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


class AESForm(forms.Form):
    """AES表单"""

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
        label="密钥（16/24/32字节）",
        max_length=32,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "输入加密密钥"}),
        required=True,
    )


class AESTool(BaseTool):
    """AES加密解密工具"""

    name = "AES加密"
    slug = "aes"
    description = "AES对称加密解密工具"
    icon = "fa fa-key"
    category = ToolCategory.ENCRYPT
    form_class = AESForm

    def handle(self, request, form):
        if not HAS_CRYPTO:
            return {"error": "请安装 pycryptodome: pip install pycryptodome"}

        # 延迟导入，避免缺依赖时模块加载失败，并让类型检查更稳定
        from Crypto.Cipher import AES  # nosec B413 - 使用 pycryptodome（非废弃 pycrypto）
        from Crypto.Util.Padding import pad, unpad  # nosec B413 - 使用 pycryptodome

        mode = form.cleaned_data["mode"]
        text = form.cleaned_data["text"]
        key = form.cleaned_data["key"].encode("utf-8")

        # 密钥长度调整
        if len(key) < 16:
            key = key.ljust(16, b"0")
        elif len(key) < 24:
            key = key.ljust(24, b"0")
        elif len(key) < 32:
            key = key.ljust(32, b"0")
        else:
            key = key[:32]

        try:
            if mode == "encrypt":
                cipher = AES.new(key, AES.MODE_CBC)
                ct_bytes = cipher.encrypt(pad(text.encode("utf-8"), AES.block_size))
                iv = cipher.iv
                result = base64.b64encode(iv + ct_bytes).decode("utf-8")
                return {"mode": "encrypt", "result": result}
            else:
                raw = base64.b64decode(text)
                iv = raw[:16]
                ct = raw[16:]
                cipher = AES.new(key, AES.MODE_CBC, iv)
                pt = unpad(cipher.decrypt(ct), AES.block_size)
                return {"mode": "decrypt", "result": pt.decode("utf-8")}
        except Exception as e:
            return {"error": str(e)}
