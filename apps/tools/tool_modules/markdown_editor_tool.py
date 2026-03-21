"""
Markdown编辑器工具
"""
from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool
import markdown
import bleach


class MarkdownEditorForm(forms.Form):
    """Markdown编辑器表单"""
    markdown_text = forms.CharField(
        label='Markdown内容',
        widget=forms.Textarea(attrs={'rows': 15, 'class': 'form-control font-monospace', 'placeholder': '在此输入Markdown内容...'}),
        required=True
    )
    output_format = forms.ChoiceField(
        label='输出格式',
        choices=[
            ('preview', '实时预览'),
            ('html', 'HTML代码'),
            ('both', '预览+HTML'),
        ],
        initial='preview',
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class MarkdownEditorTool(BaseTool):
    """Markdown编辑器工具"""
    name = "Markdown编辑器"
    slug = "markdown-editor"
    description = "实时预览Markdown，支持导出HTML"
    icon = "fa fa-file-alt"
    category = ToolCategory.DATA
    form_class = MarkdownEditorForm

    def handle(self, request, form):
        markdown_text = form.cleaned_data['markdown_text']
        output_format = form.cleaned_data['output_format']
        
        # 配置Markdown扩展
        extensions = [
            'extra',           # 支持表格、代码块等
            'toc',             # 目录支持
            'codehilite',      # 代码高亮
            'tables',          # 表格
            'fenced_code',     # 围栏代码块
        ]
        
        try:
            # 转换为HTML
            html_content = markdown.markdown(
                markdown_text,
                extensions=extensions,
                output_format='html5'
            )
            
            # 安全过滤（防止XSS）
            allowed_tags = [
                'p', 'br', 'strong', 'em', 'u', 's', 'del', 'ins',
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                'ul', 'ol', 'li',
                'blockquote', 'pre', 'code',
                'a', 'img',
                'table', 'thead', 'tbody', 'tr', 'th', 'td',
                'hr', 'div', 'span',
            ]
            allowed_attrs = {
                'a': ['href', 'title', 'target'],
                'img': ['src', 'alt', 'title', 'width', 'height'],
                'div': ['class'],
                'span': ['class'],
                'code': ['class'],
                'pre': ['class'],
            }
            
            html_content = bleach.clean(
                html_content,
                tags=allowed_tags,
                attributes=allowed_attrs,
                strip=False
            )
            
            # 统计信息
            lines = markdown_text.count('\n') + 1
            words = len(markdown_text.split())
            chars = len(markdown_text)
            
            result = {
                'markdown': markdown_text,
                'stats': {
                    'lines': lines,
                    'words': words,
                    'chars': chars,
                }
            }
            
            if output_format in ['preview', 'both']:
                result['preview'] = html_content
            
            if output_format in ['html', 'both']:
                result['html'] = html_content
            
            return result
            
        except Exception as e:
            return {'error': f'转换失败: {str(e)}'}
