"""
身份证号码生成/校验工具
"""
from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool
import random
import re


class IDCardForm(forms.Form):
    """身份证号码生成/校验表单"""
    mode = forms.ChoiceField(
        label='操作',
        choices=[
            ('generate', '生成'),
            ('validate', '校验'),
        ],
        initial='generate',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    id_card = forms.CharField(
        label='身份证号码',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False
    )
    region = forms.CharField(
        label='地区代码（生成时使用）',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例如：110101'}),
        required=False
    )
    birth_date = forms.CharField(
        label='出生日期（生成时使用）',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例如：1990-01-01'}),
        required=False
    )


class IDCardTool(BaseTool):
    """身份证号码生成/校验工具"""
    name = "身份证号码生成/校验"
    slug = "id-card"
    description = "根据规则生成虚拟身份证号码，或校验输入的身份证号码是否合法"
    icon = "fa fa-id-card"
    category = ToolCategory.SECURITY
    form_class = IDCardForm

    def handle(self, request, form):
        mode = form.cleaned_data['mode']
        id_card = form.cleaned_data['id_card']
        region = form.cleaned_data['region']
        birth_date = form.cleaned_data['birth_date']

        try:
            if mode == 'generate':
                # 生成身份证号码
                # 1. 地区代码
                if not region:
                    # 使用随机地区代码
                    regions = ['110101', '310101', '440101', '440301', '330101', '510101', '500101']
                    region = random.choice(regions)

                # 2. 出生日期
                if not birth_date:
                    # 生成随机出生日期
                    import datetime
                    start_date = datetime.date(1970, 1, 1)
                    end_date = datetime.date(2000, 12, 31)
                    days_between = (end_date - start_date).days
                    random_days = random.randint(0, days_between)
                    birth_date = start_date + datetime.timedelta(days=random_days)
                    birth_date_str = birth_date.strftime('%Y%m%d')
                else:
                    # 格式化输入的出生日期
                    birth_date_str = birth_date.replace('-', '')

                # 3. 顺序码
                sequence = str(random.randint(1, 999)).zfill(3)

                # 4. 校验码
                temp_id = region + birth_date_str + sequence
                check_code = self._calculate_check_code(temp_id)

                # 组合身份证号码
                result = temp_id + check_code

                return {
                    'mode': '生成',
                    'result': result
                }
            else:
                # 校验身份证号码
                if not id_card:
                    return {'error': '请输入身份证号码'}

                # 1. 长度校验
                if len(id_card) != 18:
                    return {'error': '身份证号码长度错误'}

                # 2. 格式校验
                if not re.match(r'^[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[0-9Xx]$', id_card):
                    return {'error': '身份证号码格式错误'}

                # 3. 校验码校验
                temp_id = id_card[:17]
                check_code = self._calculate_check_code(temp_id)
                if check_code != id_card[17].upper():
                    return {'error': '身份证号码校验码错误'}

                return {
                    'mode': '校验',
                    'result': '身份证号码合法',
                    'id_card': id_card
                }
        except Exception as e:
            return {'error': str(e)}

    def _calculate_check_code(self, temp_id):
        """计算校验码"""
        # 权重
        weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        # 校验码对应值
        check_codes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']

        # 计算总和
        total = sum(int(temp_id[i]) * weights[i] for i in range(17))
        # 计算校验码
        check_code_index = total % 11
        return check_codes[check_code_index]
