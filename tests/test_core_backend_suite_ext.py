"""Test-4: 核心后端回归扩展集（继续替代 legacy 脚本断言）。"""

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import Client


@pytest.mark.django_db
def test_ext_01_admin_url_reachable():
    resp = Client().get('/admin/')
    assert resp.status_code in (200, 301, 302)


@pytest.mark.django_db
def test_ext_02_api_posts_ok():
    resp = Client().get('/api/posts/')
    assert resp.status_code == 200


@pytest.mark.django_db
def test_ext_03_api_categories_ok():
    resp = Client().get('/api/categories/')
    assert resp.status_code == 200


@pytest.mark.django_db
def test_ext_04_api_tags_ok():
    resp = Client().get('/api/tags/')
    assert resp.status_code == 200


@pytest.mark.django_db
def test_ext_05_api_docs_visibility_by_debug():
    resp = Client().get('/api/docs/')
    expected = 200 if settings.DEBUG else 404
    assert resp.status_code == expected


@pytest.mark.django_db
def test_ext_06_api_redoc_visibility_by_debug():
    resp = Client().get('/api/redoc/')
    expected = 200 if settings.DEBUG else 404
    assert resp.status_code == expected


@pytest.mark.django_db
def test_ext_07_perf_headers_present_on_home():
    resp = Client().get('/')
    assert resp.get('X-Request-Duration-Ms') is not None
    assert resp.get('X-DB-Queries') is not None


def test_ext_08_csrf_middleware_enabled():
    from django.conf import settings as dj_settings

    assert 'django.middleware.csrf.CsrfViewMiddleware' in dj_settings.MIDDLEWARE


@pytest.mark.django_db
def test_ext_09_db_connection_usable():
    assert connection.is_usable()


@pytest.mark.django_db
def test_ext_10_db_select_one():
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
        assert cursor.fetchone()[0] == 1


@pytest.mark.django_db
def test_ext_11_user_model_loaded():
    User = get_user_model()
    # 仅验证模型可用，不要求预置数据
    assert User is not None


@pytest.mark.django_db
def test_ext_12_site_map_like_routes_accessible():
    client = Client()
    for url in ('/', '/blog/', '/forum/', '/tools/', '/accounts/login/', '/accounts/register/', '/api/'):
        resp = client.get(url)
        assert resp.status_code in (200, 301, 302)
