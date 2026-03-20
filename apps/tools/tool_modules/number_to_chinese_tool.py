"""
数字转中文大写工具
"""
from django import forms
from apps.tools.base_tool import BaseTool


class NumberToChineseForm(forms.Form):
    """数字转中文表单"""
    number = forms.DecimalField(
        label='输入数字',
        max_digits=20,
        decimal_places=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入整数，例如：1234567890'
        }),
        required=True
    )


class NumberToChineseTool(BaseTool):
    """数字转中文大写工具"""
    name = "数字转中文"
    slug = "number-to-chinese"
    description = "将阿拉伯数字转换为中文数字（零一二三四五六七八九）"
    icon = "fa fa-sort-numeric-up"
    form_class = NumberToChineseForm

    NUMBERS = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九']
    UNITS = ['', '十', '百', '千', '万']
    
    def number_to_chinese(self, num):
        """将数字转换为中文"""
        if num == 0:
            return '零'
        
        result = ''
        num_str = str(int(num))
        length = len(num_str)
        
        for i, digit in enumerate(num_str):
            digit_int = int(digit)
            position = length - i - 1
            
            if digit_int == 0:
                if result and result[-1] != '零':
                    result += '零'
            else:
                if result and result[-1] == '零' and position > 3:
                    result = result[:-1]  # 去掉零
                    
                if position == 1 and digit_int == 1 and length == 2:
                    # 十前面的一不读
                    result += self.UNITS[position]
                else:
                    result += self.NUMBERS[digit_int]
                    result += self.UNITS[position]
        
        result = result.rstrip('零')
        if result.startswith('十'):
            result = result[1:]  # 开头的一不读
        
        return result

    def handle(self, request, form):
        number = form.cleaned_data['number']
        
        chinese = self.number_to_chinese(number)
        
        # 也提供金额读法
        amount_read = chinese + '元'
        
        return {
            'number': int(number),
            'chinese': chinese,
            'amount_read': amount_read,
            'digits': len(str(int(number))),
        }
