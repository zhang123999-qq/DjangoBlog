"""
二维码生成工具
"""

from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool

try:
    import qrcode
    from io import BytesIO
    import base64

    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False


class QRCodeForm(forms.Form):
    """二维码表单"""

    text = forms.CharField(
        label="文本内容",
        widget=forms.Textarea(attrs={"rows": 3, "class": "form-control", "placeholder": "输入要生成二维码的内容"}),
        required=True,
    )
    size = forms.ChoiceField(
        label="尺寸",
        choices=[
            ("small", "小 (200x200)"),
            ("medium", "中 (300x300)"),
            ("large", "大 (400x400)"),
        ],
        initial="medium",
        widget=forms.Select(attrs={"class": "form-control"}),
    )


class QRCodeTool(BaseTool):
    """二维码生成工具"""

    name = "二维码生成"
    slug = "qrcode"
    description = "生成二维码图片"
    icon = "fa fa-qrcode"
    category = ToolCategory.GENERATE
    form_class = QRCodeForm

    def handle(self, request, form):
        if not HAS_QRCODE:
            return {"error": "请安装 qrcode: pip install qrcode[pil]"}

        text = form.cleaned_data["text"]
        size = form.cleaned_data["size"]

        sizes = {
            "small": 200,
            "medium": 300,
            "large": 400,
        }

        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(text)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # 调整大小
            img = img.resize((sizes[size], sizes[size]))

            # 转换为base64
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            img_base64 = base64.b64encode(buffer.getvalue()).decode()

            return {
                "text": text,
                "image": f"data:image/png;base64,{img_base64}",
            }
        except Exception as e:
            return {"error": str(e)}
