"""DjangoBlog 工具功能测试"""
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.development'
import django
django.setup()

from django.test import Client
import json

print('='*70)
print('DjangoBlog v2.3.0 - Tools Functional Test')
print('='*70)
print()

client = Client()

# 测试结果
results = {'passed': 0, 'failed': 0, 'tests': []}

def test_tool(name, slug, post_data=None, expected_status=200):
    global results
    try:
        if post_data:
            response = client.post(f'/tools/{slug}/', post_data)
        else:
            response = client.get(f'/tools/{slug}/')
        
        if response.status_code == expected_status:
            results['passed'] += 1
            print(f'  [PASS] {name}')
            return response
        else:
            results['failed'] += 1
            print(f'  [FAIL] {name} - Expected {expected_status}, got {response.status_code}')
            return None
    except Exception as e:
        results['failed'] += 1
        print(f'  [ERROR] {name} - {str(e)[:50]}')
        return None

# ============================================================
# 编码工具测试
# ============================================================
print('[1] Encoding Tools')
print('-'*70)

test_tool('Base64 Encode', 'base64', {'text': 'Hello World', 'action': 'encode'})
test_tool('URL Encode', 'url-encode', {'text': 'Hello World', 'action': 'encode'})
test_tool('HTML Entity', 'html-entity', {'text': '<script>alert(1)</script>', 'action': 'encode'})
print()

# ============================================================
# 加密工具测试
# ============================================================
print('[2] Encryption Tools')
print('-'*70)

test_tool('MD5 Hash', 'md5', {'text': 'Hello World'})
test_tool('SHA256 Hash', 'sha256', {'text': 'Hello World'})
test_tool('AES Encrypt', 'aes', {'text': 'Hello World', 'key': 'secretkey123', 'action': 'encrypt'})
print()

# ============================================================
# 生成工具测试
# ============================================================
print('[3] Generator Tools')
print('-'*70)

test_tool('UUID Generator', 'uuid-generator', {'count': '5'})
test_tool('Password Generator', 'password-generator', {'length': '16'})
test_tool('QR Code', 'qr-code', {'text': 'https://example.com'})
print()

# ============================================================
# 文本工具测试
# ============================================================
print('[4] Text Tools')
print('-'*70)

test_tool('JSON Formatter', 'json-formatter', {'text': '{"name":"test"}'})
test_tool('Text Diff', 'text-diff', {'text1': 'Hello', 'text2': 'World'})
test_tool('Word Counter', 'word-counter', {'text': 'Hello World'})
print()

# ============================================================
# 数据工具测试
# ============================================================
print('[5] Data Tools')
print('-'*70)

test_tool('Timestamp Converter', 'timestamp-converter', {'timestamp': '1609459200'})
test_tool('Color Picker', 'color-picker', {'hex': '#FF5733'})
test_tool('Cron Parser', 'cron-parser', {'expression': '0 0 * * *'})
print()

# ============================================================
# 网络工具测试
# ============================================================
print('[6] Network Tools')
print('-'*70)

# 这些工具可能需要网络连接，所以只测试页面加载
test_tool('IP Lookup', 'ip-lookup', expected_status=200)
test_tool('User Agent Parser', 'user-agent-parser', expected_status=200)
print()

# ============================================================
# 图片工具测试
# ============================================================
print('[7] Image Tools')
print('-'*70)

test_tool('Color Picker', 'color-picker', expected_status=200)
print()

# ============================================================
# 安全工具测试
# ============================================================
print('[8] Security Tools')
print('-'*70)

test_tool('JWT Decoder', 'jwt-decoder', {'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c'})
test_tool('SQL Injection Check', 'sql-injection-check', {'text': "SELECT * FROM users WHERE id='1' OR '1'='1'"})
print()

# ============================================================
# 时间工具测试
# ============================================================
print('[9] Time Tools')
print('-'*70)

test_tool('Timestamp Converter', 'timestamp-converter', expected_status=200)
print()

# ============================================================
# 测试总结
# ============================================================
print('='*70)
print('TOOLS TEST SUMMARY')
print('='*70)
print(f'  Total Tests: {results["passed"] + results["failed"]}')
print(f'  Passed: {results["passed"]}')
print(f'  Failed: {results["failed"]}')
print(f'  Pass Rate: {results["passed"]/(results["passed"]+results["failed"])*100:.1f}%')
print('='*70)
