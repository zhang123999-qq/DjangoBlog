"""
凯撒密码加密解密工具
"""
from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool


class CaesarForm(forms.Form):
    """凯撒密码表单"""
    mode = forms.ChoiceField(
        label='操作',
        choices=[
            ('encrypt', '加密'),
            ('decrypt', '解密'),
        ],
        initial='encrypt',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    text = forms.CharField(
        label='文本内容',
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        required=True
    )
    shift = forms.IntegerField(
        label='位移量',
        min_value=-25,
        max_value=25,
        initial=3,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


class CaesarTool(BaseTool):
    """凯撒密码加密解密工具"""
    name = "凯撒密码"
    slug = "caesar"
    description = "对英文字母进行凯撒位移加密/解密"
    icon = "fa fa-exchange"
    category = ToolCategory.ENCRYPT
    form_class = CaesarForm

    def handle(self, request, form):
        mode = form.cleaned_data['mode']
        text = form.cleaned_data['text']
        shift = form.cleaned_data['shift']
        
        try:
            result = []
            for char in text:
                if char.isalpha():
                    # 确定字符的基础（大写或小写）
                    base = ord('A') if char.isupper() else ord('a')
                    # 计算位移后的字符
                    if mode == 'encrypt':
                        shifted = (ord(char) - base + shift) % 26
                    else:  # decrypt
                        shifted = (ord(char) - base - shift) % 26
                    result.append(chr(base + shifted))
                else:
                    # 非字母字符保持不变
                    result.append(char)
            
            return {
                'mode': '加密' if mode == 'encrypt' else '解密',
                'text': text,
                'shift': shift,
                'result': ''.join(result)
            }
        except Exception as e:
            return {'error': str(e)}
