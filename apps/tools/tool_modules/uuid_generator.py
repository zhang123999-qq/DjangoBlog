"""
UUID Generator Tool
Generate UUID/GUID with different versions
"""

from ..categories import ToolCategory
from django import forms
import uuid
from apps.tools.base_tool import BaseTool


class UUIDForm(forms.Form):
    version = forms.ChoiceField(
        choices=[
            ("4", "UUID v4 (Random)"),
            ("1", "UUID v1 (Time-based)"),
            ("3", "UUID v3 (MD5)"),
            ("5", "UUID v5 (SHA1)"),
        ],
        initial="4",
        label="UUID Version",
    )
    count = forms.IntegerField(min_value=1, max_value=100, initial=1, label="Count")
    namespace = forms.CharField(
        required=False, max_length=100, label="Namespace (for v3/v5)", help_text="DNS, URL, or custom string"
    )
    name = forms.CharField(required=False, max_length=100, label="Name (for v3/v5)")
    uppercase = forms.BooleanField(required=False, initial=False, label="Uppercase")
    no_hyphens = forms.BooleanField(required=False, initial=False, label="Remove hyphens")


def generate_uuids(version, count, namespace=None, name=None, uppercase=False, no_hyphens=False):
    """Generate UUIDs based on version"""
    uuids = []

    for _ in range(count):
        if version == "4":
            new_uuid = uuid.uuid4()
        elif version == "1":
            new_uuid = uuid.uuid1()
        elif version == "3":
            if namespace and name:
                # Parse namespace
                if namespace.lower() == "dns":
                    ns = uuid.NAMESPACE_DNS
                elif namespace.lower() == "url":
                    ns = uuid.NAMESPACE_URL
                elif namespace.lower() == "oid":
                    ns = uuid.NAMESPACE_OID
                else:
                    ns = uuid.uuid5(uuid.NAMESPACE_DNS, namespace)
                new_uuid = uuid.uuid3(ns, name)
            else:
                new_uuid = uuid.uuid4()  # Fallback
        elif version == "5":
            if namespace and name:
                if namespace.lower() == "dns":
                    ns = uuid.NAMESPACE_DNS
                elif namespace.lower() == "url":
                    ns = uuid.NAMESPACE_URL
                elif namespace.lower() == "oid":
                    ns = uuid.NAMESPACE_OID
                else:
                    ns = uuid.uuid5(uuid.NAMESPACE_DNS, namespace)
                new_uuid = uuid.uuid5(ns, name)
            else:
                new_uuid = uuid.uuid4()  # Fallback
        else:
            new_uuid = uuid.uuid4()

        uuid_str = str(new_uuid)

        if uppercase:
            uuid_str = uuid_str.upper()

        if no_hyphens:
            uuid_str = uuid_str.replace("-", "")

        uuids.append(uuid_str)

    return uuids


def process(form):
    """Process the form and return result"""
    if not form.is_valid():
        return {"error": "Invalid input", "uuids": []}

    cleaned = form.cleaned_data
    version = cleaned.get("version", "4")
    count = cleaned.get("count", 1)
    namespace = cleaned.get("namespace", "")
    name = cleaned.get("name", "")
    uppercase = cleaned.get("uppercase", False)
    no_hyphens = cleaned.get("no_hyphens", False)

    uuids = generate_uuids(version, count, namespace, name, uppercase, no_hyphens)

    return {
        "uuids": uuids,
        "count": len(uuids),
        "version": version,
    }


# Tool class for registry


class UUIDGeneratorTool(BaseTool):
    name = "UUID生成器"
    slug = "uuid"
    description = "生成UUID/GUID，支持多种版本"
    icon = "key"
    category = ToolCategory.GENERATE
    form_class = UUIDForm

    def handle(self, request, form):
        return process(form)
