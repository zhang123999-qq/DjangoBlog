"""
文本加密/解密工具
"""
from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool


class TextCryptoForm(forms.Form):
    """文本加密/解密表单"""
    mode = forms.ChoiceField(
        label='操作',
        choices=[
            ('encrypt', '加密'),
            ('decrypt', '解密'),
        ],
        initial='encrypt',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    text = forms.CharField(
        label='文本内容',
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        required=True
    )
    key = forms.CharField(
        label='密钥',
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '输入加密密钥'}),
        required=True
    )


class TextCryptoTool(BaseTool):
    """文本加密/解密工具"""
    name = "文本加密/解密"
    slug = "text-crypto"
    description = "使用简单的加密算法对文本进行加密和解密"
    icon = "fa fa-lock"
    category = ToolCategory.ENCRYPT
    form_class = TextCryptoForm

    def handle(self, request, form):
        mode = form.cleaned_data['mode']
        text = form.cleaned_data['text']
        key = form.cleaned_data['key']
        
        try:
            if mode == 'encrypt':
                result = self.encrypt(text, key)
                return {'mode': 'encrypt', 'result': result}
            else:
                result = self.decrypt(text, key)
                return {'mode': 'decrypt', 'result': result}
        except Exception as e:
            return {'error': str(e)}

    def encrypt(self, text, key):
        """加密文本"""
        result = []
        key_len = len(key)
        for i, char in enumerate(text):
            key_char = key[i % key_len]
            encrypted_char = chr((ord(char) + ord(key_char)) % 256)
            result.append(encrypted_char)
        return ''.join(result)

    def decrypt(self, text, key):
        """解密文本"""
        result = []
        key_len = len(key)
        for i, char in enumerate(text):
            key_char = key[i % key_len]
            decrypted_char = chr((ord(char) - ord(key_char)) % 256)
            result.append(decrypted_char)
        return ''.join(result)
