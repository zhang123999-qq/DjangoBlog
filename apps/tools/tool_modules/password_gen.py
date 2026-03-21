from ..categories import ToolCategory
from django import forms
import random
import string
from ..base_tool import BaseTool


class PasswordGenForm(forms.Form):
    """密码生成表单"""
    length = forms.IntegerField(label='密码长度', min_value=6, max_value=100, initial=12)
    include_uppercase = forms.BooleanField(label='包含大写字母', initial=True, required=False)
    include_lowercase = forms.BooleanField(label='包含小写字母', initial=True, required=False)
    include_digits = forms.BooleanField(label='包含数字', initial=True, required=False)
    include_symbols = forms.BooleanField(label='包含特殊字符', initial=True, required=False)


class PasswordGenTool(BaseTool):
    """密码生成工具"""
    name = "密码生成"
    slug = "password-gen"
    description = "生成安全的随机密码"
    icon = "key"
    category = ToolCategory.GENERATE
    form_class = PasswordGenForm

    def handle(self, request, form):
        """处理密码生成"""
        length = form.cleaned_data['length']
        include_uppercase = form.cleaned_data['include_uppercase']
        include_lowercase = form.cleaned_data['include_lowercase']
        include_digits = form.cleaned_data['include_digits']
        include_symbols = form.cleaned_data['include_symbols']
        
        # 构建字符集
        char_set = ''
        if include_uppercase:
            char_set += string.ascii_uppercase
        if include_lowercase:
            char_set += string.ascii_lowercase
        if include_digits:
            char_set += string.digits
        if include_symbols:
            char_set += string.punctuation
        
        # 确保至少有一个字符集被选中
        if not char_set:
            return {"error": "至少需要选择一种字符类型"}
        
        # 生成密码
        password = ''.join(random.choice(char_set) for _ in range(length))
        
        return {"password": password}
