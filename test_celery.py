#!/usr/bin/env python
"""测试 Celery 配置"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置 Django 设置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# 初始化 Django
import django
django.setup()

# 测试 Celery
from config.celery import app
print('[OK] Celery app created successfully')
print(f'[INFO] Broker URL: {app.conf.broker_url}')
print(f'[INFO] Result Backend: {app.conf.result_backend}')

# 测试审核策略
from moderation.strategy import get_moderation_strategy
strategy = get_moderation_strategy()
print('[OK] 审核策略引擎加载成功')

# 测试 AI 服务
from moderation.ai_service import get_moderation_service
service = get_moderation_service()
print(f'[OK] AI 审核服务加载成功 (类型: {type(service).__name__})')

# 测试用户信誉
from moderation.reputation import UserReputation
print('[OK] 用户信誉系统加载成功')

print('\n[SUCCESS] 所有组件加载成功！')
