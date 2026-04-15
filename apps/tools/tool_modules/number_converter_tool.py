"""
Number Converter Tool
Convert between different number formats and bases
"""

from ..categories import ToolCategory
from django import forms
import struct
from apps.tools.base_tool import BaseTool


class NumberConverterForm(forms.Form):
    number = forms.CharField(
        max_length=100, label="Number", help_text="Enter a number (prefix with 0x for hex, 0b for binary, 0o for octal)"
    )
    input_base = forms.ChoiceField(
        choices=[
            ("auto", "Auto Detect"),
            ("2", "Binary (Base 2)"),
            ("8", "Octal (Base 8)"),
            ("10", "Decimal (Base 10)"),
            ("16", "Hexadecimal (Base 16)"),
        ],
        initial="auto",
        label="Input Base",
    )
    output_base = forms.ChoiceField(
        choices=[
            ("2", "Binary (Base 2)"),
            ("8", "Octal (Base 8)"),
            ("10", "Decimal (Base 10)"),
            ("16", "Hexadecimal (Base 16)"),
            ("all", "All Bases"),
        ],
        initial="all",
        label="Output Base",
    )
    show_float = forms.BooleanField(required=False, initial=False, label="Show float representation")


def parse_number(number_str, base="auto"):
    """Parse number string to integer"""
    number_str = number_str.strip().lower()

    if base == "auto":
        # Auto detect base
        if number_str.startswith("0x") or number_str.startswith("0X"):
            base = "16"
            number_str = number_str[2:]
        elif number_str.startswith("0b") or number_str.startswith("0B"):
            base = "2"
            number_str = number_str[1:]
        elif number_str.startswith("0o") or number_str.startswith("0O"):
            base = "8"
            number_str = number_str[2:]
        else:
            base = "10"

    try:
        return int(number_str, int(base))
    except ValueError:
        # Try float
        try:
            return float(number_str)
        except ValueError:
            return None


def float_to_hex(f):
    """Convert float to hex representation"""
    return hex(struct.unpack(">Q", struct.pack(">d", f))[0])


def float_to_binary(f):
    """Convert float to binary representation"""
    return bin(struct.unpack(">Q", struct.pack(">d", f))[0])


def format_with_separators(number, base, separator="_", group_size=None):
    """Format number with separators for readability"""
    if group_size is None:
        group_size = {2: 8, 8: 3, 10: 3, 16: 4}.get(base, 4)

    if base == 2:
        s = bin(number)[2:]
    elif base == 8:
        s = oct(number)[2:]
    elif base == 10:
        s = str(number)
    elif base == 16:
        s = hex(number)[2:]
    else:
        s = str(number)

    # Pad to multiple of group_size
    if len(s) % group_size != 0:
        s = "0" * (group_size - len(s) % group_size) + s

    # Add separators
    groups = [s[i : i + group_size] for i in range(0, len(s), group_size)]
    return separator.join(groups)


def process(form):
    """Process the form and return result"""
    if not form.is_valid():
        return {"error": "Invalid input"}

    cleaned = form.cleaned_data
    number_str = cleaned.get("number", "").strip()
    input_base = cleaned.get("input_base", "auto")
    output_base = cleaned.get("output_base", "all")
    show_float = cleaned.get("show_float", False)

    # Parse the number
    number = parse_number(number_str, input_base)

    if number is None:
        return {"error": "Invalid number format"}

    result = {
        "input": number_str,
        "parsed": number,
        "is_float": isinstance(number, float),
    }

    # Generate conversions
    if output_base == "all":
        if isinstance(number, int):
            result["binary"] = bin(number)[2:]
            result["binary_formatted"] = format_with_separators(number, 2)
            result["octal"] = oct(number)[2:]
            result["decimal"] = str(number)
            result["hexadecimal"] = hex(number)[2:].upper()
            result["hexadecimal_formatted"] = format_with_separators(number, 16).upper()
        else:
            result["decimal"] = str(number)
            if show_float:
                result["hex_float"] = float_to_hex(number)
                result["binary_float"] = float_to_binary(number)
    else:
        base = int(output_base)
        if isinstance(number, int):
            if base == 2:
                result["output"] = bin(number)[2:]
                result["output_formatted"] = format_with_separators(number, 2)
            elif base == 8:
                result["output"] = oct(number)[2:]
            elif base == 10:
                result["output"] = str(number)
            elif base == 16:
                result["output"] = hex(number)[2:].upper()
                result["output_formatted"] = format_with_separators(number, 16).upper()
        else:
            result["output"] = str(number)

    # Additional representations
    if isinstance(number, int):
        result["ascii"] = ""
        if 0 <= number <= 0x10FFFF:
            try:
                result["ascii"] = chr(number)
            except Exception:
                pass

        result["byte_count"] = (number.bit_length() + 7) // 8 or 1
        result["signed"] = number if number < 2**63 else f"{number} (too large for signed 64-bit)"

    return result


# Tool class for registry


class NumberConverterTool(BaseTool):
    name = "数字格式转换"
    slug = "number-converter"
    description = "自动识别并转换二/八/十/十六进制，支持浮点表示"
    icon = "number"
    category = ToolCategory.ENCODE
    form_class = NumberConverterForm

    def handle(self, request, form):
        return process(form)
