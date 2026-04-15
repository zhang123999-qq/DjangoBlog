"""Pytest 兼容入口。

保留该文件是为了兼容 `pytest moderation/tests.py` 的调用习惯，
真实测试用例位于 `tests/test_moderation_smoke.py`。
"""

from tests.test_moderation_smoke import *  # noqa: F401,F403
