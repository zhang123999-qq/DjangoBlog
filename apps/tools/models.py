from django.core.cache import cache
from django.db import models
from django.utils.text import slugify


class ToolConfig(models.Model):
    slug = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    is_enabled = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        verbose_name = '工具配置'
        verbose_name_plural = '工具配置'
        ordering = ['sort_order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        # 清除相关缓存
        cache.delete(f'tool_config_{self.slug}')
        cache.delete('tool_list')
        cache.delete('tool_categories')

    def __str__(self):
        return self.name
