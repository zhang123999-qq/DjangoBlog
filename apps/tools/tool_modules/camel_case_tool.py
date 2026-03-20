"""
驼峰命名转换工具
"""
from django import forms
from apps.tools.base_tool import BaseTool
import re


class CamelCaseForm(forms.Form):
    """驼峰命名转换表单"""
    text = forms.CharField(
        label='原始字符串',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '输入需要转换的字符串'}),
        required=True
    )
    conversion_type = forms.ChoiceField(
        label='转换类型',
        choices=[
            ('snake_to_camel', '下划线转小驼峰'),
            ('snake_to_pascal', '下划线转大驼峰'),
            ('camel_to_snake', '驼峰转下划线'),
        ],
        initial='snake_to_camel',
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class CamelCaseTool(BaseTool):
    """驼峰命名转换工具"""
    name = "驼峰命名转换"
    slug = "camel-case"
    description = "将下划线命名转换为驼峰命名，或反之"
    icon = "fa fa-exchange-alt"
    form_class = CamelCaseForm

    def handle(self, request, form):
        text = form.cleaned_data['text']
        conversion_type = form.cleaned_data['conversion_type']
        
        try:
            if conversion_type == 'snake_to_camel':
                # 下划线转小驼峰
                parts = text.split('_')
                result = parts[0] + ''.join(word.title() for word in parts[1:])
            elif conversion_type == 'snake_to_pascal':
                # 下划线转大驼峰
                parts = text.split('_')
                result = ''.join(word.title() for word in parts)
            elif conversion_type == 'camel_to_snake':
                # 驼峰转下划线
                result = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', text).lower()
            else:
                return {'error': '不支持的转换类型'}
            
            return {
                'original': text,
                'conversion_type': conversion_type,
                'result': result
            }
        except Exception as e:
            return {'error': str(e)}
