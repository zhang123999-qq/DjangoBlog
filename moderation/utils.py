"""
敏感词检测工具

使用 Aho-Corasick 自动机实现 O(n) 多模式匹配
纯 Python 实现，无外部依赖
"""

from collections import deque
from django.core.cache import cache
from .models import SensitiveWord


class AhoCorasick:
    """Aho-Corasick 自动机（纯 Python 实现）"""

    __slots__ = ("_goto", "_fail", "_output")

    def __init__(self, patterns: list[str]):
        """构建自动机

        Args:
            patterns: 模式串列表（已小写）
        """
        self._goto: list[dict[str, int]] = [{}]  # 状态转移表
        self._fail: list[int] = [0]   # 失败跳转表
        self._output: list[dict[int, str]] = [{}]  # 输出表

        self._build_trie(patterns)
        self._build_fail()

    def _build_trie(self, patterns: list[str]):
        """构建 Trie 树"""
        for idx, pattern in enumerate(patterns):
            if not pattern:
                continue
            state = 0
            for ch in pattern:
                if ch not in self._goto[state]:
                    self._goto[state][ch] = len(self._goto)
                    self._goto.append({})
                    self._fail.append(0)
                    self._output.append({})
                state = self._goto[state][ch]
            self._output[state][idx] = pattern

    def _build_fail(self):
        """构建失败跳转（BFS）"""
        q: deque[int] = deque()

        # 初始化深度为 1 的节点
        for ch, next_state in self._goto[0].items():
            q.append(next_state)
            self._fail[next_state] = 0

        # BFS 构建失败跳转
        while q:
            r = q.popleft()
            for ch, u in self._goto[r].items():
                q.append(u)
                v = self._fail[r]
                while v and ch not in self._goto[v]:
                    v = self._fail[v]
                self._fail[u] = self._goto[v].get(ch, 0)
                # 合并输出
                self._output[u].update(self._output[self._fail[u]])

    def search(self, text: str) -> list[str]:
        """搜索文本中的所有模式

        Args:
            text: 待搜索文本（已小写）

        Returns:
            匹配到的模式列表（去重，保持首次出现顺序）
        """
        state = 0
        hits = []
        seen = set()

        for ch in text:
            while state and ch not in self._goto[state]:
                state = self._fail[state]
            state = self._goto[state].get(ch, 0)

            if self._output[state]:
                for idx, pattern in self._output[state].items():
                    if pattern not in seen:
                        seen.add(pattern)
                        hits.append(pattern)

        return hits


# 模块级缓存
_automaton: AhoCorasick | None = None
_automaton_version = 0


def _get_automaton() -> AhoCorasick:
    """获取或构建自动机（带版本缓存）"""
    global _automaton, _automaton_version

    words = cache.get("sensitive_words")
    version = cache.get("sensitive_words_version", 0)

    if words is None:
        words = list(SensitiveWord.objects.filter(is_active=True).values_list("word", flat=True))
        cache.set("sensitive_words", words, 3600)
        cache.set("sensitive_words_version", 1, 3600)
        version = 1

    # 版本变化或首次构建时重建自动机
    if _automaton is None or version != _automaton_version:
        # 过滤空串并小写
        patterns = [w.lower() for w in words if w]
        _automaton = AhoCorasick(patterns)
        _automaton_version = version

    return _automaton


def get_sensitive_words() -> list[str]:
    """获取敏感词列表（带缓存）"""
    words = cache.get("sensitive_words")
    if words is None:
        words = list(SensitiveWord.objects.filter(is_active=True).values_list("word", flat=True))
        cache.set("sensitive_words", words, 3600)
    return words if isinstance(words, list) else []


def clear_sensitive_words_cache():
    """清除敏感词缓存（同时增加版本号触发自动机重建）"""
    cache.delete("sensitive_words")
    cache.incr("sensitive_words_version")


def check_sensitive_content(content: str) -> tuple[bool, list[str]]:
    """检查内容是否包含敏感词

    Args:
        content: 要检查的内容

    Returns:
        tuple: (是否包含敏感词, 命中的敏感词列表)
    """
    if not content:
        return False, []

    automaton = _get_automaton()
    if automaton is None:
        return False, []

    content_lower = content.lower()
    hit_words = automaton.search(content_lower)

    return len(hit_words) > 0, hit_words


def auto_moderate(obj, content_field: str = "content") -> bool:
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