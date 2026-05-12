"""
Diff / Text Compare Tool
Compare two texts and show differences
"""

from ..categories import ToolCategory
from django import forms
import difflib
from apps.tools.base_tool import BaseTool


class DiffForm(forms.Form):
    text1 = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 10, "class": "form-control"}), label="Original Text", required=True
    )
    text2 = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 10, "class": "form-control"}), label="Modified Text", required=True
    )
    show_line_numbers = forms.BooleanField(required=False, initial=True, label="Show line numbers")
    context_lines = forms.IntegerField(min_value=0, max_value=10, initial=3, label="Context lines")


def diff_texts(text1, text2, show_line_numbers=True, context_lines=3):
    """Compare two texts and return unified diff"""
    lines1 = text1.splitlines(keepends=True)
    lines2 = text2.splitlines(keepends=True)

    # Generate unified diff
    diff = difflib.unified_diff(lines1, lines2, fromfile="Original", tofile="Modified", n=context_lines)

    diff_text = "".join(diff)

    # Parse diff for HTML display
    diff_lines = []
    for line in diff_text.splitlines():
        line_type = "context"
        if line.startswith("@@"):
            line_type = "header"
        elif line.startswith("---"):
            line_type = "old_file"
        elif line.startswith("+++"):
            line_type = "new_file"
        elif line.startswith("-") and not line.startswith("---"):
            line_type = "removed"
        elif line.startswith("+") and not line.startswith("+++"):
            line_type = "added"

        diff_lines.append({"text": line, "type": line_type})

    # Calculate statistics
    additions = sum(1 for line in diff_lines if line["type"] == "added")
    removals = sum(1 for line in diff_lines if line["type"] == "removed")

    return {
        "diff_text": diff_text,
        "diff_lines": diff_lines,
        "additions": additions,
        "removals": removals,
        "has_changes": additions > 0 or removals > 0,
    }


def side_by_side_diff(text1, text2):
    """Generate side-by-side diff view"""
    lines1 = text1.splitlines()
    lines2 = text2.splitlines()

    # Use SequenceMatcher for better alignment
    matcher = difflib.SequenceMatcher(None, lines1, lines2)

    left_lines = []
    right_lines = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for i in range(i1, i2):
                left_lines.append({"text": lines1[i], "type": "equal"})
                right_lines.append({"text": lines2[j1 + (i - i1)], "type": "equal"})
        elif tag == "replace":
            for i in range(i1, i2):
                left_lines.append({"text": lines1[i], "type": "changed"})
            for j in range(j1, j2):
                right_lines.append({"text": lines2[j], "type": "changed"})
            # Pad shorter side
            left_len = i2 - i1
            right_len = j2 - j1
            if left_len < right_len:
                for _ in range(right_len - left_len):
                    left_lines.append({"text": "", "type": "empty"})
            elif right_len < left_len:
                for _ in range(left_len - right_len):
                    right_lines.append({"text": "", "type": "empty"})
        elif tag == "delete":
            for i in range(i1, i2):
                left_lines.append({"text": lines1[i], "type": "removed"})
                right_lines.append({"text": "", "type": "empty"})
        elif tag == "insert":
            for j in range(j1, j2):
                left_lines.append({"text": "", "type": "empty"})
                right_lines.append({"text": lines2[j], "type": "added"})

    return {"left_lines": left_lines, "right_lines": right_lines, "total_lines": max(len(left_lines), len(right_lines))}


def process(form):
    """Process the form and return result"""
    if not form.is_valid():
        return {"error": "Invalid input"}

    cleaned = form.cleaned_data
    text1 = cleaned.get("text1", "")
    text2 = cleaned.get("text2", "")
    show_line_numbers = cleaned.get("show_line_numbers", True)
    context_lines = cleaned.get("context_lines", 3)

    # Generate unified diff
    unified = diff_texts(text1, text2, show_line_numbers, context_lines)

    # Generate side-by-side diff
    side_by_side = side_by_side_diff(text1, text2)

    return {
        "unified_diff": unified["diff_text"],
        "diff_lines": unified["diff_lines"],
        "side_by_side": side_by_side,
        "stats": {
            "additions": unified["additions"],
            "removals": unified["removals"],
            "has_changes": unified["has_changes"],
            "original_lines": len(text1.splitlines()),
            "modified_lines": len(text2.splitlines()),
        },
    }


# Tool class for registry


class DiffTool(BaseTool):
    name = "文本对比"
    slug = "diff"
    description = "对比两段文本的差异"
    icon = "diff"
    category = ToolCategory.TEXT
    form_class = DiffForm

    def handle(self, request, form):
        return process(form)
