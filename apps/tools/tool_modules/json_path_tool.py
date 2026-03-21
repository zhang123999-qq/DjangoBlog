"""
JSON Path测试工具
"""
from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool
import json


class JSONPathForm(forms.Form):
    """JSON Path测试表单"""
    json_data = forms.CharField(
        label='JSON数据',
        widget=forms.Textarea(attrs={'rows': 8, 'class': 'form-control'}),
        required=True
    )
    json_path = forms.CharField(
        label='JSON Path表达式',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '$.store.book[*].title'}),
        required=True
    )


class JSONPathTool(BaseTool):
    """JSON Path测试工具"""
    name = "JSON Path测试"
    slug = "json-path"
    description = "根据JSON Path表达式提取JSON数据中的值"
    icon = "fa fa-search"
    category = ToolCategory.DATA
    form_class = JSONPathForm

    def handle(self, request, form):
        json_data = form.cleaned_data['json_data']
        json_path = form.cleaned_data['json_path']
        
        try:
            from jsonpath_ng import parse
        except ImportError:
            return {'error': '请安装 jsonpath-ng: pip install jsonpath-ng'}
        
        try:
            # 解析JSON数据
            data = json.loads(json_data)
            
            # 解析JSON Path表达式
            jsonpath_expr = parse(json_path)
            
            # 提取匹配结果
            matches = jsonpath_expr.find(data)
            results = [match.value for match in matches]
            
            return {
                'json_path': json_path,
                'results': results
            }
        except json.JSONDecodeError as e:
            return {'error': f'JSON解析错误: {str(e)}'}
        except Exception as e:
            return {'error': str(e)}
