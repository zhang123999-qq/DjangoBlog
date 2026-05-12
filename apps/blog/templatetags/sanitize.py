from django import template
from django.utils.safestring import mark_safe
import bleach
import html as _html

register = template.Library()

# Allowed tags and attributes for user content
ALLOWED_TAGS = [
    "a",
    "abbr",
    "acronym",
    "b",
    "blockquote",
    "code",
    "em",
    "i",
    "li",
    "ol",
    "p",
    "pre",
    "strong",
    "ul",
    "br",
    "img",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "div",
    "span",
]

ALLOWED_ATTRIBUTES = {
    "*": ["class", "id", "title"],
    "a": ["href", "title", "rel", "target"],
    "img": ["src", "alt", "title", "width", "height"],
}


@register.filter(is_safe=True)
def safe_html(value: str) -> str:
    """Sanitize rich HTML from editors and mark it safe for templates.

    Uses bleach to remove disallowed tags/attributes and linkify plain URLs.
    """
    if not value:
        return ""

    # 如果内容中包含被转义的 HTML 实体（例如来自某些编辑器的保存格式），先反转义
    try:
        unescaped = _html.unescape(value)
    except Exception:
        unescaped = value

    cleaned = bleach.clean(
        unescaped,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
    )

    # 将裸链转换为可点击链接
    cleaned = bleach.linkify(cleaned)

    return mark_safe(cleaned)
