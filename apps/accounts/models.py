from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.core.validators import validate_image_upload


class User(AbstractUser):
    email = models.EmailField(unique=True)
    nickname = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ImageField(
        upload_to="avatars/",
        max_length=255,
        validators=[validate_image_upload],
        blank=True,
        null=True,
        verbose_name="头像",
    )
    bio = models.TextField(blank=True, null=True, verbose_name="个人简介")
    website = models.URLField(blank=True, null=True, verbose_name="个人网站")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "用户资料"
        verbose_name_plural = "用户资料"

    def __str__(self):
        return f"{self.user.username} 的个人资料"


@receiver(post_save, sender=User, dispatch_uid="create_user_profile")
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """在用户创建或更新时自动创建/更新 Profile"""
    if created:
        # 创建Profile并分配随机头像
        from .avatar_utils import get_random_avatar

        profile = Profile(user=instance)
        profile.avatar = get_random_avatar()
        profile.save()
    else:
        # 确保用户有profile，没有则创建
        Profile.objects.get_or_create(user=instance)
