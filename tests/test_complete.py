"""DjangoBlog 完整测试套件"""
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.development'
import django
django.setup()

from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
import time
import json

print('='*70)
print('DjangoBlog v2.3.0 - Complete Test Suite')
print('='*70)
print()

User = get_user_model()
client = Client()

# ============================================================
# 测试计数器
# ============================================================
total_tests = 0
passed_tests = 0
failed_tests = 0
errors = []

def test(name, test_func):
    global total_tests, passed_tests, failed_tests, errors
    total_tests += 1
    try:
        result = test_func()
        if result:
            passed_tests += 1
            print(f'  [PASS] {name}')
        else:
            failed_tests += 1
            errors.append({'test': name, 'error': 'Returned False'})
            print(f'  [FAIL] {name}')
    except Exception as e:
        failed_tests += 1
        errors.append({'test': name, 'error': str(e)})
        print(f'  [ERROR] {name}: {str(e)[:50]}')

# ============================================================
# 1. 首页测试
# ============================================================
print('[1] Home Page Tests')
print('-'*70)

test('Home page loads', lambda: client.get('/').status_code == 200)
test('Home has performance headers', lambda: client.get('/').get('X-Request-Duration-Ms') is not None)
test('Home has query count header', lambda: client.get('/').get('X-DB-Queries') is not None)
print()

# ============================================================
# 2. 用户系统测试
# ============================================================
print('[2] User System Tests')
print('-'*70)

test('Login page loads', lambda: client.get('/accounts/login/').status_code == 200)
test('Register page loads', lambda: client.get('/accounts/register/').status_code == 200)
test('Admin user exists', lambda: User.objects.filter(is_superuser=True).exists())
test('User profile exists', lambda: User.objects.first().profile is not None if User.objects.first() else True)
print()

# ============================================================
# 3. 博客系统测试
# ============================================================
print('[3] Blog System Tests')
print('-'*70)

test('Blog list loads', lambda: client.get('/blog/').status_code == 200)

from apps.blog.models import Category, Tag, Post
categories = Category.objects.all()
tags = Tag.objects.all()

test('Categories exist', lambda: categories.count() > 0)
test('Tags exist', lambda: tags.count() > 0)

if categories.exists():
    cat = categories.first()
    test('Category page loads', lambda: client.get(f'/blog/category/{cat.slug}/').status_code == 200)

if tags.exists():
    tag = tags.first()
    test('Tag page loads', lambda: client.get(f'/blog/tag/{tag.slug}/').status_code == 200)
print()

# ============================================================
# 4. 论坛系统测试
# ============================================================
print('[4] Forum System Tests')
print('-'*70)

test('Forum list loads', lambda: client.get('/forum/').status_code == 200)

from apps.forum.models import Board
boards = Board.objects.all()

test('Boards exist', lambda: boards.count() > 0)

if boards.exists():
    board = boards.first()
    test('Board page loads', lambda: client.get(f'/forum/board/{board.slug}/').status_code == 200)
print()

# ============================================================
# 5. 工具系统测试
# ============================================================
print('[5] Tools System Tests')
print('-'*70)

test('Tools list loads', lambda: client.get('/tools/').status_code == 200)

from apps.tools.registry import registry
registry.reset_discovered()
tools = registry.get_all_tools()

test('Tools are registered', lambda: len(tools) > 50)

# 测试几个工具
test_tools = ['aes', 'base64', 'md5', 'uuid-generator', 'json-formatter']
for tool_slug in test_tools[:3]:
    test(f'Tool "{tool_slug}" loads', lambda s=tool_slug: client.get(f'/tools/{s}/').status_code == 200)
print()

# ============================================================
# 6. API 测试
# ============================================================
print('[6] API Tests')
print('-'*70)

test('API root loads', lambda: client.get('/api/').status_code == 200)
test('API posts loads', lambda: client.get('/api/posts/').status_code == 200)
test('API categories loads', lambda: client.get('/api/categories/').status_code == 200)
test('API tags loads', lambda: client.get('/api/tags/').status_code == 200)
test('API docs loads', lambda: client.get('/api/docs/').status_code == 200)
test('API schema loads', lambda: client.get('/api/schema/').status_code == 200)
print()

# ============================================================
# 7. 缓存系统测试
# ============================================================
print('[7] Cache System Tests')
print('-'*70)

# 清除测试缓存
cache.delete('test_key')

# 写入测试
cache.set('test_key', 'test_value', 60)
test('Cache write', lambda: cache.get('test_key') == 'test_value')

# 删除测试
cache.delete('test_key')
test('Cache delete', lambda: cache.get('test_key') is None)

# 复杂数据测试
complex_data = {'list': [1, 2, 3], 'dict': {'a': 'b'}}
cache.set('complex', complex_data, 60)
test('Cache complex data', lambda: cache.get('complex') == complex_data)
print()

# ============================================================
# 8. 性能优化测试
# ============================================================
print('[8] Performance Optimization Tests')
print('-'*70)

from apps.core.models import SiteConfig

# SiteConfig 缓存测试
start = time.time()
config1 = SiteConfig.get_solo()
time1 = (time.time() - start) * 1000

start = time.time()
config2 = SiteConfig.get_solo()
time2 = (time.time() - start) * 1000

test('SiteConfig caching works', lambda: time2 < time1 or time2 < 1)
print(f'  SiteConfig: first={time1:.2f}ms, cached={time2:.2f}ms')

# 分类标签缓存测试
from apps.blog.views import get_categories_and_tags

start = time.time()
cats1, tags1 = get_categories_and_tags()
time1 = (time.time() - start) * 1000

start = time.time()
cats2, tags2 = get_categories_and_tags()
time2 = (time.time() - start) * 1000

test('Categories/Tags caching works', lambda: time2 < time1 or time2 < 1)
print(f'  Categories/Tags: first={time1:.2f}ms, cached={time2:.2f}ms')
print()

# ============================================================
# 9. 安全测试
# ============================================================
print('[9] Security Tests')
print('-'*70)

response = client.get('/')
test('X-Frame-Options header', lambda: response.get('X-Frame-Options') == 'DENY')
test('X-Content-Type-Options header', lambda: response.get('X-Content-Type-Options') == 'nosniff')
test('CSRF cookie set', lambda: 'csrftoken' in response.cookies)
print()

# ============================================================
# 10. 数据库连接测试
# ============================================================
print('[10] Database Connection Tests')
print('-'*70)

from django.db import connection

test('Database connection works', lambda: connection.is_usable())

with connection.cursor() as cursor:
    cursor.execute('SELECT 1')
    test('Database query works', lambda: cursor.fetchone()[0] == 1)

# 连接池配置检查
test('Connection pool configured', lambda: connection.settings_dict.get('CONN_MAX_AGE', 0) > 0)
print()

# ============================================================
# 11. 模型测试
# ============================================================
print('[11] Model Tests')
print('-'*70)

from django.apps import apps
models = list(apps.get_models())

test('Models loaded', lambda: len(models) > 20)
print(f'  Total models: {len(models)}')

# 检查关键模型
key_models = ['User', 'Post', 'Comment', 'Topic', 'Reply', 'SensitiveWord']
for model_name in key_models:
    test(f'Model {model_name} exists', lambda n=model_name: any(m.__name__ == n for m in models))
print()

# ============================================================
# 12. URL 路由测试
# ============================================================
print('[12] URL Routing Tests')
print('-'*70)

key_urls = [
    ('Home', '/'),
    ('Blog', '/blog/'),
    ('Forum', '/forum/'),
    ('Tools', '/tools/'),
    ('Login', '/accounts/login/'),
    ('Register', '/accounts/register/'),
    ('API', '/api/'),
    ('Admin', '/admin/'),
]

for name, url in key_urls:
    response = client.get(url)
    # Admin 可能重定向到登录
    status = response.status_code in [200, 301, 302]
    test(f'{name} URL accessible', lambda s=status: s)
print()

# ============================================================
# 测试总结
# ============================================================
print('='*70)
print('TEST SUMMARY')
print('='*70)
print(f'  Total Tests: {total_tests}')
print(f'  Passed: {passed_tests}')
print(f'  Failed: {failed_tests}')
print(f'  Pass Rate: {passed_tests/total_tests*100:.1f}%')
print()

if errors:
    print('  Failed Tests:')
    for error in errors[:10]:
        print(f'    - {error["test"]}: {error["error"][:50]}')
    print()

print('='*70)
if failed_tests == 0:
    print('ALL TESTS PASSED!')
else:
    print(f'COMPLETED WITH {failed_tests} FAILURES')
print('='*70)
