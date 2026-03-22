from django.db import models
from django.core.cache import cache


class SiteConfig(models.Model):
    site_name = models.CharField(max_length=255, default='Django 综合网站')
    site_title = models.CharField(max_length=255, default='Django 综合网站')
    site_description = models.TextField(default='这是一个基于 Django 的综合网站')
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    is_installed = models.BooleanField(default=False)
    allow_registration = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '网站配置'
        verbose_name_plural = '网站配置'

    def __str__(self):
        return self.site_name

    @classmethod
    def get_solo(cls):
        """获取或创建唯一的 SiteConfig 实例（带缓存）"""
        cache_key = 'site_config_solo'
        instance = cache.get(cache_key)
        
        if instance is None:
            instance, created = cls.objects.get_or_create(pk=1)
            # 缓存 5 分钟
            cache.set(cache_key, instance, 300)
        
        return instance
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # 更新缓存
        cache.set('site_config_solo', self, 300)