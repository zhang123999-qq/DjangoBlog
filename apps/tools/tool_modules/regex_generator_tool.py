"""
正则表达式生成器工具
"""

from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool


class RegexGeneratorForm(forms.Form):
    """正则表达式生成器表单"""

    text = forms.CharField(
        label="目标文本", widget=forms.Textarea(attrs={"rows": 4, "class": "form-control"}), required=True
    )
    pattern_type = forms.ChoiceField(
        label="匹配模式",
        choices=[
            ("email", "邮箱"),
            ("url", "URL"),
            ("phone", "手机号"),
            ("number", "数字"),
            ("date", "日期"),
            ("ip", "IP地址"),
        ],
        initial="email",
        widget=forms.Select(attrs={"class": "form-control"}),
    )


class RegexGeneratorTool(BaseTool):
    """正则表达式生成器工具"""

    name = "正则表达式生成器"
    slug = "regex-generator"
    description = "根据示例文本生成简单的正则表达式"
    icon = "fa fa-code"
    category = ToolCategory.GENERATE
    form_class = RegexGeneratorForm

    def handle(self, request, form):
        text = form.cleaned_data["text"]
        pattern_type = form.cleaned_data["pattern_type"]

        try:
            # 预定义正则模板
            patterns = {
                "email": r"[\w\.-]+@[\w\.-]+\.\w+",
                "url": r"https?://[\w\.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&\'\(\)\*\+,;=.]+",
                "phone": r"1[3-9]\d{9}",
                "number": r"-?\d+(?:\.\d+)?",
                "date": r"\d{4}-\d{2}-\d{2}",
                "ip": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
            }

            # 获取对应的正则表达式
            regex_pattern = patterns.get(pattern_type)
            if not regex_pattern:
                return {"error": "不支持的模式类型"}

            # 测试正则表达式
            import re

            matches = re.findall(regex_pattern, text)

            return {"text": text, "pattern_type": pattern_type, "regex_pattern": regex_pattern, "matches": matches}
        except Exception as e:
            return {"error": str(e)}
