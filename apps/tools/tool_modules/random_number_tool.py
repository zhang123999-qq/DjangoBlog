"""
随机数生成器工具
"""

import random

from django import forms

from ..categories import ToolCategory
from apps.tools.base_tool import BaseTool


class RandomNumberForm(forms.Form):
    """随机数生成器表单"""

    min_value = forms.FloatField(label="最小值", widget=forms.NumberInput(attrs={"class": "form-control"}))
    max_value = forms.FloatField(label="最大值", widget=forms.NumberInput(attrs={"class": "form-control"}))
    count = forms.IntegerField(
        label="数量", min_value=1, max_value=100, initial=1, widget=forms.NumberInput(attrs={"class": "form-control"})
    )
    number_type = forms.ChoiceField(
        label="类型",
        choices=[
            ("int", "整数"),
            ("float", "浮点数"),
        ],
        initial="int",
        widget=forms.Select(attrs={"class": "form-control"}),
    )


class RandomNumberTool(BaseTool):
    """随机数生成器工具"""

    name = "随机数生成器"
    slug = "random-number"
    description = "生成指定范围内的随机整数或浮点数，支持多个结果"
    icon = "fa fa-dice"
    category = ToolCategory.CALC
    form_class = RandomNumberForm

    def handle(self, request, form):
        min_value = form.cleaned_data["min_value"]
        max_value = form.cleaned_data["max_value"]
        count = form.cleaned_data["count"]
        number_type = form.cleaned_data["number_type"]

        try:
            if min_value > max_value:
                return {"error": "最小值不能大于最大值"}

            # 生成随机数
            results = []
            for _ in range(count):
                if number_type == "int":
                    # 转换为整数范围
                    min_int = int(min_value)
                    max_int = int(max_value)
                    # 确保max_int包含在内
                    results.append(random.randint(min_int, max_int))
                else:
                    results.append(random.uniform(min_value, max_value))

            return {
                "min_value": min_value,
                "max_value": max_value,
                "count": count,
                "number_type": number_type,
                "results": results,
            }
        except Exception as e:
            return {"error": str(e)}
