"""
字符串转义/去转义工具
"""
from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool


class StringEscapeForm(forms.Form):
    """字符串转义/去转义表单"""
    mode = forms.ChoiceField(
        label='操作',
        choices=[
            ('escape', '转义'),
            ('unescape', '去转义'),
        ],
        initial='escape',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    text = forms.CharField(
        label='文本内容',
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        required=True
    )


class StringEscapeTool(BaseTool):
    """字符串转义/去转义工具"""
    name = "字符串转义"
    slug = "string-escape"
    description = "对字符串中的特殊字符进行转义，或恢复转义"
    icon = "fa fa-code"
    category = ToolCategory.ENCODE
    form_class = StringEscapeForm

    def handle(self, request, form):
        mode = form.cleaned_data['mode']
        text = form.cleaned_data['text']

        try:
            if mode == 'escape':
                # 转义特殊字符
                result = repr(text)[1:-1]  # 去掉引号
            else:
                # 去转义
                result = text.encode('utf-8').decode('unicode_escape')

            return {
                'mode': '转义' if mode == 'escape' else '去转义',
                'text': text,
                'result': result
            }
        except Exception as e:
            return {'error': str(e)}
