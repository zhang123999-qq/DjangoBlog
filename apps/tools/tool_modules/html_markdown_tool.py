"""
HTML/Markdown互转工具
"""
from django import forms
from apps.tools.base_tool import BaseTool
import markdown
import re
from html.parser import HTMLParser


class HTMLMarkdownForm(forms.Form):
    """HTML/Markdown互转表单"""
    mode = forms.ChoiceField(
        label='转换方向',
        choices=[
            ('html_to_markdown', 'HTML → Markdown'),
            ('markdown_to_html', 'Markdown → HTML'),
        ],
        initial='html_to_markdown',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    content = forms.CharField(
        label='内容',
        widget=forms.Textarea(attrs={'rows': 15, 'class': 'form-control font-monospace', 'placeholder': '粘贴HTML或Markdown内容...'}),
        required=True
    )


class HTMLToMarkdownConverter(HTMLParser):
    """HTML转Markdown转换器"""
    
    def __init__(self):
        super().__init__()
        self.result = []
        self.list_stack = []  # 栈用于跟踪列表类型
        self.ignore_tags = {'script', 'style', 'head', 'meta', 'link'}
        self.in_pre = False
        self.in_code = False
        
    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        
        if tag in self.ignore_tags:
            return
            
        attrs_dict = dict(attrs)
        
        if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            level = int(tag[1])
            self.result.append('\n' + '#' * level + ' ')
        elif tag == 'p':
            self.result.append('\n\n')
        elif tag == 'br':
            self.result.append('  \n')
        elif tag == 'hr':
            self.result.append('\n---\n')
        elif tag == 'strong' or tag == 'b':
            self.result.append('**')
        elif tag == 'em' or tag == 'i':
            self.result.append('*')
        elif tag == 'code':
            self.in_code = True
            if not self.in_pre:
                self.result.append('`')
        elif tag == 'pre':
            self.in_pre = True
            self.result.append('\n```\n')
        elif tag == 'blockquote':
            self.result.append('\n> ')
        elif tag == 'a':
            self.result.append('[')
        elif tag == 'img':
            src = attrs_dict.get('src', '')
            alt = attrs_dict.get('alt', '')
            self.result.append(f'![{alt}]({src})')
        elif tag == 'ul':
            self.list_stack.append('ul')
            self.result.append('\n')
        elif tag == 'ol':
            self.list_stack.append('ol')
            self.result.append('\n')
        elif tag == 'li':
            if self.list_stack:
                if self.list_stack[-1] == 'ul':
                    self.result.append('- ')
                else:
                    self.result.append('1. ')
        elif tag == 'table':
            self.result.append('\n')
            
    def handle_endtag(self, tag):
        tag = tag.lower()
        
        if tag in self.ignore_tags:
            return
            
        if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self.result.append('\n')
        elif tag == 'p':
            self.result.append('\n')
        elif tag in ('strong', 'b'):
            self.result.append('**')
        elif tag in ('em', 'i'):
            self.result.append('*')
        elif tag == 'code':
            self.in_code = False
            if not self.in_pre:
                self.result.append('`')
        elif tag == 'pre':
            self.in_pre = False
            self.result.append('\n```\n')
        elif tag == 'blockquote':
            self.result.append('\n')
        elif tag == 'a':
            self.result.append('](')
            # 注意：这里需要特殊处理href
        elif tag in ('ul', 'ol'):
            if self.list_stack:
                self.list_stack.pop()
        elif tag == 'li':
            self.result.append('\n')
            
    def handle_data(self, data):
        if not self.in_pre:
            data = data.strip()
            if data:
                self.result.append(data)
        else:
            self.result.append(data)
            
    def get_result(self):
        return ''.join(self.result).strip()


class HTMLMarkdownTool(BaseTool):
    """HTML/Markdown互转工具"""
    name = "HTML/Markdown互转"
    slug = "html-markdown"
    description = "HTML与Markdown格式相互转换"
    icon = "fa fa-exchange-alt"
    form_class = HTMLMarkdownForm

    def handle(self, request, form):
        mode = form.cleaned_data['mode']
        content = form.cleaned_data['content']
        
        try:
            if mode == 'markdown_to_html':
                result = self._markdown_to_html(content)
            else:
                result = self._html_to_markdown(content)
            
            return {
                'mode': 'HTML → Markdown' if mode == 'html_to_markdown' else 'Markdown → HTML',
                'original': content,
                'result': result,
                'original_length': len(content),
                'result_length': len(result),
            }
            
        except Exception as e:
            return {'error': f'转换失败: {str(e)}'}
    
    def _markdown_to_html(self, markdown_text):
        """Markdown转HTML"""
        extensions = ['extra', 'toc', 'codehilite', 'tables', 'fenced_code']
        return markdown.markdown(markdown_text, extensions=extensions, output_format='html5')
    
    def _html_to_markdown(self, html_content):
        """HTML转Markdown（简化实现）"""
        # 清理HTML
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # 标题
        for i in range(6, 0, -1):
            html_content = re.sub(
                rf'<h{i}[^>]*>(.*?)</h{i}>',
                rf'\n{"#" * i} \1\n',
                html_content,
                flags=re.DOTALL | re.IGNORECASE
            )
        
        # 段落
        html_content = re.sub(r'<p[^>]*>(.*?)</p>', r'\n\1\n', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # 换行
        html_content = re.sub(r'<br\s*/?>', '  \n', html_content, flags=re.IGNORECASE)
        
        # 粗体和斜体
        html_content = re.sub(r'<(strong|b)[^>]*>(.*?)</\1>', r'**\2**', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<(em|i)[^>]*>(.*?)</\1>', r'*\2*', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # 链接
        html_content = re.sub(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', r'[\2](\1)', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # 图片
        html_content = re.sub(r'<img[^>]*src=["\']([^"\']*)["\'][^>]*alt=["\']([^"\']*)["\'][^>]*/?>', r'![\2](\1)', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'<img[^>]*alt=["\']([^"\']*)["\'][^>]*src=["\']([^"\']*)["\'][^>]*/?>', r'![\1](\2)', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'<img[^>]*src=["\']([^"\']*)["\'][^>]*/?>', r'![](\1)', html_content, flags=re.IGNORECASE)
        
        # 代码块
        html_content = re.sub(r'<pre[^>]*><code[^>]*>(.*?)</code></pre>', r'\n```\n\1\n```\n', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # 列表
        html_content = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'</?[ou]l[^>]*>', '\n', html_content, flags=re.IGNORECASE)
        
        # 引用
        html_content = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>', r'\n> \1\n', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # 分割线
        html_content = re.sub(r'<hr\s*/?>', '\n---\n', html_content, flags=re.IGNORECASE)
        
        # 清理剩余标签
        html_content = re.sub(r'<[^>]+>', '', html_content)
        
        # 清理HTML实体
        import html
        html_content = html.unescape(html_content)
        
        # 清理多余空白
        html_content = re.sub(r'\n{3,}', '\n\n', html_content)
        html_content = html_content.strip()
        
        return html_content
