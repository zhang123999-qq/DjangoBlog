"""
文本去重工具
"""
from django import forms
from apps.tools.base_tool import BaseTool
import re


class TextDeduplicateForm(forms.Form):
    """文本去重表单"""
    mode = forms.ChoiceField(
        label='去重模式',
        choices=[
            ('lines', '按行去重'),
            ('words', '按词去重'),
            ('chars', '按字符去重'),
        ],
        initial='lines',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    text = forms.CharField(
        label='文本内容',
        widget=forms.Textarea(attrs={'rows': 15, 'class': 'form-control', 'placeholder': '输入需要去重的文本...'}),
        required=True
    )
    keep_order = forms.BooleanField(
        label='保持原有顺序',
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    case_sensitive = forms.BooleanField(
        label='区分大小写',
        initial=False,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    trim_whitespace = forms.BooleanField(
        label='去除首尾空白',
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    remove_empty = forms.BooleanField(
        label='删除空行/空项',
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class TextDeduplicateTool(BaseTool):
    """文本去重工具"""
    name = "文本去重"
    slug = "text-deduplicate"
    description = "去除重复行/重复词，支持多行文本"
    icon = "fa fa-filter"
    form_class = TextDeduplicateForm

    def handle(self, request, form):
        mode = form.cleaned_data['mode']
        text = form.cleaned_data['text']
        keep_order = form.cleaned_data['keep_order']
        case_sensitive = form.cleaned_data['case_sensitive']
        trim_whitespace = form.cleaned_data['trim_whitespace']
        remove_empty = form.cleaned_data['remove_empty']
        
        try:
            if mode == 'lines':
                result = self._deduplicate_lines(text, keep_order, case_sensitive, trim_whitespace, remove_empty)
            elif mode == 'words':
                result = self._deduplicate_words(text, keep_order, case_sensitive)
            else:  # chars
                result = self._deduplicate_chars(text, case_sensitive)
            
            return result
            
        except Exception as e:
            return {'error': f'处理失败: {str(e)}'}
    
    def _deduplicate_lines(self, text, keep_order, case_sensitive, trim_whitespace, remove_empty):
        """按行去重"""
        lines = text.split('\n')
        original_count = len(lines)
        
        # 预处理
        processed_lines = []
        for line in lines:
            if trim_whitespace:
                line = line.strip()
            processed_lines.append(line)
        
        # 删除空行
        if remove_empty:
            processed_lines = [line for line in processed_lines if line]
        
        # 去重
        if keep_order:
            seen = set()
            unique_lines = []
            for line in processed_lines:
                compare_key = line if case_sensitive else line.lower()
                if compare_key not in seen:
                    seen.add(compare_key)
                    unique_lines.append(line)
        else:
            if case_sensitive:
                unique_lines = list(dict.fromkeys(processed_lines))
            else:
                seen = set()
                unique_lines = []
                for line in processed_lines:
                    key = line.lower()
                    if key not in seen:
                        seen.add(key)
                        unique_lines.append(line)
        
        result_text = '\n'.join(unique_lines)
        unique_count = len(unique_lines)
        removed_count = original_count - unique_count
        
        return {
            'mode': 'lines',
            'result': result_text,
            'stats': {
                'original_count': original_count,
                'unique_count': unique_count,
                'removed_count': removed_count,
                'removal_rate': f'{(removed_count / original_count * 100):.1f}%' if original_count > 0 else '0%',
            }
        }
    
    def _deduplicate_words(self, text, keep_order, case_sensitive):
        """按词去重"""
        # 分词（支持中英文）
        words = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z]+|\d+|[^\s\u4e00-\u9fa5a-zA-Z0-9]+', text)
        original_count = len(words)
        
        if keep_order:
            seen = set()
            unique_words = []
            for word in words:
                compare_key = word if case_sensitive else word.lower()
                if compare_key not in seen:
                    seen.add(compare_key)
                    unique_words.append(word)
        else:
            if case_sensitive:
                unique_words = list(dict.fromkeys(words))
            else:
                seen = set()
                unique_words = []
                for word in words:
                    key = word.lower()
                    if key not in seen:
                        seen.add(key)
                        unique_words.append(word)
        
        result_text = ' '.join(unique_words)
        unique_count = len(unique_words)
        removed_count = original_count - unique_count
        
        return {
            'mode': 'words',
            'result': result_text,
            'stats': {
                'original_count': original_count,
                'unique_count': unique_count,
                'removed_count': removed_count,
                'removal_rate': f'{(removed_count / original_count * 100):.1f}%' if original_count > 0 else '0%',
            }
        }
    
    def _deduplicate_chars(self, text, case_sensitive):
        """按字符去重"""
        original_count = len(text)
        
        if case_sensitive:
            unique_chars = list(dict.fromkeys(text))
        else:
            seen = set()
            unique_chars = []
            for char in text:
                key = char.lower()
                if key not in seen:
                    seen.add(key)
                    unique_chars.append(char)
        
        result_text = ''.join(unique_chars)
        unique_count = len(unique_chars)
        removed_count = original_count - unique_count
        
        return {
            'mode': 'chars',
            'result': result_text,
            'stats': {
                'original_count': original_count,
                'unique_count': unique_count,
                'removed_count': removed_count,
                'removal_rate': f'{(removed_count / original_count * 100):.1f}%' if original_count > 0 else '0%',
            }
        }
