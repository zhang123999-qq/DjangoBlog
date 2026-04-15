"""
网站配置 Admin
"""

from django.contrib import admin, messages
from django.utils.html import format_html
from .admin_site import admin_site

from apps.core.models import SiteConfig


@admin.register(SiteConfig, site=admin_site)
class SiteConfigAdmin(admin.ModelAdmin):
    """网站配置管理"""

    list_display = ["site_name", "show_icp", "show_gongan_beian", "site_author", "is_installed", "created_at"]
    fieldsets = (
        (
            "网站信息",
            {
                "fields": (
                    ("site_name", "site_title"),
                    "site_description",
                    "site_author",
                    "logo",
                ),
            },
        ),
        (
            "备案信息",
            {
                "fields": ("site_icp", "site_gongan_beian"),
                "description": (
                    "💡 **ICP 备案**：填写备案号，保存后页脚自动显示。留空则隐藏。"
                    "示例：豫ICP备20260102345号-1"
                    "  |  **公安联网备案**：只需输入备案编号部分（如 11010502030001），"
                    "下方按钮会自动补全格式。"
                ),
            },
        ),
        (
            "系统设置",
            {
                "fields": ("is_installed", "allow_registration"),
                "classes": ("collapse",),
            },
        ),
    )

    change_form_template = "admin/core/change_form_siteconfig.html"

    @admin.display(description="ICP 备案号", ordering="site_icp")
    def show_icp(self, obj):
        if obj.site_icp:
            return format_html(
                '<a href="https://beian.miit.gov.cn/" target="_blank" '
                'style="color:#10b981;text-decoration:underline;">{}</a>',
                obj.site_icp,
            )
        return format_html('<span style="color:#999;">未设置</span>')

    @admin.display(description="公安联网备案号", ordering="site_gongan_beian")
    def show_gongan_beian(self, obj):
        if obj.site_gongan_beian:
            link = obj.gongan_beian_link
            return format_html(
                '<a href="{}" target="_blank" ' 'style="color:#3b82f6;text-decoration:underline;">{}</a>',
                link,
                obj.site_gongan_beian,
            )
        return format_html('<span style="color:#999;">未设置</span>')

    def save_model(self, request, obj, form, change):
        """保存时自动清除缓存，公安备案号格式补全由 Model.save() 处理"""
        super().save_model(request, obj, form, change)
        from django.core.cache import cache

        cache.delete("site_config_solo")

        # 消息提示
        msgs = []
        if obj.site_icp:
            msgs.append(f"✅ ICP 备案号已保存为「{obj.site_icp}」")
        if obj.site_gongan_beian:
            msgs.append(f"🛡️ 公安联网备案号已保存为「{obj.site_gongan_beian}」")
        if not msgs:
            self.message_user(request, "⚠️ 备案号为空，备案信息已隐藏。", messages.WARNING)
        else:
            self.message_user(request, "，".join(msgs) + "，页脚自动生效。", messages.SUCCESS)

    def has_add_permission(self, request):
        if self.model.objects.count() >= 1:
            return False
        return super().has_add_permission(request)
