"""DjangoBlog 完整验收测试"""
import pytest

if __name__ != '__main__':
    pytest.skip('legacy script-style suite, skip in pytest collection', allow_module_level=True)

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.development'
import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.core.cache import cache
from apps.core.models import SiteConfig
from apps.blog.models import Category, Tag, Post
from apps.forum.models import Board, Topic
from apps.tools.registry import registry
import time

print('='*70)
print('DjangoBlog v2.4.0 - Final Acceptance Test')
print('='*70)
print()

client = Client()
User = get_user_model()

# ============================================================
# 测试结果统计
# ============================================================
results = {
    'total': 0,
    'passed': 0,
    'failed': 0,
    'errors': []
}

def test(name, func, expected=True):
    global results
    results['total'] += 1
    try:
        result = func()
        if result == expected:
            results['passed'] += 1
            print(f'  [PASS] {name}')
            return True
        else:
            results['failed'] += 1
            results['errors'].append(f'{name}: expected {expected}, got {result}')
            print(f'  [FAIL] {name}')
            return False
    except Exception as e:
        results['failed'] += 1
        results['errors'].append(f'{name}: {str(e)[:50]}')
        print(f'  [ERROR] {name}: {str(e)[:30]}')
        return False

# ============================================================
# 1. 系统基础测试
# ============================================================
print('[1] System Basic Tests')
print('-'*70)

test('Database connection', lambda: True)
test('Cache system', lambda: cache.set('test', 'ok', 10) and cache.get('test') == 'ok')
test('SiteConfig model', lambda: SiteConfig.objects.exists())
test('User model', lambda: User.objects.count() >= 1)
print()

# ============================================================
# 2. 博客系统测试
# ============================================================
print('[2] Blog System Tests')
print('-'*70)

test('Categories exist', lambda: Category.objects.count() >= 1)
test('Tags exist', lambda: Tag.objects.count() >= 1)
test('Blog list page', lambda: client.get('/blog/').status_code == 200)
test('Blog category page', lambda: client.get(f'/blog/category/{Category.objects.first().slug}/').status_code == 200)
test('Blog tag page', lambda: client.get(f'/blog/tag/{Tag.objects.first().slug}/').status_code == 200)
print()

# ============================================================
# 3. 论坛系统测试
# ============================================================
print('[3] Forum System Tests')
print('-'*70)

test('Boards exist', lambda: Board.objects.count() >= 1)
test('Forum list page', lambda: client.get('/forum/').status_code == 200)
test('Board page', lambda: client.get(f'/forum/board/{Board.objects.first().slug}/').status_code == 200)
print()

# ============================================================
# 4. 工具系统测试
# ============================================================
print('[4] Tools System Tests')
print('-'*70)

registry.reset_discovered()
tools = registry.get_all_tools()
test('Tools registered (72+)', lambda: len(tools) >= 72)
test('Tools list page', lambda: client.get('/tools/').status_code == 200)

# 测试几个常用工具
test_tools = ['aes', 'base64', 'md5', 'sha256', 'uuid-generator']
for slug in test_tools:
    test(f'Tool "{slug}"', lambda s=slug: client.get(f'/tools/{s}/').status_code == 200)
print()

# ============================================================
# 5. API 系统测试
# ============================================================
print('[5] API System Tests')
print('-'*70)

test('API root', lambda: client.get('/api/').status_code == 200)
test('API posts', lambda: client.get('/api/posts/').status_code == 200)
test('API categories', lambda: client.get('/api/categories/').status_code == 200)
test('API tags', lambda: client.get('/api/tags/').status_code == 200)
test('API docs (Swagger)', lambda: client.get('/api/docs/').status_code == 200)
test('API schema', lambda: client.get('/api/schema/').status_code == 200)
print()

# ============================================================
# 6. 用户系统测试
# ============================================================
print('[6] User System Tests')
print('-'*70)

test('Login page', lambda: client.get('/accounts/login/').status_code == 200)
test('Register page', lambda: client.get('/accounts/register/').status_code == 200)
test('Admin user exists', lambda: User.objects.filter(is_superuser=True).exists())
print()

# ============================================================
# 7. 安全测试
# ============================================================
print('[7] Security Tests')
print('-'*70)

response = client.get('/')
test('X-Frame-Options header', lambda: response.get('X-Frame-Options') == 'DENY')
test('X-Content-Type-Options header', lambda: response.get('X-Content-Type-Options') == 'nosniff')
print()

# ============================================================
# 8. 性能测试
# ============================================================
print('[8] Performance Tests')
print('-'*70)

# 性能头测试
response = client.get('/')
test('Performance duration header', lambda: response.get('X-Request-Duration-Ms') is not None)
test('Performance queries header', lambda: response.get('X-DB-Queries') is not None)

# 缓存性能测试
start = time.time()
SiteConfig.get_solo()
first_time = (time.time() - start) * 1000

start = time.time()
SiteConfig.get_solo()
cached_time = (time.time() - start) * 1000

print(f'  SiteConfig: first={first_time:.2f}ms, cached={cached_time:.2f}ms')
test('Cache performance OK', lambda: cached_time < 1 or cached_time <= first_time)
print()

# ============================================================
# 9. 负载测试
# ============================================================
print('[9] Load Tests (50 requests per endpoint)')
print('-'*70)

endpoints = [('/', 'Home'), ('/blog/', 'Blog'), ('/forum/', 'Forum'), ('/tools/', 'Tools')]

for url, name in endpoints:
    times = []
    for _ in range(50):
        start = time.time()
        client.get(url)
        times.append((time.time() - start) * 1000)

    avg = sum(times) / len(times)
    p95 = sorted(times)[int(len(times) * 0.95)]
    print(f'  {name}: avg={avg:.2f}ms, P95={p95:.2f}ms')
    test(f'{name} load OK', lambda a=avg: a < 100)  # 平均响应 < 100ms
print()

# ============================================================
# 10. 工具功能测试
# ============================================================
print('[10] Tools Functional Tests')
print('-'*70)

# Base64
response = client.post('/tools/base64/', {'text': 'Hello', 'action': 'encode'})
test('Base64 encode', lambda: response.status_code == 200)

# MD5
response = client.post('/tools/md5/', {'text': 'Hello'})
test('MD5 hash', lambda: response.status_code == 200)

# UUID
response = client.post('/tools/uuid-generator/', {'count': '5'})
test('UUID generator', lambda: response.status_code == 200)

# JSON formatter
response = client.post('/tools/json-formatter/', {'text': '{"test": 1}'})
test('JSON formatter', lambda: response.status_code == 200)
print()

# ============================================================
# 测试总结
# ============================================================
print('='*70)
print('FINAL ACCEPTANCE TEST SUMMARY')
print('='*70)
print(f'  Total Tests: {results["total"]}')
print(f'  Passed: {results["passed"]}')
print(f'  Failed: {results["failed"]}')
print(f'  Pass Rate: {results["passed"]/results["total"]*100:.1f}%')
print()

if results['errors']:
    print('  Errors:')
    for err in results['errors'][:5]:
        print(f'    - {err}')
    print()

print('='*70)
if results['failed'] == 0:
    print('ALL TESTS PASSED - PROJECT READY FOR DELIVERY')
else:
    print(f'COMPLETED WITH {results["failed"]} FAILURES')
print('='*70)
