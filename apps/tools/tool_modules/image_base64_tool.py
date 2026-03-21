"""
Image to Base64 Converter Tool
Convert image to Base64 string and vice versa
"""
from ..categories import ToolCategory
from django import forms
from django.core.exceptions import ValidationError
import base64
import struct
from apps.tools.base_tool import BaseTool


def detect_image_type(data):
    """检测图片类型（替代 imghdr）"""
    # PNG
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return 'png'
    # JPEG
    if data[:2] == b'\xff\xd8':
        return 'jpeg'
    # GIF
    if data[:6] in (b'GIF87a', b'GIF89a'):
        return 'gif'
    # BMP
    if data[:2] == b'BM':
        return 'bmp'
    # WebP
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return 'webp'
    # ICO
    if data[:4] == b'\x00\x00\x01\x00':
        return 'ico'
    return 'jpeg'  # 默认


class ImageBase64Form(forms.Form):
    MODE_CHOICES = [
        ('image_to_base64', 'Image to Base64'),
        ('base64_to_image', 'Base64 to Image'),
    ]
    
    mode = forms.ChoiceField(
        choices=MODE_CHOICES,
        initial='image_to_base64',
        label='Mode'
    )
    image_file = forms.ImageField(
        required=False,
        label='Image File',
        help_text='Upload image (max 2MB)'
    )
    base64_input = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
        required=False,
        label='Base64 String',
        help_text='Paste base64 string (with or without data URI prefix)'
    )
    output_format = forms.ChoiceField(
        choices=[
            ('data_uri', 'Data URI (for HTML/CSS)'),
            ('raw', 'Raw Base64'),
        ],
        initial='data_uri',
        label='Output Format'
    )


def image_to_base64(image_file, output_format='data_uri'):
    """Convert uploaded image to base64"""
    try:
        # Read image data
        image_data = image_file.read()
        
        # Detect image type
        image_type = detect_image_type(image_data)
        
        # Encode to base64
        base64_str = base64.b64encode(image_data).decode('utf-8')
        
        if output_format == 'data_uri':
            result = f'data:image/{image_type};base64,{base64_str}'
        else:
            result = base64_str
        
        return {
            'base64': result,
            'image_type': image_type,
            'size': len(image_data),
            'size_readable': format_size(len(image_data)),
            'data_uri_preview': f'data:image/{image_type};base64,{base64_str[:100]}...',
        }
    except Exception as e:
        return {'error': str(e)}


def base64_to_image(base64_str):
    """Convert base64 string to image data"""
    try:
        # Remove data URI prefix if present
        if base64_str.startswith('data:'):
            # Extract mime type and data
            parts = base64_str.split(',', 1)
            if len(parts) == 2:
                header = parts[0]
                base64_str = parts[1]
                
                # Extract image type from header
                if 'image/' in header:
                    image_type = header.split('image/')[1].split(';')[0]
                else:
                    image_type = 'png'
            else:
                image_type = 'png'
        else:
            image_type = 'png'
        
        # Decode base64
        image_data = base64.b64decode(base64_str)
        
        return {
            'image_data': image_data,
            'image_type': image_type,
            'size': len(image_data),
            'size_readable': format_size(len(image_data)),
            'data_uri': f'data:image/{image_type};base64,{base64_str[:100]}...',
        }
    except Exception as e:
        return {'error': str(e)}


def format_size(bytes_size):
    """Format bytes to human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f'{bytes_size:.2f} {unit}'
        bytes_size /= 1024
    return f'{bytes_size:.2f} TB'


def process(form):
    """Process the form and return result"""
    if not form.is_valid():
        return {'error': 'Invalid input'}
    
    cleaned = form.cleaned_data
    mode = cleaned.get('mode', 'image_to_base64')
    output_format = cleaned.get('output_format', 'data_uri')
    
    if mode == 'image_to_base64':
        image_file = cleaned.get('image_file')
        if not image_file:
            return {'error': 'Please upload an image file'}
        
        # Check file size (2MB limit)
        if image_file.size > 2 * 1024 * 1024:
            return {'error': 'Image file too large (max 2MB)'}
        
        result = image_to_base64(image_file, output_format)
        result['mode'] = 'image_to_base64'
        return result
        
    elif mode == 'base64_to_image':
        base64_input = cleaned.get('base64_input', '').strip()
        if not base64_input:
            return {'error': 'Please enter a base64 string'}
        
        result = base64_to_image(base64_input)
        result['mode'] = 'base64_to_image'
        return result
    
    return {'error': 'Invalid mode'}


# Tool class for registry


class ImageBase64Tool(BaseTool):
    name = "图片Base64"
    slug = "image-base64"
    description = "图片与Base64字符串互转"
    icon = "image"
    category = ToolCategory.IMAGE
    form_class = ImageBase64Form

    def get_form(self, data=None, files=None):
        """Get form instance with file support"""
        if self.form_class:
            return self.form_class(data, files)
        return None

    def handle(self, request, form):
        return process(form)
