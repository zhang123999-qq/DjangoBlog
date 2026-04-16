"""
图片压缩工具
"""

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from apps.core.validators import validate_image_extension, validate_file_size
from ..categories import ToolCategory
from apps.tools.base_tool import BaseTool
from PIL import Image
import io


class ImageCompressForm(forms.Form):
    """图片压缩表单"""

    image = forms.ImageField(
        label="上传图片",
        validators=[
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "gif", "bmp", "webp"]),
            validate_image_extension,
            lambda f: validate_file_size(f, max_size_mb=10),
        ],
        widget=forms.FileInput(attrs={"class": "form-control-file", "accept": "image/*"}),
        required=True,
    )
    quality = forms.IntegerField(
        label="压缩质量",
        min_value=1,
        max_value=100,
        initial=85,
        widget=forms.NumberInput(attrs={"class": "form-control", "type": "range"}),
        help_text="1-100，数值越小文件越小但质量越低",
    )
    output_format = forms.ChoiceField(
        label="输出格式",
        choices=[
            ("auto", "保持原格式"),
            ("jpeg", "JPEG"),
            ("png", "PNG"),
            ("webp", "WebP（推荐）"),
        ],
        initial="auto",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    max_width = forms.IntegerField(
        label="最大宽度",
        min_value=100,
        max_value=4000,
        initial=1920,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "留空则不限制"}),
        help_text="超过此宽度会等比缩放",
    )
    max_height = forms.IntegerField(
        label="最大高度",
        min_value=100,
        max_value=4000,
        initial=1080,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "留空则不限制"}),
        help_text="超过此高度会等比缩放",
    )

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if image:
            # 限制文件大小（10MB）
            if image.size > 10 * 1024 * 1024:
                raise ValidationError("图片文件不能超过10MB")
        return image


class ImageCompressTool(BaseTool):
    """图片压缩工具"""

    name = "图片压缩"
    slug = "image-compress"
    description = "上传图片后自动压缩，支持调整质量和尺寸"
    icon = "fa fa-compress-alt"
    category = ToolCategory.IMAGE
    form_class = ImageCompressForm

    def get_form(self, data=None, files=None):
        """获取表单实例，支持文件上传"""
        if self.form_class:
            return self.form_class(data, files)
        return None

    def handle(self, request, form):
        image_file = form.cleaned_data["image"]
        quality = form.cleaned_data["quality"]
        output_format = form.cleaned_data["output_format"]
        max_width = form.cleaned_data.get("max_width")
        max_height = form.cleaned_data.get("max_height")

        try:
            # 读取图片
            img = Image.open(image_file)
            original_size = image_file.size
            original_format = img.format or "PNG"

            # 转换RGBA为RGB（JPEG不支持透明通道）
            if output_format == "jpeg" and img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            elif output_format == "auto" and original_format == "JPEG" and img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # 缩放图片
            if max_width or max_height:
                max_width = max_width or img.width
                max_height = max_height or img.height
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            # 确定输出格式
            if output_format == "auto":
                if original_format == "JPEG":
                    fmt = "JPEG"
                elif original_format == "PNG":
                    fmt = "PNG"
                else:
                    fmt = "PNG"
            else:
                fmt = output_format.upper()
                if fmt == "WEBP":
                    fmt = "WEBP"

            # 压缩图片
            output = io.BytesIO()
            save_kwargs = {"format": fmt}

            if fmt in ("JPEG", "WEBP"):
                save_kwargs["quality"] = quality
                save_kwargs["optimize"] = True
            elif fmt == "PNG":
                save_kwargs["optimize"] = True

            img.save(output, **save_kwargs)
            compressed_size = output.tell()
            output.seek(0)

            # 计算压缩比
            compression_ratio = (1 - compressed_size / original_size) * 100

            # 生成预览（base64）
            preview = io.BytesIO()
            preview_img = img.copy()
            preview_img.thumbnail((400, 400), Image.Resampling.LANCZOS)
            preview_format = "PNG" if fmt == "PNG" or preview_img.mode == "RGBA" else "JPEG"
            preview_img.save(preview, format=preview_format, quality=85)
            import base64

            preview_base64 = base64.b64encode(preview.getvalue()).decode()

            return {
                "success": True,
                "original": {
                    "size": original_size,
                    "size_readable": self._format_size(original_size),
                    "format": original_format,
                    "width": img.width,
                    "height": img.height,
                },
                "compressed": {
                    "size": compressed_size,
                    "size_readable": self._format_size(compressed_size),
                    "format": fmt,
                    "width": img.width,
                    "height": img.height,
                },
                "compression_ratio": round(compression_ratio, 1),
                "saved_bytes": original_size - compressed_size,
                "preview_base64": preview_base64,
                "preview_format": f"image/{preview_format.lower()}",
            }

        except Exception as e:
            return {"error": f"压缩失败: {str(e)}"}

    def _format_size(self, bytes_size):
        """格式化文件大小"""
        for unit in ["B", "KB", "MB", "GB"]:
            if bytes_size < 1024:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.2f} TB"
