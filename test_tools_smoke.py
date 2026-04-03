"""Test smoke: verify tool box optimization"""
import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from apps.tools.registry import registry
passed = 0
failed = 0

def ck(name, cond):
    global passed, failed
    if cond:
        print(f"  [OK] {name}")
        passed += 1
    else:
        print(f"  [FAIL] {name}")
        failed += 1

print("=" * 50)
print("Tool Box Smoke Test")
print("=" * 50)

# 1. Verify deleted tools are gone
print("\n[1] Deleted tools should not exist")
deleted = ['ip-detector', 'json-formatter', 'poem-generator', 'famous-quote', 'chinese-counter']
for slug in deleted:
    tool = registry.get_tool(slug)
    ck(f"{slug} deleted", tool is None)

# 2. Merged tools exist
print("\n[2] Merged tools should exist")
ip_tool = registry.get_tool('ip-query')
ck("ip-query exists", ip_tool is not None)
ck("ip-query slug correct", ip_tool and ip_tool.slug == 'ip-query')

insp = registry.get_tool('inspiration')
ck("inspiration exists", insp is not None)
ck("inspiration slug correct", insp and insp.slug == 'inspiration')

tc = registry.get_tool('text-counter')
ck("text-counter exists", tc is not None)
ck("text-counter slug correct", tc and tc.slug == 'text-counter')

# 3. Text counter stats
print("\n[3] Text counter (merged) functionality")
text = "Hello world! This is a test."
form = tc.get_form({'text': text})
ck("form valid", form.is_valid())
if form.is_valid():
    result = tc.handle(None, form)
    ck(f"total_chars={result.get('total_chars', '?')}", result.get('total_chars', 0) == len(text))
    ck(f"word_count={result.get('word_count', '?')}", result.get('word_count', 0) == 6)
    ck(f"line_count={result.get('line_count', '?')}", result.get('line_count', 0) == 1)

# 4. Inspiration tool
print("\n[4] Inspiration tool functionality")
form = insp.get_form({'content_type': 'poem', 'category': 'all', 'count': 2})
ck("form valid", form.is_valid())
if form.is_valid():
    result = insp.handle(None, form)
    poems = result.get('poems', [])
    ck(f"returned {len(poems)} poems", len(poems) > 0)
    titles = [p['title'] for p in poems]
    ck("no duplicate poems", len(titles) == len(set(titles)))

# 5. Security fixes
print("\n[5] Security fixes")
import importlib, inspect
mod = importlib.import_module('apps.tools.tool_modules.password_gen')
src = inspect.getsource(mod)
ck("password uses secrets", "import secrets" in src)
ck("no random import in password_gen", "import random" not in src)

crypto_mod = importlib.import_module('apps.tools.tool_modules.text_crypto_tool')
src = inspect.getsource(crypto_mod)
ck("crypto warns about safety", "娱乐" in src or "混淆" in src or "不具备" in src)

weather_mod = importlib.import_module('apps.tools.tool_modules.weather_tool')
src = inspect.getsource(weather_mod)
ck("weather has wttr.in fallback", "wttr.in" in src)

# 6. Total count
print("\n[6] Total count")
all_tools = registry.get_all_tools()
ck(f"total tools = {len(all_tools)} (expect 68)", len(all_tools) == 68)

# Summary
print("\n" + "=" * 50)
print(f"Result: {passed} passed, {failed} failed, total {passed + failed}")
if failed == 0:
    print("ALL TESTS PASSED!")
else:
    print(f"WARNING: {failed} test(s) failed")
print("=" * 50)
