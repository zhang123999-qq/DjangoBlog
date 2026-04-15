from django.core.cache import cache
from .models import SensitiveWord


def get_sensitive_words():
    """获取敏感词列表（带缓存）

    Returns:
        list: 敏感词列表
    """
    words = cache.get("sensitive_words")
    if words is None:
        words = list(SensitiveWord.objects.filter(is_active=True).values_list("word", flat=True))
        # 缓存1小时
        cache.set("sensitive_words", words, 3600)
    return words


def clear_sensitive_words_cache():
    """清除敏感词缓存"""
    cache.delete("sensitive_words")


def check_sensitive_content(content):
    """检查内容是否包含敏感词

    Args:
        content: 要检查的内容

    Returns:
        tuple: (是否包含敏感词, 命中的敏感词列表)
    """
    if not content:
        return False, []

    # 使用缓存的敏感词列表
    sensitive_words = get_sensitive_words()

    if not sensitive_words:
        return False, []

    hit_words = []
    content_lower = content.lower()

    for word in sensitive_words:
        if word.lower() in content_lower:
            hit_words.append(word)

    return len(hit_words) > 0, hit_words


def auto_moderate(obj, content_field="content"):
    """自动审核内容

    无敏感词 → 自动通过（approved）
    有敏感词 → 进入人工审核（pending）

    Args:
        obj: 要审核的对象
        content_field: 内容字段名

    Returns:
        bool: 是否包含敏感内容
    """
    content = getattr(obj, content_field, "")
    has_sensitive, hit_words = check_sensitive_content(content)

    if has_sensitive:
        obj.review_status = "pending"
        obj.review_note = f'命中敏感词: {", ".join(hit_words)}'
    else:
        obj.review_status = "approved"
        obj.review_note = "自动审核通过（无敏感词）"

    return has_sensitive
