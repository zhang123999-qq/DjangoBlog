"""
多级审核策略引擎

支持：
- 基于用户信誉的智能审核策略
- 敏感词 + AI 双重检测
- 自动决策 / 人工审核分流
"""

import logging
from typing import Tuple, Dict, Any, Optional
from django.conf import settings
from django.contrib.auth import get_user_model

from .utils import check_sensitive_content
from .ai_service import get_moderation_service
from .reputation import UserReputation

User = get_user_model()
logger = logging.getLogger(__name__)


class ModerationStrategy:
    """审核策略引擎"""

    # 审核结果常量
    APPROVED = 'approved'  # 自动通过
    REJECTED = 'rejected'  # 自动拒绝
    PENDING = 'pending'  # 待人工审核
    SENSITIVE = 'sensitive'  # 敏感词命中
    AI_REJECTED = 'ai_rejected'  # AI 拒绝
    AI_PENDING = 'ai_pending'  # AI 不确定

    def __init__(self):
        self.moderation_service = get_moderation_service()
        self.mode = getattr(settings, 'MODERATION_MODE', 'hybrid')
        self.ai_threshold = getattr(settings, 'MODERATION_AI_THRESHOLD', 0.8)

    def get_review_strategy(self, user, content: str) -> Tuple[str, Dict[str, Any]]:
        """获取审核策略

        根据用户信誉和内容特征，决定审核策略

        Args:
            user: 用户对象
            content: 内容文本

        Returns:
            tuple: (策略名称, 审核详情)
                - 策略名称: 'auto_publish' / 'manual_review' / 'sensitive_review' / etc.
                - 审核详情: 包含敏感词、AI 结果等信息的字典
        """
        details = {
            'user_level': 'normal',
            'has_sensitive': False,
            'sensitive_words': [],
            'ai_result': None,
            'ai_details': None,
            'final_decision': None,
        }

        # 1. 获取用户信誉等级
        if user.is_authenticated:
            reputation = UserReputation.get_or_create_for_user(user)
            details['user_level'] = reputation.level
        else:
            # 匿名用户，默认普通等级
            details['user_level'] = 'normal'

        # 2. 高信誉用户：自动发布
        if details['user_level'] == 'trusted':
            details['final_decision'] = self.APPROVED
            return 'auto_publish', details

        # 3. 低信誉用户：强制人工审核
        if details['user_level'] == 'low':
            details['final_decision'] = self.PENDING
            return 'manual_review', details

        # 4. 普通用户：敏感词 + AI 双重检测

        # 4.1 敏感词快速检测
        has_sensitive, sensitive_words = check_sensitive_content(content)
        details['has_sensitive'] = has_sensitive
        details['sensitive_words'] = sensitive_words

        if has_sensitive:
            details['final_decision'] = self.SENSITIVE
            return 'sensitive_review', details

        # 4.2 AI 语义审核
        ai_result, ai_details = self.moderation_service.moderate_text(content)
        details['ai_result'] = ai_result
        details['ai_details'] = ai_details

        if ai_result == 'approved':
            details['final_decision'] = self.APPROVED
            return 'auto_publish', details

        elif ai_result == 'rejected':
            details['final_decision'] = self.AI_REJECTED
            return 'ai_rejected', details

        elif ai_result == 'pending':
            details['final_decision'] = self.PENDING
            return 'manual_review', details

        else:
            # AI 出错，保守处理
            details['final_decision'] = self.PENDING
            return 'manual_review', details

    def moderate_content(self, user, content: str, content_type: str = 'text') -> Dict[str, Any]:
        """审核内容

        综合敏感词、AI、用户信誉给出最终审核意见

        Args:
            user: 用户对象
            content: 内容文本
            content_type: 内容类型 (text/image/etc.)

        Returns:
            dict: 审核结果
                {
                    'status': 'approved' / 'rejected' / 'pending',
                    'strategy': 策略名称,
                    'details': 审核详情,
                    'message': 审核意见说明,
                }
        """
        strategy, details = self.get_review_strategy(user, content)

        result = {
            'status': self.PENDING,
            'strategy': strategy,
            'details': details,
            'message': '',
        }

        # 根据策略设置最终状态
        if strategy == 'auto_publish':
            result['status'] = self.APPROVED
            result['message'] = '自动审核通过'

        elif strategy == 'sensitive_review':
            result['status'] = self.PENDING
            words = ', '.join(details['sensitive_words'][:5])
            result['message'] = f'命中敏感词: {words}'

        elif strategy == 'ai_rejected':
            result['status'] = self.REJECTED
            if details['ai_details']:
                violations = [v['type'] for v in details['ai_details']]
                result['message'] = f'AI 识别违规: {", ".join(violations)}'
            else:
                result['message'] = 'AI 识别违规内容'

        elif strategy == 'manual_review':
            result['status'] = self.PENDING
            if details['ai_result'] == 'pending':
                result['message'] = 'AI 审核不确定，需人工判断'
            else:
                result['message'] = '需人工审核'

        else:
            result['status'] = self.PENDING
            result['message'] = '待审核'

        return result

    def moderate_image(self, user, image_path: Optional[str] = None, image_url: Optional[str] = None) -> Dict[str, Any]:
        """审核图片

        Args:
            user: 用户对象
            image_path: 图片路径
            image_url: 图片 URL

        Returns:
            dict: 审核结果
        """
        details = {
            'user_level': 'normal',
            'ai_result': None,
            'ai_details': None,
        }

        # 获取用户信誉
        if user.is_authenticated:
            reputation = UserReputation.get_or_create_for_user(user)
            details['user_level'] = reputation.level

        # 高信誉用户自动通过
        if details['user_level'] == 'trusted':
            return {
                'status': self.APPROVED,
                'strategy': 'auto_publish',
                'details': details,
                'message': '高信誉用户，自动通过',
            }

        # AI 图片审核
        if image_path:
            ai_result, ai_details = self.moderation_service.moderate_image(image_path)
        elif image_url:
            ai_result, ai_details = self.moderation_service.moderate_image_url(image_url)
        else:
            return {
                'status': self.PENDING,
                'strategy': 'manual_review',
                'details': details,
                'message': '无图片内容',
            }

        details['ai_result'] = ai_result
        details['ai_details'] = ai_details

        if ai_result == 'approved':
            return {
                'status': self.APPROVED,
                'strategy': 'ai_approved',
                'details': details,
                'message': 'AI 审核通过',
            }

        elif ai_result == 'rejected':
            return {
                'status': self.REJECTED,
                'strategy': 'ai_rejected',
                'details': details,
                'message': 'AI 识别违规图片',
            }

        else:
            return {
                'status': self.PENDING,
                'strategy': 'manual_review',
                'details': details,
                'message': '需人工审核',
            }


# 全局实例
_moderation_strategy = None


def get_moderation_strategy():
    """获取审核策略实例"""
    global _moderation_strategy
    if _moderation_strategy is None:
        _moderation_strategy = ModerationStrategy()
    return _moderation_strategy
