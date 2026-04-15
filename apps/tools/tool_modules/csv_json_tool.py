"""
CSV与JSON互转工具
"""

from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool
import csv
import json
import io


class CSVJSONForm(forms.Form):
    """CSV与JSON互转表单"""

    mode = forms.ChoiceField(
        label="操作",
        choices=[
            ("csv_to_json", "CSV转JSON"),
            ("json_to_csv", "JSON转CSV"),
        ],
        initial="csv_to_json",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    data = forms.CharField(
        label="数据", widget=forms.Textarea(attrs={"rows": 8, "class": "form-control"}), required=True
    )


class CSVJSONTool(BaseTool):
    """CSV与JSON互转工具"""

    name = "CSV/JSON互转"
    slug = "csv-json"
    description = "将CSV数据转换为JSON数组/对象，或将JSON数组转换为CSV"
    icon = "fa fa-exchange-alt"
    category = ToolCategory.DATA
    form_class = CSVJSONForm

    def handle(self, request, form):
        mode = form.cleaned_data["mode"]
        data = form.cleaned_data["data"]

        try:
            if mode == "csv_to_json":
                # CSV转JSON
                csv_data = io.StringIO(data)
                reader = csv.DictReader(csv_data)
                result = json.dumps(list(reader), ensure_ascii=False, indent=2)
            else:
                # JSON转CSV
                json_data = json.loads(data)
                if not isinstance(json_data, list):
                    return {"error": "JSON数据必须是数组格式"}
                if not json_data:
                    return {"error": "JSON数组不能为空"}

                # 获取所有字段名
                fieldnames = set()
                for item in json_data:
                    if isinstance(item, dict):
                        fieldnames.update(item.keys())
                fieldnames = list(fieldnames)

                # 写入CSV
                csv_output = io.StringIO()
                writer = csv.DictWriter(csv_output, fieldnames=fieldnames)
                writer.writeheader()
                for item in json_data:
                    if isinstance(item, dict):
                        writer.writerow(item)
                result = csv_output.getvalue()

            return {"mode": "CSV转JSON" if mode == "csv_to_json" else "JSON转CSV", "result": result}
        except json.JSONDecodeError as e:
            return {"error": f"JSON解析错误: {str(e)}"}
        except Exception as e:
            return {"error": str(e)}
