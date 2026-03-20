"""
进制转换工具
"""
from django import forms
from apps.tools.base_tool import BaseTool


class BaseConverterForm(forms.Form):
    """进制转换表单"""
    number = forms.CharField(
        label='数值',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '输入要转换的数值'}),
        required=True
    )
    from_base = forms.ChoiceField(
        label='源进制',
        choices=[
            (2, '二进制'),
            (8, '八进制'),
            (10, '十进制'),
            (16, '十六进制'),
        ],
        initial=10,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class BaseConverterTool(BaseTool):
    """进制转换工具"""
    name = "进制转换"
    slug = "base-converter"
    description = "二进制、八进制、十进制、十六进制互转"
    icon = "fa fa-exchange-alt"
    form_class = BaseConverterForm

    def handle(self, request, form):
        number = form.cleaned_data['number'].strip()
        from_base = int(form.cleaned_data['from_base'])
        
        try:
            # 先转换为十进制
            decimal_value = int(number, from_base)
            
            # 转换为各种进制
            results = {
                'binary': bin(decimal_value)[2:],
                'octal': oct(decimal_value)[2:],
                'decimal': str(decimal_value),
                'hexadecimal': hex(decimal_value)[2:].upper(),
            }
            
            return {
                'input': number,
                'from_base': from_base,
                'decimal_value': decimal_value,
                'results': results,
            }
        except ValueError as e:
            return {'error': f'数值格式错误: {str(e)}'}
        except Exception as e:
            return {'error': str(e)}
