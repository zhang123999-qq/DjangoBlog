"""
BMI计算器工具
"""

from django import forms
from apps.tools.base_tool import BaseTool


class BMICalculatorForm(forms.Form):
    """BMI计算器表单"""

    height = forms.DecimalField(
        label="身高（厘米）",
        max_digits=5,
        decimal_places=1,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "例如：175"}),
        required=True,
    )
    weight = forms.DecimalField(
        label="体重（公斤）",
        max_digits=5,
        decimal_places=1,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "例如：70"}),
        required=True,
    )


class BMICalculatorTool(BaseTool):
    """BMI计算器工具"""

    name = "BMI计算器"
    slug = "bmi-calculator"
    description = "计算身体质量指数(BMI)，评估体重是否健康"
    icon = "fa fa-heartbeat"
    form_class = BMICalculatorForm

    def handle(self, request, form):
        height = float(form.cleaned_data["height"])  # cm
        weight = float(form.cleaned_data["weight"])  # kg

        # BMI计算
        height_m = height / 100
        bmi = weight / (height_m * height_m)
        bmi = round(bmi, 1)

        # 评估BMI
        if bmi < 18.5:
            category = "偏瘦"
            color = "#FFC107"
            advice = "建议适当增加营养摄入，多运动增肌"
        elif bmi < 24:
            category = "正常"
            color = "#28A745"
            advice = "继续保持健康的生活方式！"
        elif bmi < 28:
            category = "偏胖"
            color = "#FD7E14"
            advice = "建议控制饮食，适当增加运动"
        elif bmi < 30:
            category = "肥胖"
            color = "#DC3545"
            advice = "建议开始减肥计划，注意健康"
        else:
            category = "重度肥胖"
            color = "#DC3545"
            advice = "建议咨询医生，制定科学的减肥方案"

        # 标准体重范围
        normal_min = 18.5 * height_m * height_m
        normal_max = 24 * height_m * height_m

        return {
            "height": height,
            "weight": weight,
            "bmi": bmi,
            "category": category,
            "color": color,
            "advice": advice,
            "normal_min": round(normal_min, 1),
            "normal_max": round(normal_max, 1),
        }
