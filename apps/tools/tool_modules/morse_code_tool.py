"""
摩斯密码编解码工具
"""
from django import forms
from apps.tools.base_tool import BaseTool


class MorseCodeForm(forms.Form):
    """摩斯密码表单"""
    mode = forms.ChoiceField(
        label='操作',
        choices=[
            ('encode', '文本 → 摩斯密码'),
            ('decode', '摩斯密码 → 文本'),
        ],
        initial='encode',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    text = forms.CharField(
        label='内容',
        widget=forms.Textarea(attrs={'rows': 6, 'class': 'form-control', 'placeholder': '输入文本或摩斯密码...'}),
        required=True
    )
    separator = forms.ChoiceField(
        label='分隔符',
        choices=[
            ('space', '空格'),
            ('slash', '斜杠 (/)'),
            ('pipe', '竖线 (|)'),
        ],
        initial='space',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='字母之间的分隔符'
    )


# 摩斯密码对照表
MORSE_CODE_DICT = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
    'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
    'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
    'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
    'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
    'Z': '--..',
    '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
    '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.',
    '.': '.-.-.-', ',': '--..--', '?': '..--..', "'": '.----.',
    '!': '-.-.--', '/': '-..-.', '(': '-.--.', ')': '-.--.-',
    '&': '.-...', ':': '---...', ';': '-.-.-.', '=': '-...-',
    '+': '.-.-.', '-': '-....-', '_': '..--.-', '"': '.-..-.',
    '$': '...-..-', '@': '.--.-.', ' ': '/',
}

# 反向映射
MORSE_CODE_REVERSE = {v: k for k, v in MORSE_CODE_DICT.items()}


class MorseCodeTool(BaseTool):
    """摩斯密码编解码工具"""
    name = "摩斯密码"
    slug = "morse-code"
    description = "文本与摩斯密码互转"
    icon = "fa fa-tty"
    form_class = MorseCodeForm

    def handle(self, request, form):
        mode = form.cleaned_data['mode']
        text = form.cleaned_data['text']
        separator = form.cleaned_data['separator']
        
        # 获取分隔符
        sep_map = {'space': ' ', 'slash': '/', 'pipe': '|'}
        sep = sep_map.get(separator, ' ')
        
        try:
            if mode == 'encode':
                result = self._encode(text, sep)
            else:
                result = self._decode(text, sep)
            
            return {
                'mode': '编码' if mode == 'encode' else '解码',
                'original': text,
                'result': result,
            }
            
        except Exception as e:
            return {'error': f'转换失败: {str(e)}'}
    
    def _encode(self, text, sep):
        """文本转摩斯密码"""
        result = []
        for char in text.upper():
            if char in MORSE_CODE_DICT:
                result.append(MORSE_CODE_DICT[char])
            else:
                # 未知字符用问号表示
                result.append('..--..')
        
        return sep.join(result)
    
    def _decode(self, text, sep):
        """摩斯密码转文本"""
        # 自动检测分隔符
        if '/' in text and ' ' in text:
            # 可能是单词分隔
            words = text.split(' / ')
            result_words = []
            for word in words:
                chars = word.split()
                word_result = []
                for code in chars:
                    word_result.append(MORSE_CODE_REVERSE.get(code, '?'))
                result_words.append(''.join(word_result))
            return ' '.join(result_words)
        
        # 尝试不同的分隔符
        for possible_sep in [' ', '/', '|', '\n']:
            if possible_sep in text:
                parts = text.split(possible_sep)
                break
        else:
            parts = [text]
        
        result = []
        for code in parts:
            code = code.strip()
            if code:
                if code == '/':
                    result.append(' ')
                else:
                    result.append(MORSE_CODE_REVERSE.get(code, '?'))
        
        return ''.join(result)
