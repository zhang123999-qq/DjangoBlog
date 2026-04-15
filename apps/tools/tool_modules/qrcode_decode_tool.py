"""
二维码识别/解码工具
"""

from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool


class QRCodeDecodeForm(forms.Form):
    """二维码识别/解码表单"""

    file = forms.FileField(label="上传二维码图片", widget=forms.FileInput(attrs={"class": "form-control"}))


class QRCodeDecodeTool(BaseTool):
    """二维码识别/解码工具"""

    name = "二维码识别"
    slug = "qrcode-decode"
    description = "上传二维码图片，识别并解码其中的文本内容"
    icon = "fa fa-qrcode"
    category = ToolCategory.GENERATE
    form_class = QRCodeDecodeForm

    def handle(self, request, form):
        uploaded_file = form.cleaned_data["file"]

        try:
            from pyzbar import pyzbar
            from PIL import Image
        except ImportError:
            return {"error": "请安装 pyzbar 和 pillow: pip install pyzbar pillow"}

        try:
            # 打开图片
            image = Image.open(uploaded_file)

            # 识别二维码
            decoded_objects = pyzbar.decode(image)

            if not decoded_objects:
                return {"error": "未识别到二维码"}

            # 提取解码结果
            results = []
            for obj in decoded_objects:
                results.append({"type": obj.type, "data": obj.data.decode("utf-8")})

            return {"filename": uploaded_file.name, "results": results}
        except Exception as e:
            return {"error": str(e)}
