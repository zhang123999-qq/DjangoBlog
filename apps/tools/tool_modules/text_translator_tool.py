"""
文本翻译工具
"""
from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool
import requests


class TextTranslatorForm(forms.Form):
    """文本翻译表单"""
    text = forms.CharField(
        label='要翻译的文本',
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        required=True
    )
    source_lang = forms.ChoiceField(
        label='源语言',
        choices=[
            ('auto', '自动检测'),
            ('zh', '中文'),
            ('en', '英语'),
            ('ja', '日语'),
            ('ko', '韩语'),
            ('fr', '法语'),
            ('de', '德语'),
            ('es', '西班牙语'),
        ],
        initial='auto',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    target_lang = forms.ChoiceField(
        label='目标语言',
        choices=[
            ('zh', '中文'),
            ('en', '英语'),
            ('ja', '日语'),
            ('ko', '韩语'),
            ('fr', '法语'),
            ('de', '德语'),
            ('es', '西班牙语'),
        ],
        initial='en',
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class TextTranslatorTool(BaseTool):
    """文本翻译工具"""
    name = "文本翻译"
    slug = "text-translator"
    description = "将文本从一种语言翻译为另一种语言"
    icon = "fa fa-language"
    category = ToolCategory.TEXT
    form_class = TextTranslatorForm

    def handle(self, request, form):
        text = form.cleaned_data['text']
        source_lang = form.cleaned_data['source_lang']
        target_lang = form.cleaned_data['target_lang']

        try:
            # 使用Google Translate API进行翻译
            # 注意：这里使用了一个示例API密钥，实际使用时需要替换为真实的API密钥
            api_key = "YOUR_API_KEY"
            base_url = "https://translation.googleapis.com/language/translate/v2"
            params = {
                "key": api_key,
                "q": text,
                "source": source_lang if source_lang != "auto" else None,
                "target": target_lang,
                "format": "text"
            }

            # 过滤掉None值的参数
            params = {k: v for k, v in params.items() if v is not None}

            response = requests.post(base_url, json=params, timeout=10)
            data = response.json()

            if response.status_code == 200:
                translated_text = data.get("data", {}).get("translations", [{}])[0].get("translatedText")
                return {
                    "original_text": text,
                    "translated_text": translated_text,
                    "source_lang": source_lang,
                    "target_lang": target_lang
                }
            else:
                return {"error": f"翻译失败: {data.get('error', {}).get('message', '未知错误')}"}
        except Exception as e:
            return {"error": f"翻译失败: {str(e)}"}
