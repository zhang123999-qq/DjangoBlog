from django import forms
import json
from ..base_tool import BaseTool


class JSONFormatterForm(forms.Form):
    """JSON 格式化表单"""
    json_text = forms.CharField(label='JSON 文本', widget=forms.Textarea(attrs={'rows': 10}), required=True)


class JSONFormatterTool(BaseTool):
    """JSON 格式化工具"""
    name = "JSON 格式化"
    slug = "json-formatter"
    description = "格式化 JSON 文本，使其更易阅读"
    icon = "file-code"
    form_class = JSONFormatterForm

    def handle(self, request, form):
        """处理 JSON 格式化"""
        json_text = form.cleaned_data['json_text']
        
        try:
            # 解析 JSON
            data = json.loads(json_text)
            # 格式化 JSON
            formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
            return {"formatted_json": formatted_json}
        except json.JSONDecodeError as e:
            return {"error": f"JSON 解析失败: {str(e)}"}
        except Exception as e:
            return {"error": f"操作失败: {str(e)}"}
