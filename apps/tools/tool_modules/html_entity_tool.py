"""
HTML实体编码/解码工具
"""
from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool
import html


class HTMLEntityForm(forms.Form):
    """HTML实体编码/解码表单"""
    mode = forms.ChoiceField(
        label='操作',
        choices=[
            ('encode', '编码'),
            ('decode', '解码'),
        ],
        initial='encode',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    text = forms.CharField(
        label='文本内容',
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        required=True
    )


class HTMLEntityTool(BaseTool):
    """HTML实体编码/解码工具"""
    name = "HTML实体编解码"
    slug = "html-entity"
    description = "将HTML特殊字符转义为实体，或解码回原字符"
    icon = "fa fa-code"
    category = ToolCategory.ENCODE
    form_class = HTMLEntityForm

    def handle(self, request, form):
        mode = form.cleaned_data['mode']
        text = form.cleaned_data['text']
        
        try:
            if mode == 'encode':
                result = html.escape(text)
            else:
                result = html.unescape(text)
            
            return {
                'mode': '编码' if mode == 'encode' else '解码',
                'text': text,
                'result': result
            }
        except Exception as e:
            return {'error': str(e)}
