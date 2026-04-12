# DjangoBlog 超级管理员后台 UI 重构方案

> **创建日期**: 2026-04-11  
> **状态**: 待实施

---

## 一、现状分析

### 1.1 现有结构

```
apps/core/admin/
├── __init__.py           # 统一导入
├── admin_site.py         # DjangoBlogAdminSite + 仪表盘统计
├── user_admin.py         # User + Profile (2个模型)
├── blog_admin.py         # Post
├── category_tag_admin.py # Category + Tag
├── comment_admin.py      # Comment
├── forum_admin.py        # Board + Topic + Reply (3个)
├── moderation_admin.py   # 6个审核相关模型
├── site_config_admin.py  # SiteConfig
├── tool_admin.py         # ToolConfig
└── builtin_admin.py      # Group + Site

templates/admin/
├── base_site.html        # 品牌覆盖 (25行)
├── index.html            # 自定义仪表盘 (185行)
└── change_form.html      # 表单样式 (116行内联CSS)

static/css/
├── admin-modern.css      # 133行
└── admin-editor.css      # 117行 (TinyMCE)
```

### 1.2 现有问题

| 问题 | 影响 | 优先级 |
|------|------|--------|
| 手写 CSS 维护成本高 | 修改样式需改多处 | P1 |
| change_form.html 内联 CSS | 不可复用、难维护 | P1 |
| 列表页未优化 | 默认 Django 样式，体验差 | P2 |
| 无暗色模式 | 夜间使用刺眼 | P2 |
| 移动端体验一般 | 响应式不够完善 | P3 |
| 无数据可视化 | 统计仅数字，缺少图表 | P3 |

---

## 二、技术选型

### 2.1 方案对比

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **django-unfold** | Tailwind CSS、暗色模式、现代设计、活跃维护 | 需迁移代码 | ⭐⭐⭐⭐⭐ |
| django-jazzmin | 功能全、Bootstrap | 设计稍旧、更新慢 | ⭐⭐⭐ |
| django-simpleui | Element UI、中文友好 | 不够现代 | ⭐⭐⭐ |
| 自研 | 完全可控 | 工作量大、维护成本高 | ⭐⭐ |

### 2.2 推荐：django-unfold

**选择理由：**

1. **设计最现代** - Tailwind CSS，像素级精美
2. **原生暗色模式** - 一键切换
3. **响应式完美** - 移动端体验极佳
4. **可定制性强** - 支持自定义 Dashboard、Actions、Widgets
5. **2025年活跃维护** - 持续更新

---

## 三、架构设计

### 3.1 目标架构

```
apps/core/admin/
├── __init__.py
├── admin_site.py         # UnfoldAdminSite 配置
├── dashboard.py          # [新增] 仪表盘配置
├── user_admin.py         # 继承 Unfold ModelAdmin
├── blog_admin.py
├── category_tag_admin.py
├── comment_admin.py
├── forum_admin.py
├── moderation_admin.py
├── site_config_admin.py
├── tool_admin.py
├── builtin_admin.py
└── widgets.py            # [新增] 自定义小部件

templates/admin/
├── base_site.html        # 简化，仅品牌覆盖
└── [删除其他]            # Unfold 自带模板

static/admin/
└── custom.css            # [新增] 少量自定义覆盖
```

### 3.2 核心变更对照表

| 组件 | 原代码 | 新代码 |
|------|--------|--------|
| AdminSite | `admin.AdminSite` | `unfold.admin.AdminSite` |
| ModelAdmin | `admin.ModelAdmin` | `unfold.admin.ModelAdmin` |
| UserAdmin | `auth.UserAdmin` | `unfold.UserAdmin` |
| TabularInline | `admin.TabularInline` | `unfold.admin.TabularInline` |
| StackedInline | `admin.StackedInline` | `unfold.admin.StackedInline` |
| Dashboard | 自定义 index.html | `unfold.views.DashboardView` |

---

## 四、详细实施步骤

### Phase 1：安装与基础配置 (0.5天)

#### 1.1 安装依赖

```bash
pip install django-unfold
```

#### 1.2 配置 settings.py

```python
# config/settings/base.py

INSTALLED_APPS = [
    # Unfold 必须在 django.contrib.admin 之前
    "unfold",
    "unfold.contrib.filters",    # 高级过滤器
    "unfold.contrib.forms",      # 表单增强
    "unfold.contrib.inlines",    # 内联增强
    
    "django.contrib.admin",
    # ... 其他 apps 保持不变
]

# Unfold 配置
UNFOLD = {
    "SITE_TITLE": "DjangoBlog",
    "SITE_HEADER": "DjangoBlog 管理后台",
    "SITE_SYMBOL": "blog",  # Material Symbols 图标
    "SHOW_LANGUAGES": False,
    "SHOW_VIEW_ON_SITE": True,
}
```

---

### Phase 2：迁移 AdminSite (0.5天)

#### 2.1 修改 admin_site.py

```python
# apps/core/admin/admin_site.py

from unfold.admin import AdminSite

class DjangoBlogAdminSite(AdminSite):
    """DjangoBlog 自定义后台站点"""
    
    site_header = "DjangoBlog 管理后台"
    site_title = "DjangoBlog Admin"
    index_title = "仪表盘"
    site_symbol = "blog"

admin_site = DjangoBlogAdminSite(name="admin")
```

---

### Phase 3：迁移 ModelAdmin (1天)

#### 3.1 修改 user_admin.py

```python
# apps/core/admin/user_admin.py

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin, StackedInline
from unfold.decorators import action
from .admin_site import admin_site

from apps.accounts.models import User, Profile


class ProfileInline(StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "个人资料"
    extra = 0


@admin.register(User, site=admin_site)
class CustomUserAdmin(BaseUserAdmin, ModelAdmin):
    inlines = [ProfileInline]
    list_filter_submit = True  # 过滤器提交按钮
    
    @action(description="激活所选用户")
    def activate_users(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"成功激活 {count} 个用户")
```

#### 3.2 修改 blog_admin.py

```python
# apps/core/admin/blog_admin.py

from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import RangeDateFilter
from unfold.decorators import action
from .admin_site import admin_site

from apps.blog.models import Post


@admin.register(Post, site=admin_site)
class PostAdmin(ModelAdmin):
    list_display = ["title", "author", "category", "status", "views_count", "published_at"]
    list_filter_submit = True
    list_filter = [
        ("status", admin.ChoicesFieldListFilter),
        "category",
        ("published_at", RangeDateFilter),
    ]
    search_fields = ["title", "content", "author__username"]
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ["tags"]
    
    @action(description="发布所选文章")
    def publish_posts(self, request, queryset):
        count = queryset.update(status="published")
        self.message_user(request, f"成功发布 {count} 篇文章")
    
    # TinyMCE 保留
    class Media:
        js = ("https://cdn.jsdelivr.net/npm/tinymce@7/tinymce.min.js", "js/admin-editor.js")
        css = {"all": ("css/admin-editor.css",)}
```

#### 3.3 其他文件迁移要点

每个 admin 文件只需修改 3 处：

1. **导入**：`from unfold.admin import ModelAdmin`
2. **继承**：`class XxxAdmin(ModelAdmin)`
3. **Actions**：添加 `@action(description="...")` 装饰器

---

### Phase 4：自定义仪表盘 (0.5天)

#### 4.1 创建 dashboard.py

```python
# apps/core/admin/dashboard.py

from unfold.views import DashboardView
from unfold.sections import RecentActionsSection
from apps.core.admin.admin_site import admin_site


@admin_site.register_dashboard
class Dashboard(DashboardView):
    sections = [
        # 可添加自定义统计卡片、图表等
        RecentActionsSection(),
    ]
```

---

### Phase 5：清理旧代码 (0.5天)

#### 5.1 删除文件

```bash
# 删除自定义模板（Unfold 自带）
rm templates/admin/index.html
rm templates/admin/change_form.html

# 删除自定义 CSS（大部分不再需要）
rm static/css/admin-modern.css
```

#### 5.2 简化 base_site.html

```html
<!-- templates/admin/base_site.html -->
{% extends "admin/base_site.html" %}
{% load static %}

{% block extrastyle %}
{{ block.super }}
<link rel="stylesheet" href="{% static 'admin/custom.css' %}">
{% endblock %}
```

---

## 五、工作量估算

| 阶段 | 任务 | 预估时间 | 风险 |
|------|------|----------|------|
| Phase 1 | 安装配置 | 0.5天 | 低 |
| Phase 2 | AdminSite 迁移 | 0.5天 | 低 |
| Phase 3 | ModelAdmin 迁移 | 1天 | 低 |
| Phase 4 | 仪表盘定制 | 0.5天 | 中 |
| Phase 5 | 清理测试 | 0.5天 | 低 |
| **总计** | | **3天** | |

---

## 六、验收标准

### 6.1 功能验收

- [ ] 所有 ModelAdmin 正常显示
- [ ] 列表页过滤、搜索正常
- [ ] 批量操作正常
- [ ] TinyMCE 编辑器正常
- [ ] 内联模型正常
- [ ] 仪表盘统计正常

### 6.2 UI 验收

- [ ] 现代化设计风格
- [ ] 暗色模式可切换
- [ ] 移动端响应式正常
- [ ] 图标正确显示

### 6.3 性能验收

- [ ] 页面加载 < 2s
- [ ] 无 JS 错误
- [ ] 无 CSS 冲突

---

## 七、回滚方案

如遇问题，可通过 Git 回滚：

```bash
git checkout HEAD~1 -- apps/core/admin/
git checkout HEAD~1 -- templates/admin/
git checkout HEAD~1 -- static/css/
git checkout HEAD~1 -- config/settings/base.py
pip uninstall django-unfold
```

---

## 八、参考资料

- django-unfold 官方文档：https://github.com/unfoldadmin/django-unfold
- Django Admin 文档：https://docs.djangoproject.com/en/4.2/ref/contrib/admin/
- Tailwind CSS：https://tailwindcss.com/
