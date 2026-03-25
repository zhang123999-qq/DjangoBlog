"""DjangoBlog 功能测试脚本"""
import pytest

if __name__ != '__main__':
    pytest.skip('legacy script-style suite, skip in pytest collection', allow_module_level=True)

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.development'
import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

print('='*60)
print('DjangoBlog v2.3.0 - Functional Test')
print('='*60)
print()

User = get_user_model()
client = Client()

# 测试结果
passed = 0
failed = 0

def test(name, url, expected_status=200):
    global passed, failed
    try:
        response = client.get(url)
        if response.status_code == expected_status:
            passed += 1
            print(f'[PASS] {name} - {response.status_code}')
        else:
            failed += 1
            print(f'[FAIL] {name} - Expected {expected_status}, got {response.status_code}')
    except Exception as e:
        failed += 1
        print(f'[ERROR] {name} - {e}')

print('[Testing Public Pages]')
print('-'*40)
test('Home Page', '/')
test('Blog List', '/blog/')
test('Forum List', '/forum/')
test('Tools List', '/tools/')
test('Login Page', '/accounts/login/')
test('Register Page', '/accounts/register/')
print()

print('[Testing API Endpoints]')
print('-'*40)
test('API Root', '/api/')
test('API Posts', '/api/posts/')
test('API Categories', '/api/categories/')
test('API Tags', '/api/tags/')
test('API Docs (Swagger)', '/api/docs/')
print()

print('[Testing Performance Headers]')
print('-'*40)
response = client.get('/')
print(f'  X-Request-Duration-Ms: {response.get("X-Request-Duration-Ms", "N/A")}')
print(f'  X-DB-Queries: {response.get("X-DB-Queries", "N/A")}')
print(f'  X-DB-Time-Ms: {response.get("X-DB-Time-Ms", "N/A")}')
print()

print('[Testing Cache]')
print('-'*40)
from django.core.cache import cache
import time
start = time.time()
cache.set('test_key', 'test_value', 10)
value = cache.get('test_key')
elapsed = (time.time() - start) * 1000
print(f'  Cache write/read: {elapsed:.2f}ms')
print(f'  Value match: {value == "test_value"}')
print()

print('[Testing Database]')
print('-'*40)
from django.db import connection
import time
start = time.time()
with connection.cursor() as cursor:
    cursor.execute('SELECT COUNT(*) FROM accounts_user')
    count = cursor.fetchone()[0]
elapsed = (time.time() - start) * 1000
print(f'  Query time: {elapsed:.2f}ms')
print(f'  User count: {count}')
print()

print('='*60)
print(f'Results: {passed} passed, {failed} failed')
print('='*60)
