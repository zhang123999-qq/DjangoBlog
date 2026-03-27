"""
增强版 JSON 格式化工具（使用 Monaco Editor）
"""
from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool
import json


class JsonFormatterEnhancedForm(forms.Form):
    """JSON格式化表单"""
    json_content = forms.CharField(
        label='JSON内容',
        widget=forms.Textarea(attrs={
            'rows': 20,
            'class': 'form-control font-monospace',
            'data-editor': 'monaco',
            'data-language': 'json',
            'placeholder': '在此输入JSON内容...'
        }),
        required=True
    )
    indent = forms.ChoiceField(
        label='缩进',
        choices=[
            ('2', '2空格'),
            ('4', '4空格'),
            ('tab', 'Tab'),
        ],
        initial='2',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    sort_keys = forms.BooleanField(
        label='按键排序',
        initial=False,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class JsonFormatterEnhancedTool(BaseTool):
    """JSON格式化工具（增强版）"""
    name = "JSON 格式化（增强版）"
    slug = "json-formatter-enhanced"
    description = "使用Monaco编辑器的JSON格式化工具，支持语法高亮和错误提示"
    icon = "fa fa-code"
    category = ToolCategory.DATA
    form_class = JsonFormatterEnhancedForm
    template_name = "tools/json_formatter_enhanced.html"

    def handle(self, request, form):
        json_content = form.cleaned_data['json_content']
        indent = form.cleaned_data['indent']
        sort_keys = form.cleaned_data['sort_keys']

        try:
            # 解析JSON
            data = json.loads(json_content)

            # 格式化
            if indent == 'tab':
                indent_str = '\t'
            else:
                indent_str = int(indent)

            result = json.dumps(
                data,
                indent=indent_str,
                ensure_ascii=False,
                sort_keys=sort_keys
            )

            return {
                'success': True,
                'original': json_content,
                'result': result,
                'stats': {
                    'original_length': len(json_content),
                    'result_length': len(result),
                    'keys_count': self._count_keys(data),
                    'depth': self._get_depth(data),
                }
            }

        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f'JSON解析错误: {str(e)}',
                'line': e.lineno,
                'column': e.colno,
            }

    def _count_keys(self, data, count=0):
        """统计键数量"""
        if isinstance(data, dict):
            count += len(data)
            for value in data.values():
                count = self._count_keys(value, count)
        elif isinstance(data, list):
            for item in data:
                count = self._count_keys(item, count)
        return count

    def _get_depth(self, data, depth=0):
        """获取嵌套深度"""
        if isinstance(data, dict):
            if not data:
                return depth + 1
            return max(self._get_depth(v, depth + 1) for v in data.values())
        elif isinstance(data, list):
            if not data:
                return depth + 1
            return max(self._get_depth(item, depth + 1) for item in data)
        return depth
