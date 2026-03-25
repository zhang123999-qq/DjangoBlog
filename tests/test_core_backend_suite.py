"""Test-3: 核心后端可运行用例（替代部分遗留 E2E 场景）。"""

import pytest
from django.core.cache import cache
from django.test import Client


@pytest.mark.django_db
def test_core_01_home_page_ok():
    resp = Client().get('/')
    assert resp.status_code == 200


@pytest.mark.django_db
def test_core_02_login_page_ok():
    resp = Client().get('/accounts/login/')
    assert resp.status_code in (200, 302)


@pytest.mark.django_db
def test_core_03_register_page_ok():
    resp = Client().get('/accounts/register/')
    assert resp.status_code in (200, 302)


@pytest.mark.django_db
def test_core_04_blog_list_ok():
    resp = Client().get('/blog/')
    assert resp.status_code == 200


@pytest.mark.django_db
def test_core_05_forum_list_ok():
    resp = Client().get('/forum/')
    assert resp.status_code == 200


@pytest.mark.django_db
def test_core_06_tools_list_ok():
    resp = Client().get('/tools/')
    assert resp.status_code == 200


@pytest.mark.django_db
def test_core_07_api_root_ok():
    resp = Client().get('/api/')
    assert resp.status_code == 200


@pytest.mark.django_db
def test_core_08_api_schema_ok():
    resp = Client().get('/api/schema/')
    assert resp.status_code == 200


@pytest.mark.django_db
def test_core_09_security_headers_present():
    resp = Client().get('/')
    assert resp.get('X-Frame-Options') == 'DENY'
    assert resp.get('X-Content-Type-Options') == 'nosniff'


@pytest.mark.django_db
def test_core_10_cache_roundtrip_ok():
    cache.set('test3:key', {'v': 1}, 60)
    assert cache.get('test3:key') == {'v': 1}
    cache.delete('test3:key')
