"""
图片元数据查看器（EXIF）工具
"""

from django import forms
from django.core.validators import FileExtensionValidator
from apps.core.validators import validate_image_extension, validate_file_size
from ..categories import ToolCategory
from apps.tools.base_tool import BaseTool


class EXIFForm(forms.Form):
    """图片元数据查看器表单"""

    file = forms.FileField(
        label="上传图片",
        validators=[
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "gif", "bmp", "webp"]),
            validate_image_extension,
            lambda f: validate_file_size(f, max_size_mb=10),
        ],
        widget=forms.FileInput(attrs={"class": "form-control"}),
    )


class EXIFTool(BaseTool):
    """图片元数据查看器（EXIF）工具"""

    name = "图片元数据查看"
    slug = "exif"
    description = "上传图片，提取并显示其EXIF元数据（如拍摄时间、相机型号、GPS坐标）"
    icon = "fa fa-image"
    category = ToolCategory.IMAGE
    form_class = EXIFForm

    def handle(self, request, form):
        uploaded_file = form.cleaned_data["file"]

        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
        except ImportError:
            return {"error": "请安装 pillow: pip install pillow"}

        try:
            # 打开图片
            image = Image.open(uploaded_file)

            # 提取EXIF数据
            exif_data = {}
            if hasattr(image, "_getexif"):
                exif = image._getexif()
                if exif:
                    for tag, value in exif.items():
                        tag_name = TAGS.get(tag, tag)
                        exif_data[tag_name] = value

            # 如果没有EXIF数据
            if not exif_data:
                return {"filename": uploaded_file.name, "message": "未找到EXIF元数据"}

            return {"filename": uploaded_file.name, "exif_data": exif_data}
        except Exception as e:
            return {"error": str(e)}
