"""
人民币大写转换工具
"""
from django import forms
from apps.tools.base_tool import BaseTool


class RMBUpperForm(forms.Form):
    """人民币大写转换表单"""
    amount = forms.DecimalField(
        label='金额',
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入金额，例如：1234.56'
        }),
        required=True
    )


class RMBUpperTool(BaseTool):
    """人民币大写转换工具"""
    name = "人民币大写"
    slug = "rmb-upper"
    description = "将数字金额转换为人民币大写（壹贰叁肆伍陆柒捌玖零）"
    icon = "fa fa-money-bill"
    form_class = RMBUpperForm

    def handle(self, request, form):
        amount = form.cleaned_data['amount']
        
        # 数字到大写映射
        digits = ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖']
        units = ['', '拾', '佰', '仟', '万', '拾', '佰', '仟', '亿']
        
        # 处理负数
        is_negative = amount < 0
        amount = abs(amount)
        
        # 转换为整数部分和小数部分
        integer_part = int(amount)
        decimal_part = round((amount - integer_part) * 100)
        
        # 转换整数部分
        if integer_part == 0:
            result = '零'
        else:
            result = ''
            num_str = str(integer_part)
            length = len(num_str)
            
            for i, digit in enumerate(num_str):
                digit_int = int(digit)
                position = length - i - 1
                
                if digit_int == 0:
                    if result and result[-1] != '零' and result[-1] != '万':
                        # 连续的零只保留一个
                        if position % 4 != 0:  # 不是万位
                            result += '零'
                else:
                    if result and result[-1] == '零' and result[-2:] != '零万':
                        result = result[:-1]  # 去掉末尾的零
                    result += digits[digit_int]
                    result += units[position % 4] if position < 8 else ''
                    
                    # 处理万、亿
                    if position == 4:
                        result += '万'
                    elif position == 8:
                        result += '亿'
            
            # 去除末尾的零
            result = result.rstrip('零')
            if result.endswith('万') and '亿' in result:
                result = result[:-1]
        
        # 处理小数部分
        if decimal_part == 0:
            result += '整'
        else:
            yuan = decimal_part // 10
            jiao = decimal_part % 10
            if yuan > 0:
                result += digits[yuan] + '角'
            if jiao > 0:
                result += digits[jiao] + '分'
            elif yuan == 0 and jiao == 0:
                result += '整'
        
        # 处理负数
        if is_negative:
            result = '负' + result
        
        return {
            'original': float(amount),
            'upper': result,
            'is_negative': is_negative,
            'integer_part': integer_part,
            'decimal_part': decimal_part,
        }
