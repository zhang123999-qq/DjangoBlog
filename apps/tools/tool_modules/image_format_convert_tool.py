"""
图片格式转换工具（增强版）
支持 PNG/JPG/WEBP/GIF/BMP/TIFF 互转
"""
from ..categories import ToolCategory
from django import forms
from django.core.exceptions import ValidationError
from apps.tools.base_tool import BaseTool
from PIL import Image
import io
import base64


class ImageFormatConvertForm(forms.Form):
    """图片格式转换表单"""
    image = forms.ImageField(
        label='上传图片',
        widget=forms.FileInput(attrs={'class': 'form-control-file', 'accept': 'image/*'}),
        required=True
    )
    output_format = forms.ChoiceField(
        label='输出格式',
        choices=[
            ('PNG', 'PNG - 无损压缩，支持透明'),
            ('JPEG', 'JPEG - 有损压缩，适合照片'),
            ('WEBP', 'WebP - 现代格式，体积小'),
            ('GIF', 'GIF - 支持动画'),
            ('BMP', 'BMP - 无压缩位图'),
            ('TIFF', 'TIFF - 高质量，支持多页'),
        ],
        initial='PNG',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    quality = forms.IntegerField(
        label='压缩质量',
        min_value=1,
        max_value=100,
        initial=95,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text='仅对JPEG/WebP有效，1-100'
    )
    resize_option = forms.ChoiceField(
        label='尺寸调整',
        choices=[
            ('original', '保持原尺寸'),
            ('percent', '按比例缩放'),
            ('custom', '自定义尺寸'),
        ],
        initial='original',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    resize_percent = forms.IntegerField(
        label='缩放比例',
        min_value=10,
        max_value=200,
        initial=100,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '50表示缩小一半'}),
    )
    custom_width = forms.IntegerField(
        label='自定义宽度',
        min_value=10,
        max_value=8000,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '像素'}),
    )
    custom_height = forms.IntegerField(
        label='自定义高度',
        min_value=10,
        max_value=8000,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '像素'}),
    )
    maintain_aspect = forms.BooleanField(
        label='保持宽高比',
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='自定义尺寸时自动计算另一边'
    )

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # 限制文件大小（20MB）
            if image.size > 20 * 1024 * 1024:
                raise ValidationError('图片文件不能超过20MB')
        return image


class ImageFormatConvertTool(BaseTool):
    """图片格式转换工具"""
    name = "图片格式转换"
    slug = "image-format-convert"
    description = "PNG/JPG/WEBP/GIF/BMP/TIFF 互转，支持调整尺寸"
    icon = "fa fa-image"
    category = ToolCategory.IMAGE
    form_class = ImageFormatConvertForm

    def get_form(self, data=None, files=None):
        """获取表单实例，支持文件上传"""
        if self.form_class:
            return self.form_class(data, files)
        return None

    def handle(self, request, form):
        image_file = form.cleaned_data['image']
        output_format = form.cleaned_data['output_format']
        quality = form.cleaned_data.get('quality', 95)
        resize_option = form.cleaned_data['resize_option']
        resize_percent = form.cleaned_data.get('resize_percent')
        custom_width = form.cleaned_data.get('custom_width')
        custom_height = form.cleaned_data.get('custom_height')
        maintain_aspect = form.cleaned_data.get('maintain_aspect', True)
        
        try:
            # 读取图片
            img = Image.open(image_file)
            original_format = img.format or 'PNG'
            original_size = image_file.size
            original_width, original_height = img.size
            original_mode = img.mode
            
            # 处理尺寸调整
            new_width, new_height = original_width, original_height
            
            if resize_option == 'percent' and resize_percent:
                scale = resize_percent / 100
                new_width = int(original_width * scale)
                new_height = int(original_height * scale)
            elif resize_option == 'custom':
                if custom_width and custom_height and not maintain_aspect:
                    new_width = custom_width
                    new_height = custom_height
                elif custom_width:
                    new_width = custom_width
                    new_height = int(original_height * (custom_width / original_width))
                elif custom_height:
                    new_height = custom_height
                    new_width = int(original_width * (custom_height / original_height))
            
            # 调整尺寸
            if (new_width, new_height) != (original_width, original_height):
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 处理颜色模式转换
            if output_format == 'JPEG':
                # JPEG不支持透明通道
                if img.mode in ('RGBA', 'P'):
                    # 创建白色背景
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
            elif output_format == 'BMP':
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
            
            # 转换格式
            output = io.BytesIO()
            save_kwargs = {'format': output_format}
            
            if output_format == 'JPEG':
                save_kwargs['quality'] = quality
                save_kwargs['optimize'] = True
            elif output_format == 'WEBP':
                save_kwargs['quality'] = quality
            elif output_format == 'PNG':
                save_kwargs['optimize'] = True
            elif output_format == 'TIFF':
                save_kwargs['compression'] = 'tiff_lzw'
            
            img.save(output, **save_kwargs)
            converted_size = output.tell()
            output.seek(0)
            
            # 生成预览
            preview_img = img.copy()
            preview_img.thumbnail((400, 400), Image.Resampling.LANCZOS)
            preview = io.BytesIO()
            preview_format = 'PNG' if output_format in ('PNG', 'GIF', 'BMP', 'TIFF') else 'JPEG'
            preview_img.save(preview, format=preview_format, quality=85)
            preview_base64 = base64.b64encode(preview.getvalue()).decode()
            
            # 生成下载链接
            download_base64 = base64.b64encode(output.getvalue()).decode()
            
            return {
                'success': True,
                'original': {
                    'format': original_format,
                    'size': original_size,
                    'size_readable': self._format_size(original_size),
                    'width': original_width,
                    'height': original_height,
                    'mode': original_mode,
                },
                'converted': {
                    'format': output_format,
                    'size': converted_size,
                    'size_readable': self._format_size(converted_size),
                    'width': new_width,
                    'height': new_height,
                },
                'preview_base64': preview_base64,
                'preview_format': f'image/{preview_format.lower()}',
                'download_base64': download_base64,
                'download_format': f'image/{output_format.lower()}',
                'download_filename': f'converted.{output_format.lower()}',
                'compression_ratio': f'{(1 - converted_size / original_size) * 100:.1f}%' if original_size > 0 else '0%',
            }
            
        except Exception as e:
            return {'error': f'转换失败: {str(e)}'}
    
    def _format_size(self, bytes_size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024:
                return f'{bytes_size:.2f} {unit}'
            bytes_size /= 1024
        return f'{bytes_size:.2f} TB'
