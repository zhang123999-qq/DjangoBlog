"""
URL缩短工具
"""
from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool
import hashlib


class URLShortenerForm(forms.Form):
    """URL缩短表单"""
    url = forms.URLField(
        label='原始URL',
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': '输入要缩短的URL'}),
        required=True
    )
    custom_code = forms.CharField(
        label='自定义代码（可选）',
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '可选的自定义短代码'}),
        required=False
    )


class URLShortenerTool(BaseTool):
    """URL缩短工具"""
    name = "URL缩短"
    slug = "url-shortener"
    description = "将长URL缩短为短链接"
    icon = "fa fa-link"
    category = ToolCategory.NETWORK
    form_class = URLShortenerForm

    def handle(self, request, form):
        url = form.cleaned_data['url']
        custom_code = form.cleaned_data['custom_code']
        
        try:
            if custom_code:
                short_code = custom_code
            else:
                # 生成短代码
                short_code = self.generate_short_code(url)
            
            # 构建短链接
            base_url = request.build_absolute_uri('/')
            short_url = f"{base_url}s/{short_code}"
            
            return {
                'original_url': url,
                'short_code': short_code,
                'short_url': short_url
            }
        except Exception as e:
            return {'error': str(e)}

    def generate_short_code(self, url):
        """生成短代码"""
        # 使用MD5哈希生成短代码
        hash_obj = hashlib.md5(url.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()
        # 取前8位作为短代码
        short_code = hash_hex[:8]
        return short_code
