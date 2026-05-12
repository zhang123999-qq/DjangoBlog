"""
Code Beautifier / Formatter Tool
Format and beautify code (JSON, CSS, HTML, SQL)
"""

from ..categories import ToolCategory
from django import forms
import json
import re
from apps.tools.base_tool import BaseTool


class CodeBeautifyForm(forms.Form):
    MODE_CHOICES = [
        ("json", "JSON"),
        ("css", "CSS"),
        ("html", "HTML"),
        ("sql", "SQL"),
        ("xml", "XML"),
    ]

    mode = forms.ChoiceField(choices=MODE_CHOICES, initial="json", label="Code Type")
    code = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 12, "class": "form-control", "spellcheck": "false"}),
        label="Input Code",
        required=True,
    )
    action = forms.ChoiceField(
        choices=[
            ("beautify", "Beautify / Format"),
            ("minify", "Minify / Compress"),
        ],
        initial="beautify",
        label="Action",
    )
    indent = forms.IntegerField(min_value=1, max_value=8, initial=2, label="Indent spaces")


def beautify_json(code, indent=2):
    """Beautify JSON"""
    try:
        data = json.loads(code)
        result = json.dumps(data, indent=indent, ensure_ascii=False, sort_keys=False)
        return {"result": result, "valid": True}
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}", "valid": False}


def minify_json(code):
    """Minify JSON"""
    try:
        data = json.loads(code)
        result = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
        return {"result": result, "valid": True}
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}", "valid": False}


def beautify_css(code, indent=2):
    """Beautify CSS"""
    try:
        # Remove extra whitespace
        code = re.sub(r"\s+", " ", code)

        # Add newlines after braces and semicolons
        result = code.replace("{", " {\n" + " " * indent)
        result = result.replace("}", "\n}\n")
        result = result.replace(";", ";\n")

        # Clean up
        lines = result.split("\n")
        formatted = []
        indent_level = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("}"):
                indent_level = max(0, indent_level - 1)

            formatted.append(" " * indent * indent_level + line)

            if line.endswith("{"):
                indent_level += 1

        result = "\n".join(formatted)
        return {"result": result, "valid": True}
    except Exception as e:
        return {"error": str(e), "valid": False}


def minify_css(code):
    """Minify CSS"""
    try:
        # Remove comments
        code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)
        # Remove whitespace
        code = re.sub(r"\s+", " ", code)
        # Remove spaces around special chars
        code = re.sub(r"\s*([{};:,>+~])\s*", r"\1", code)
        # Remove trailing semicolons before closing braces
        code = re.sub(r";}", "}", code)
        return {"result": code.strip(), "valid": True}
    except Exception as e:
        return {"error": str(e), "valid": False}


def beautify_html(code, indent=2):
    """Beautify HTML"""
    try:
        # Simple HTML beautifier
        code = re.sub(r">\s+<", ">\n<", code)

        lines = code.split("\n")
        formatted = []
        indent_level = 0

        # Tags that increase indent
        opening_tags = re.compile(r"^<(?!/|!|br|hr|img|input|meta|link)(\w+)[^>]*>$")
        closing_tags = re.compile(r"^</(\w+)>$")
        self_closing = re.compile(r"^<(br|hr|img|input|meta|link|area|base|col|embed|param|source|track|wbr)[^>]*/?>$")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for closing tag first
            closing_match = closing_tags.match(line)
            if closing_match:
                indent_level = max(0, indent_level - 1)

            formatted.append(" " * indent * indent_level + line)

            # Check for opening tag
            if opening_tags.match(line) and not self_closing.match(line):
                indent_level += 1

        result = "\n".join(formatted)
        return {"result": result, "valid": True}
    except Exception as e:
        return {"error": str(e), "valid": False}


def minify_html(code):
    """Minify HTML"""
    try:
        # Remove comments
        code = re.sub(r"<!--.*?-->", "", code, flags=re.DOTALL)
        # Remove whitespace
        code = re.sub(r"\s+", " ", code)
        # Remove spaces around tags
        code = re.sub(r">\s+<", "><", code)
        return {"result": code.strip(), "valid": True}
    except Exception as e:
        return {"error": str(e), "valid": False}


def beautify_sql(code, indent=2):
    """Beautify SQL"""
    try:
        # Keywords to uppercase and newline
        keywords = [
            "SELECT",
            "FROM",
            "WHERE",
            "AND",
            "OR",
            "ORDER BY",
            "GROUP BY",
            "HAVING",
            "LIMIT",
            "OFFSET",
            "JOIN",
            "LEFT JOIN",
            "RIGHT JOIN",
            "INNER JOIN",
            "OUTER JOIN",
            "ON",
            "INSERT INTO",
            "VALUES",
            "UPDATE",
            "SET",
            "DELETE FROM",
            "CREATE TABLE",
            "ALTER TABLE",
            "DROP TABLE",
            "UNION",
            "UNION ALL",
        ]

        result = code.upper()

        for keyword in sorted(keywords, key=len, reverse=True):
            result = re.sub(r"\b" + keyword + r"\b", "\n" + keyword, result, flags=re.IGNORECASE)

        # Clean up
        result = re.sub(r"\n\s*\n", "\n", result)
        result = result.strip()

        return {"result": result, "valid": True}
    except Exception as e:
        return {"error": str(e), "valid": False}


def minify_sql(code):
    """Minify SQL"""
    try:
        # Remove comments
        code = re.sub(r"--.*$", "", code, flags=re.MULTILINE)
        code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)
        # Remove extra whitespace
        code = re.sub(r"\s+", " ", code)
        return {"result": code.strip(), "valid": True}
    except Exception as e:
        return {"error": str(e), "valid": False}


def beautify_xml(code, indent=2):
    """Beautify XML"""
    try:
        from defusedxml.minidom import parseString

        dom = parseString(code)
        result = dom.toprettyxml(indent=" " * indent)

        # Remove extra blank lines
        result = "\n".join([line for line in result.split("\n") if line.strip()])

        return {"result": result, "valid": True}
    except Exception as e:
        return {"error": str(e), "valid": False}


def process(form):
    """Process the form and return result"""
    if not form.is_valid():
        return {"error": "Invalid input"}

    cleaned = form.cleaned_data
    mode = cleaned.get("mode", "json")
    code = cleaned.get("code", "")
    action = cleaned.get("action", "beautify")
    indent = cleaned.get("indent", 2)

    if mode == "json":
        if action == "beautify":
            result = beautify_json(code, indent)
        else:
            result = minify_json(code)
    elif mode == "css":
        if action == "beautify":
            result = beautify_css(code, indent)
        else:
            result = minify_css(code)
    elif mode == "html":
        if action == "beautify":
            result = beautify_html(code, indent)
        else:
            result = minify_html(code)
    elif mode == "sql":
        if action == "beautify":
            result = beautify_sql(code, indent)
        else:
            result = minify_sql(code)
    elif mode == "xml":
        if action == "beautify":
            result = beautify_xml(code, indent)
        else:
            result = minify_json(code)  # XML minify similar to JSON
    else:
        return {"error": "Unknown mode"}

    # Add statistics
    if "result" in result:
        result["original_size"] = len(code)
        result["result_size"] = len(result["result"])
        result["compression_ratio"] = round(len(result["result"]) / max(len(code), 1) * 100, 1)

    return result


# Tool class for registry


class CodeBeautifyTool(BaseTool):
    name = "代码格式化"
    slug = "code-format"
    description = "美化/压缩 JSON/CSS/HTML/SQL 代码"
    icon = "code"
    category = ToolCategory.DATA
    form_class = CodeBeautifyForm

    def handle(self, request, form):
        return process(form)
