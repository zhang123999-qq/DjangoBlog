"""
Unicode 编码解码工具
"""
from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool


class UnicodeForm(forms.Form):
    """Unicode编码表单"""
    mode = forms.ChoiceField(
        label='操作',
        choices=[
            ('encode', '编码（中文→Unicode）'),
            ('decode', '解码（Unicode→中文）'),
        ],
        initial='encode',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    text = forms.CharField(
        label='文本内容',
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        required=True
    )


class UnicodeTool(BaseTool):
    """Unicode编码解码工具"""
    name = "Unicode编码"
    slug = "unicode"
    description = "Unicode编码和解码工具"
    icon = "fa fa-font"
    category = ToolCategory.ENCODE
    form_class = UnicodeForm

    def handle(self, request, form):
        mode = form.cleaned_data['mode']
        text = form.cleaned_data['text']
        
        try:
            if mode == 'encode':
                # 中文转Unicode
                result = text.encode('unicode-escape').decode('utf-8')
            else:
                # Unicode转中文
                result = text.encode('utf-8').decode('unicode-escape')
            
            return {
                'mode': mode,
                'original': text,
                'result': result,
            }
        except Exception as e:
            return {'error': str(e)}
