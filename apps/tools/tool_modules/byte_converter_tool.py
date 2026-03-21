"""
字节转换工具
"""
from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool


class ByteConverterForm(forms.Form):
    """字节转换表单"""
    value = forms.DecimalField(
        label='输入数值',
        max_digits=20,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '例如：1024'
        }),
        required=True
    )
    unit = forms.ChoiceField(
        label='当前单位',
        choices=[
            ('B', '字节 (B)'),
            ('KB', '千字节 (KB)'),
            ('MB', '兆字节 (MB)'),
            ('GB', '吉字节 (GB)'),
            ('TB', '太字节 (TB)'),
        ],
        initial='KB',
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class ByteConverterTool(BaseTool):
    """字节转换工具"""
    name = "字节转换"
    slug = "byte-converter"
    description = "字节(B)、KB、MB、GB、TB等单位相互转换"
    icon = "fa fa-database"
    category = ToolCategory.CALC
    form_class = ByteConverterForm

    def handle(self, request, form):
        value = float(form.cleaned_data['value'])
        unit = form.cleaned_data['unit']
        
        # 转换为字节
        units = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 ** 2,
            'GB': 1024 ** 3,
            'TB': 1024 ** 4,
        }
        
        bytes_value = value * units[unit]
        
        # 转换为各单位的值
        result = {
            'original': {
                'value': value,
                'unit': unit,
            },
            'B': round(bytes_value, 2),
            'KB': round(bytes_value / 1024, 4),
            'MB': round(bytes_value / (1024 ** 2), 4),
            'GB': round(bytes_value / (1024 ** 3), 6),
            'TB': round(bytes_value / (1024 ** 4), 8),
        }
        
        # 智能推荐显示
        if bytes_value < 1024:
            display = f"{result['B']} B"
        elif bytes_value < 1024 ** 2:
            display = f"{result['KB']} KB"
        elif bytes_value < 1024 ** 3:
            display = f"{result['MB']} MB"
        elif bytes_value < 1024 ** 4:
            display = f"{result['GB']} GB"
        else:
            display = f"{result['TB']} TB"
        
        result['smart_display'] = display
        
        return result
