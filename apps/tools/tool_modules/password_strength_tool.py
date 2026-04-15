"""
密码强度检测工具
"""

from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool
import re


class PasswordStrengthForm(forms.Form):
    """密码强度检测表单"""

    password = forms.CharField(
        label="密码",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "输入要检测的密码"}),
        required=True,
    )


class PasswordStrengthTool(BaseTool):
    """密码强度检测工具"""

    name = "密码强度检测"
    slug = "password-strength"
    description = "检测密码强度等级，给出安全建议"
    icon = "fa fa-shield-alt"
    category = ToolCategory.SECURITY
    form_class = PasswordStrengthForm

    def handle(self, request, form):
        password = form.cleaned_data["password"]

        # 检测各项指标
        checks = {
            "length": len(password) >= 8,
            "length_strong": len(password) >= 12,
            "uppercase": bool(re.search(r"[A-Z]", password)),
            "lowercase": bool(re.search(r"[a-z]", password)),
            "digits": bool(re.search(r"\d", password)),
            "symbols": bool(re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password)),
            "no_common": password.lower() not in ["password", "123456", "qwerty", "abc123", "111111", "password123"],
            "no_sequential": not self._has_sequential(password),
            "no_repeated": not self._has_repeated(password),
        }

        # 计算分数
        score = sum(
            [
                checks["length"] * 10,
                checks["length_strong"] * 5,
                checks["uppercase"] * 15,
                checks["lowercase"] * 10,
                checks["digits"] * 15,
                checks["symbols"] * 20,
                checks["no_common"] * 10,
                checks["no_sequential"] * 10,
                checks["no_repeated"] * 5,
            ]
        )

        # 确定强度等级
        if score >= 80:
            level = "非常强"
            level_class = "success"
            emoji = "💪"
        elif score >= 60:
            level = "强"
            level_class = "info"
            emoji = "✅"
        elif score >= 40:
            level = "中等"
            level_class = "warning"
            emoji = "⚠️"
        else:
            level = "弱"
            level_class = "danger"
            emoji = "❌"

        # 生成建议
        suggestions = []
        if not checks["length"]:
            suggestions.append("建议密码长度至少8位")
        if not checks["length_strong"] and checks["length"]:
            suggestions.append("密码长度12位以上更安全")
        if not checks["uppercase"]:
            suggestions.append("添加大写字母可提高安全性")
        if not checks["lowercase"]:
            suggestions.append("添加小写字母可提高安全性")
        if not checks["digits"]:
            suggestions.append("添加数字可提高安全性")
        if not checks["symbols"]:
            suggestions.append("添加特殊字符可显著提高安全性")
        if not checks["no_common"]:
            suggestions.append("避免使用常见密码")
        if not checks["no_sequential"]:
            suggestions.append("避免使用连续字符（如123、abc）")
        if not checks["no_repeated"]:
            suggestions.append("避免使用重复字符（如111、aaa）")

        return {
            "score": min(score, 100),
            "level": level,
            "level_class": level_class,
            "emoji": emoji,
            "checks": checks,
            "suggestions": suggestions,
            "length": len(password),
        }

    def _has_sequential(self, password):
        """检测连续字符"""
        sequences = [
            "abcdefghijklmnopqrstuvwxyz",
            "01234567890",
            "qwertyuiop",
            "asdfghjkl",
            "zxcvbnm",
        ]
        password_lower = password.lower()
        for seq in sequences:
            for i in range(len(seq) - 2):
                if seq[i : i + 3] in password_lower or seq[i : i + 3][::-1] in password_lower:
                    return True
        return False

    def _has_repeated(self, password):
        """检测重复字符"""
        for i in range(len(password) - 2):
            if password[i] == password[i + 1] == password[i + 2]:
                return True
        return False
