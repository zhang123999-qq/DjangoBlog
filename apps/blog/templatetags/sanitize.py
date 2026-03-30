from django import template
from django.utils.safestring import mark_safe
import bleach

register = template.Library()

# Allowed tags and attributes for user content
ALLOWED_TAGS = [
    'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'p', 'pre',
    'strong', 'ul', 'br', 'img', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'table', 'thead',
    'tbody', 'tr', 'th', 'td', 'div', 'span'
]

ALLOWED_ATTRIBUTES = {
    '*': ['class', 'id', 'title'],
    'a': ['href', 'title', 'rel', 'target'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
}


@register.filter(is_safe=True)
def safe_html(value: str) -> str:
    """Sanitize rich HTML from editors and mark it safe for templates.

    Uses bleach to remove disallowed tags/attributes and linkify plain URLs.
    """
    if not value:
        return ''

    cleaned = bleach.clean(
        value,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
    )

    # Convert bare URLs into links
    cleaned = bleach.linkify(cleaned)

    return mark_safe(cleaned)
