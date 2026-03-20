from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile


class ProfileInline(admin.StackedInline):
    """在 User 管理页面中内联显示 Profile"""
    model = Profile
    can_delete = False
    verbose_name_plural = '个人资料'


class CustomUserAdmin(UserAdmin):
    """自定义 User 管理"""
    inlines = [ProfileInline]
    list_display = ['username', 'email', 'nickname', 'is_staff', 'is_active', 'date_joined', 'last_login']
    list_filter = ['is_staff', 'is_active', 'is_superuser']
    search_fields = ['username', 'email', 'nickname']
    ordering = ['-date_joined']


class ProfileAdmin(admin.ModelAdmin):
    """个人资料管理"""
    list_display = ['user', 'bio', 'website']
    search_fields = ['user__username', 'user__email', 'bio', 'website']
    ordering = ['user__username']


admin.site.register(User, CustomUserAdmin)
admin.site.register(Profile, ProfileAdmin)
