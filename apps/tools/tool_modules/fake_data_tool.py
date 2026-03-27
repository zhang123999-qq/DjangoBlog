"""
假数据生成器工具
"""
from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool


class FakeDataForm(forms.Form):
    """假数据生成器表单"""
    data_type = forms.ChoiceField(
        label='数据类型',
        choices=[
            ('name', '姓名'),
            ('address', '地址'),
            ('phone', '电话'),
            ('email', '邮箱'),
            ('company', '公司名'),
            ('id_card', '身份证号'),
            ('job', '职业'),
            ('city', '城市'),
        ],
        initial='name',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    count = forms.IntegerField(
        label='数量',
        min_value=1,
        max_value=100,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    locale = forms.ChoiceField(
        label='地区',
        choices=[
            ('zh_CN', '中文'),
            ('en_US', '英文'),
        ],
        initial='zh_CN',
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class FakeDataTool(BaseTool):
    """假数据生成器工具"""
    name = "假数据生成器"
    slug = "fake-data"
    description = "生成随机姓名、地址、电话、邮箱、公司名等假数据"
    icon = "fa fa-random"
    category = ToolCategory.GENERATE
    form_class = FakeDataForm

    def handle(self, request, form):
        data_type = form.cleaned_data['data_type']
        count = form.cleaned_data['count']
        locale = form.cleaned_data['locale']

        try:
            from faker import Faker
        except ImportError:
            return {'error': '请安装 faker: pip install faker'}

        try:
            # 创建Faker实例
            fake = Faker(locale)

            # 生成数据
            results = []
            for _ in range(count):
                if data_type == 'name':
                    if locale == 'zh_CN':
                        results.append(fake.name())
                    else:
                        results.append(fake.name())
                elif data_type == 'address':
                    if locale == 'zh_CN':
                        results.append(fake.address())
                    else:
                        results.append(fake.address())
                elif data_type == 'phone':
                    if locale == 'zh_CN':
                        results.append(fake.phone_number())
                    else:
                        results.append(fake.phone_number())
                elif data_type == 'email':
                    results.append(fake.email())
                elif data_type == 'company':
                    if locale == 'zh_CN':
                        results.append(fake.company())
                    else:
                        results.append(fake.company())
                elif data_type == 'id_card':
                    if locale == 'zh_CN':
                        results.append(fake.ssn())
                    else:
                        results.append(fake.ssn())
                elif data_type == 'job':
                    if locale == 'zh_CN':
                        results.append(fake.job())
                    else:
                        results.append(fake.job())
                elif data_type == 'city':
                    if locale == 'zh_CN':
                        results.append(fake.city())
                    else:
                        results.append(fake.city())

            return {
                'data_type': data_type,
                'count': count,
                'locale': locale,
                'results': results
            }
        except Exception as e:
            return {'error': str(e)}
