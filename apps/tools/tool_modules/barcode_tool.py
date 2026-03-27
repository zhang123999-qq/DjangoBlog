"""
条形码生成工具
"""
from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool
import base64
from io import BytesIO


class BarcodeForm(forms.Form):
    """条形码生成表单"""
    text = forms.CharField(
        label='文本内容',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '输入要生成条形码的文本'}),
        required=True
    )
    barcode_type = forms.ChoiceField(
        label='条形码类型',
        choices=[
            ('code128', 'Code128'),
            ('ean13', 'EAN-13'),
            ('ean8', 'EAN-8'),
            ('upc', 'UPC-A'),
        ],
        initial='code128',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    width = forms.IntegerField(
        label='宽度',
        min_value=100,
        max_value=1000,
        initial=300,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    height = forms.IntegerField(
        label='高度',
        min_value=20,
        max_value=200,
        initial=50,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


class BarcodeTool(BaseTool):
    """条形码生成工具"""
    name = "条形码生成"
    slug = "barcode"
    description = "根据输入的文本生成条形码图片（如Code128、EAN-13）"
    icon = "fa fa-barcode"
    category = ToolCategory.GENERATE
    form_class = BarcodeForm

    def handle(self, request, form):
        text = form.cleaned_data['text']
        barcode_type = form.cleaned_data['barcode_type']
        height = form.cleaned_data['height']

        try:
            import barcode
            from barcode.writer import ImageWriter
        except ImportError:
            return {'error': '请安装 python-barcode: pip install python-barcode pillow'}

        try:
            # 获取条形码类
            barcode_class = None
            if barcode_type == 'code128':
                barcode_class = barcode.get_barcode_class('code128')
            elif barcode_type == 'ean13':
                # EAN-13需要12位数字
                if len(text) != 12 or not text.isdigit():
                    return {'error': 'EAN-13需要12位数字'}
                barcode_class = barcode.get_barcode_class('ean13')
            elif barcode_type == 'ean8':
                # EAN-8需要7位数字
                if len(text) != 7 or not text.isdigit():
                    return {'error': 'EAN-8需要7位数字'}
                barcode_class = barcode.get_barcode_class('ean8')
            elif barcode_type == 'upc':
                # UPC-A需要11位数字
                if len(text) != 11 or not text.isdigit():
                    return {'error': 'UPC-A需要11位数字'}
                barcode_class = barcode.get_barcode_class('upca')

            if not barcode_class:
                return {'error': '不支持的条形码类型'}

            # 创建条形码
            barcode_instance = barcode_class(text, writer=ImageWriter())

            # 生成图片 - 优化比例，高度为宽度的1/4左右
            buffer = BytesIO()
            # module_height 控制条的高度，使用较小的值避免图片过高
            # quiet_zone 是两侧的空白边距
            module_height = max(10, min(height // 5, 30))  # 限制模块高度
            barcode_instance.write(buffer, options={
                'module_width': 0.3,  # 条码线宽度
                'module_height': module_height,  # 条码线高度
                'quiet_zone': 6,  # 边距
                'font_size': 10,  # 文字大小
                'text_distance': 3,  # 文字与条码的距离
            })
            buffer.seek(0)

            # 转换为Base64
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            buffer.close()

            return {
                'text': text,
                'barcode_type': barcode_type,
                'image_base64': image_base64
            }
        except Exception as e:
            return {'error': str(e)}
