"""
用户信誉系统

管理用户信誉分数，支持：
- 自动计算信誉等级
- 信誉分增减
- 历史记录追踪
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class UserReputation(models.Model):
    """用户信誉系统"""

    REPUTATION_LEVEL_CHOICES = (
        ("trusted", "高信誉"),  # 自动发布
        ("normal", "正常"),  # 敏感词检测
        ("low", "低信誉"),  # 人工审核
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reputation", verbose_name="用户"
    )

    # 信誉分数 (0-100)
    score = models.IntegerField(default=50, verbose_name="信誉分")

    # 历史统计
    total_posts = models.IntegerField(default=0, verbose_name="总发帖数")
    approved_count = models.IntegerField(default=0, verbose_name="通过数")
    rejected_count = models.IntegerField(default=0, verbose_name="拒绝数")
    report_count = models.IntegerField(default=0, verbose_name="被举报次数")

    # 连续无违规天数
    clean_days = models.IntegerField(default=0, verbose_name="连续无违规天数")
    last_clean_check = models.DateField(auto_now_add=True, verbose_name="上次检查日期")

    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "用户信誉"
        verbose_name_plural = "用户信誉"

    def __str__(self):
        return f"{self.user.username} - {self.score}分 ({self.get_level_display()})"

    @property
    def level(self):
        """获取信誉等级"""
        if self.score >= 80:
            return "trusted"
        elif self.score >= 30:
            return "normal"
        else:
            return "low"

    @property
    def level_display(self):
        """获取信誉等级显示名称"""
        return dict(self.REPUTATION_LEVEL_CHOICES).get(self.level, "正常")

    def update_score(self, delta, reason=""):
        """更新信誉分

        Args:
            delta: 分数变化（正数增加，负数减少）
            reason: 原因说明

        Returns:
            int: 更新后的分数
        """
        from django.conf import settings as django_settings

        old_score = self.score
        min_score = getattr(django_settings, "REPUTATION_MIN_SCORE", 0)
        max_score = getattr(django_settings, "REPUTATION_MAX_SCORE", 100)

        self.score = max(min_score, min(max_score, self.score + delta))
        self.save()

        # 记录日志
        ReputationLog.objects.create(
            user_reputation=self,
            action="score_change",
            old_score=old_score,
            new_score=self.score,
            delta=delta,
            reason=reason,
        )

        return self.score

    def increment_posts(self, approved=True):
        """增加发帖统计

        Args:
            approved: 是否通过审核
        """
        self.total_posts += 1
        if approved:
            self.approved_count += 1
        else:
            self.rejected_count += 1
        self.save()

    def increment_reports(self):
        """增加被举报次数"""
        self.report_count += 1
        self.save()

    def check_clean_days(self):
        """检查连续无违规天数"""
        today = timezone.now().date()

        if self.last_clean_check < today:
            days_diff = (today - self.last_clean_check).days

            # 如果没有新的违规，增加连续天数
            if self.rejected_count == 0 and self.report_count == 0:
                self.clean_days += days_diff
            else:
                self.clean_days = 0

            self.last_clean_check = today
            self.save()

        # 连续7天无违规，奖励5分
        if self.clean_days >= 7 and self.clean_days % 7 == 0:
            from django.conf import settings as django_settings

            bonus = getattr(django_settings, "REPUTATION_WEEKLY_BONUS", 5)
            self.update_score(bonus, f"连续{self.clean_days}天无违规")

        return self.clean_days

    @classmethod
    def get_or_create_for_user(cls, user):
        """获取或创建用户信誉记录"""
        reputation, created = cls.objects.get_or_create(user=user)
        return reputation


class ReputationLog(models.Model):
    """信誉变化日志"""

    ACTION_CHOICES = (
        ("score_change", "分数变化"),
        ("level_change", "等级变化"),
        ("bonus", "奖励"),
        ("penalty", "惩罚"),
        ("manual", "手动调整"),
    )

    user_reputation = models.ForeignKey(
        UserReputation, on_delete=models.CASCADE, related_name="logs", verbose_name="用户信誉"
    )

    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="操作类型")
    old_score = models.IntegerField(verbose_name="原分数")
    new_score = models.IntegerField(verbose_name="新分数")
    delta = models.IntegerField(verbose_name="变化量")
    reason = models.CharField(max_length=200, blank=True, verbose_name="原因")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "信誉日志"
        verbose_name_plural = "信誉日志"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_reputation.user.username} {self.get_action_display()} {self.old_score}→{self.new_score}"
