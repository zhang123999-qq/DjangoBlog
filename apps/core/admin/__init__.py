"""
DjangoBlog Admin 包

统一使用自定义 admin_site 管理所有模型。
拆分自原 admin.py（约 550 行），按模块拆分为独立文件。
"""

from .admin_site import admin_site
from .blog_admin import *  # noqa: F401, F403
from .comment_admin import *  # noqa: F401, F403
from .forum_admin import *  # noqa: F401, F403
from .moderation_admin import *  # noqa: F401, F403
from .site_config_admin import *  # noqa: F401, F403
from .tool_admin import *  # noqa: F401, F403
from .user_admin import *  # noqa: F401, F403
from .builtin_admin import *  # noqa: F401, F403
