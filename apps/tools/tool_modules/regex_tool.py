"""
正则表达式测试工具
"""

import re
from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool


class RegexForm(forms.Form):
    """正则表达式表单"""

    pattern = forms.CharField(
        label="正则表达式",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": r"例如: \d+"}),
        required=True,
    )
    text = forms.CharField(
        label="测试文本", widget=forms.Textarea(attrs={"rows": 5, "class": "form-control"}), required=True
    )
    flags = forms.MultipleChoiceField(
        label="修饰符",
        required=False,
        choices=[
            ("ignore", "忽略大小写 (i)"),
            ("multiline", "多行模式 (m)"),
            ("dotall", "点匹配换行 (s)"),
        ],
        widget=forms.CheckboxSelectMultiple(),
    )


class RegexTool(BaseTool):
    """正则表达式测试工具"""

    name = "正则测试"
    slug = "regex"
    description = "测试正则表达式匹配"
    icon = "fa fa-code"
    category = ToolCategory.OTHER
    form_class = RegexForm

    def handle(self, request, form):
        pattern = form.cleaned_data["pattern"]
        text = form.cleaned_data["text"]
        flags_list = form.cleaned_data.get("flags", [])

        # 构建flags
        flags = 0
        if "ignore" in flags_list:
            flags |= re.IGNORECASE
        if "multiline" in flags_list:
            flags |= re.MULTILINE
        if "dotall" in flags_list:
            flags |= re.DOTALL

        try:
            # 编译正则
            regex = re.compile(pattern, flags)

            # 查找所有匹配
            matches = []
            for match in regex.finditer(text):
                matches.append(
                    {
                        "match": match.group(),
                        "start": match.start(),
                        "end": match.end(),
                        "groups": match.groups() if match.groups() else None,
                    }
                )

            return {
                "pattern": pattern,
                "text": text,
                "flags": flags_list,
                "matches": matches,
                "count": len(matches),
            }
        except re.error as e:
            return {"error": f"正则表达式错误: {str(e)}"}
        except Exception as e:
            return {"error": str(e)}
