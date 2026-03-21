from ..categories import ToolCategory
from django import forms
import base64
from ..base_tool import BaseTool


class Base64CodecForm(forms.Form):
    """Base64 编解码表单"""
    action = forms.ChoiceField(label='操作', choices=[
        ('encode', '编码'),
        ('decode', '解码'),
    ])
    text = forms.CharField(label='文本内容', widget=forms.Textarea(attrs={'rows': 5}), required=True)


class Base64CodecTool(BaseTool):
    """Base64 编解码工具"""
    name = "Base64 编解码"
    slug = "base64-codec"
    description = "对文本进行 Base64 编码或解码"
    icon = "code"
    category = ToolCategory.ENCRYPT
    form_class = Base64CodecForm

    def handle(self, request, form):
        """处理 Base64 编解码"""
        action = form.cleaned_data['action']
        text = form.cleaned_data['text']
        
        try:
            if action == 'encode':
                # 编码
                encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
                return {"result": encoded, "action": "encoded"}
            else:
                # 解码
                decoded = base64.b64decode(text).decode('utf-8')
                return {"result": decoded, "action": "decoded"}
        except Exception as e:
            return {"error": f"操作失败: {str(e)}"}
