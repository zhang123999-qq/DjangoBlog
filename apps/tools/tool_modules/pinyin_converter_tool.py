"""
拼音转换工具
"""
from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool


class PinyinConverterForm(forms.Form):
    """拼音转换表单"""
    text = forms.CharField(
        label='输入中文',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': '请输入要转换的中文...'
        }),
        required=True
    )
    tone = forms.BooleanField(
        label='带声调',
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class PinyinConverterTool(BaseTool):
    """拼音转换工具"""
    name = "拼音转换"
    slug = "pinyin-converter"
    description = "将中文汉字转换为汉语拼音，支持带声调"
    icon = "fa fa-font"
    category = ToolCategory.ENCODE
    form_class = PinyinConverterForm

    # 拼音映射表（简化版）
    PINYIN_MAP = {
        '啊': 'a', '八': 'ba', '擦': 'ca', '大': 'da', '饿': 'e',
        '发': 'fa', '嘎': 'ga', '哈': 'ha', '击': 'ji', '咖': 'ka',
        '拉': 'la', '妈': 'ma', '那': 'na', '哦': 'o', '趴': 'pa',
        '七': 'qi', '然': 'ran', '撒': 'sa', '他': 'ta', '瓦': 'wa',
        '下': 'xia', '呀': 'ya', '在': 'zai', '的': 'de', '一': 'yi',
        '是': 'shi', '我': 'wo', '你': 'ni', '他': 'ta', '她': 'ta',
        '们': 'men', '好': 'hao', '再': 'zai', '见': 'jian',
        '爱': 'ai', '学': 'xue', '习': 'xi', '中': 'zhong', '国': 'guo',
        '人': 'ren', '民': 'min', '有': 'you', '梦': 'meng', '想': 'xiang',
    }

    # 带声调版本
    PINYIN_WITH_TONE = {
        '啊': 'ā', '八': 'bā', '擦': 'cā', '大': 'dà', '饿': 'è',
        '发': 'fā', '嘎': 'gā', '哈': 'hā', '击': 'jī', '咖': 'kā',
        '拉': 'lā', '妈': 'mā', '那': 'nà', '哦': 'ó', '趴': 'pā',
        '七': 'qī', '然': 'rán', '撒': 'sā', '他': 'tā', '瓦': 'wǎ',
        '下': 'xià', '呀': 'yā', '在': 'zài', '的': 'de', '一': 'yī',
        '是': 'shì', '我': 'wǒ', '你': 'nǐ', '她': 'tā',
        '们': 'men', '好': 'hǎo', '见': 'jiàn',
        '爱': 'ài', '学': 'xué', '习': 'xí', '中': 'zhōng', '国': 'guó',
        '人': 'rén', '民': 'mín', '有': 'yǒu', '梦': 'mèng', '想': 'xiǎng',
    }

    def handle(self, request, form):
        text = form.cleaned_data['text']
        use_tone = form.cleaned_data['tone']

        # 简单的拼音转换（基于映射表）
        pinyin_map = self.PINYIN_WITH_TONE if use_tone else self.PINYIN_MAP

        result = ''
        for char in text:
            if char.strip():  # 非空白字符
                result += pinyin_map.get(char, char) + ' '
            else:
                result += char

        return {
            'original': text,
            'pinyin': result.strip(),
            'with_tone': use_tone,
            'char_count': len([c for c in text if c.strip()]),
        }
