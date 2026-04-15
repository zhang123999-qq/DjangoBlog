"""
颜色转换工具
"""

from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool


class ColorForm(forms.Form):
    """颜色表单"""

    color = forms.CharField(
        label="颜色值",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "例如: #FF5733 或 rgb(255,87,51)", "id": "color-input"}
        ),
        required=True,
    )


class ColorTool(BaseTool):
    """颜色转换工具"""

    name = "颜色转换"
    slug = "color"
    description = "颜色格式转换工具"
    icon = "fa fa-palette"
    category = ToolCategory.IMAGE
    form_class = ColorForm

    def hex_to_rgb(self, hex_color):
        """HEX转RGB"""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    def rgb_to_hex(self, r, g, b):
        """RGB转HEX"""
        return f"#{r:02X}{g:02X}{b:02X}"

    def rgb_to_hsl(self, r, g, b):
        """RGB转HSL"""
        r, g, b = r / 255, g / 255, b / 255
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        lightness = (max_c + min_c) / 2

        if max_c == min_c:
            h = s = 0
        else:
            d = max_c - min_c
            s = d / (2 - max_c - min_c)
            if max_c == r:
                h = (g - b) / d + (6 if g < b else 0)
            elif max_c == g:
                h = (b - r) / d + 2
            else:
                h = (r - g) / d + 4
            h /= 6

        return round(h * 360), round(s * 100), round(lightness * 100)

    def handle(self, request, form):
        color = form.cleaned_data["color"].strip()

        try:
            r, g, b = None, None, None

            # 解析颜色值
            if color.startswith("#"):
                r, g, b = self.hex_to_rgb(color)
            elif color.lower().startswith("rgb"):
                # 解析 rgb(r,g,b)
                nums = color.replace("rgb", "").replace("(", "").replace(")", "").split(",")
                r, g, b = int(nums[0]), int(nums[1]), int(nums[2])
            elif color.lower().startswith("hsl"):
                # 解析 hsl(h,s%,l%)
                return {"error": "HSL输入暂不支持，请使用HEX或RGB格式"}
            else:
                # 尝试作为HEX处理
                if len(color) == 6:
                    r, g, b = self.hex_to_rgb("#" + color)
                else:
                    return {"error": "无法识别的颜色格式"}

            if r is None:
                return {"error": "无法解析颜色值"}

            # 转换为各种格式
            h, s, lightness = self.rgb_to_hsl(r, g, b)

            return {
                "input": color,
                "hex": self.rgb_to_hex(r, g, b),
                "rgb": f"rgb({r}, {g}, {b})",
                "rgba": f"rgba({r}, {g}, {b}, 1)",
                "hsl": f"hsl({h}, {s}%, {lightness}%)",
                "values": {
                    "r": r,
                    "g": g,
                    "b": b,
                    "h": h,
                    "s": s,
                    "lightness": lightness,
                },
                "preview": self.rgb_to_hex(r, g, b),
            }
        except Exception as e:
            return {"error": f"颜色解析错误: {str(e)}"}
