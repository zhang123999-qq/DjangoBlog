"""moderation 模块最小冒烟测试（P2）。"""

import pytest
from django.contrib.auth import get_user_model

from moderation.baidu_moderation import get_moderation_summary
from moderation.models import SensitiveWord
from moderation.reputation import UserReputation
from moderation.strategy import ModerationStrategy
from moderation.utils import check_sensitive_content


@pytest.mark.django_db
def test_sensitive_word_detection_smoke():
    SensitiveWord.objects.create(word='违禁词')

    has_sensitive, hit_words = check_sensitive_content('这是一段包含违禁词的文本')

    assert has_sensitive is True
    assert '违禁词' in hit_words


@pytest.mark.django_db
def test_user_reputation_level_boundaries_smoke():
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username='rep_user',
        email='rep_user@example.com',
        password='Pass12345!'
    )
    reputation = UserReputation.get_or_create_for_user(user)

    reputation.score = 85
    reputation.save(update_fields=['score'])
    assert reputation.level == 'trusted'

    reputation.score = 50
    reputation.save(update_fields=['score'])
    assert reputation.level == 'normal'

    reputation.score = 10
    reputation.save(update_fields=['score'])
    assert reputation.level == 'low'


@pytest.mark.django_db
def test_moderation_strategy_trusted_user_auto_publish_smoke():
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username='trusted_user',
        email='trusted_user@example.com',
        password='Pass12345!'
    )
    reputation = UserReputation.get_or_create_for_user(user)
    reputation.score = 90
    reputation.save(update_fields=['score'])

    strategy = ModerationStrategy()
    result = strategy.moderate_content(user, '普通内容')

    assert result['strategy'] == 'auto_publish'
    assert result['status'] == 'approved'


def test_get_moderation_summary_rejected_smoke():
    summary = get_moderation_summary('rejected', {
        'violations': [{'type': '广告'}],
    })

    assert '违规' in summary
    assert '广告' in summary
