"""Test-6: 运维与系统行为后端回归（无浏览器依赖）。"""

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client


@pytest.mark.django_db
def test_ops_01_healthz_json_shape():
    resp = Client().get('/healthz/')
    assert resp.status_code in (200, 503)
    data = resp.json()
    assert 'status' in data and 'checks' in data


@pytest.mark.django_db
def test_ops_02_readiness_json_shape():
    resp = Client().get('/readiness/')
    assert resp.status_code in (200, 503)
    data = resp.json()
    assert 'ready' in data and 'checks' in data


@pytest.mark.django_db
def test_ops_03_liveness_ok():
    resp = Client().get('/liveness/')
    assert resp.status_code == 200
    assert resp.json().get('alive') is True


@pytest.mark.django_db
def test_ops_04_search_empty_ok():
    resp = Client().get('/search/?q=')
    assert resp.status_code == 200


@pytest.mark.django_db
def test_ops_05_contact_get_ok():
    resp = Client().get('/contact/')
    assert resp.status_code == 200


@pytest.mark.django_db
def test_ops_06_contact_post_redirect():
    resp = Client().post('/contact/', data={'name': 't', 'email': 't@example.com', 'message': 'hello'})
    assert resp.status_code in (301, 302)


@pytest.mark.django_db
def test_ops_07_settings_anonymous_redirect_login():
    resp = Client().get('/settings/')
    assert resp.status_code in (301, 302)


@pytest.mark.django_db
def test_ops_08_settings_staff_access_or_forbidden_by_env():
    User = get_user_model()
    u = User.objects.create_user(username='staff_t6', email='staff_t6@example.com', password='Pass123!@#', is_staff=True)
    c = Client()
    assert c.login(username='staff_t6', password='Pass123!@#') is True

    resp = c.get('/settings/')
    # DEBUG=False 时会 Forbidden；DEBUG=True 时可访问
    assert resp.status_code in (200, 403)


@pytest.mark.django_db
def test_ops_09_home_cache_populated():
    cache.delete('core:home:v1')
    resp = Client().get('/')
    assert resp.status_code == 200
    assert cache.get('core:home:v1') is not None


@pytest.mark.django_db
def test_ops_10_moderation_metrics_staff_ok():
    User = get_user_model()
    User.objects.create_user(username='mod_t6', email='mod_t6@example.com', password='Pass123!@#', is_staff=True)
    c = Client()
    assert c.login(username='mod_t6', password='Pass123!@#') is True

    resp = c.get('/api/moderation/metrics/?minutes=10')
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('success') is True
    assert 'thresholds' in data


@pytest.mark.django_db
def test_ops_11_moderation_approve_invalid_type_400():
    User = get_user_model()
    User.objects.create_user(username='mod_t6_2', email='mod_t6_2@example.com', password='Pass123!@#', is_staff=True)
    c = Client()
    assert c.login(username='mod_t6_2', password='Pass123!@#') is True

    resp = c.post('/api/moderation/approve/unknown/1/')
    assert resp.status_code == 400
    data = resp.json()
    assert data.get('error_code') == 'MODERATION_INVALID_CONTENT_TYPE'


@pytest.mark.django_db
def test_ops_12_moderation_reject_invalid_type_400():
    User = get_user_model()
    User.objects.create_user(username='mod_t6_3', email='mod_t6_3@example.com', password='Pass123!@#', is_staff=True)
    c = Client()
    assert c.login(username='mod_t6_3', password='Pass123!@#') is True

    resp = c.post('/api/moderation/reject/unknown/1/', data={'review_note': 'x'})
    assert resp.status_code == 400
    data = resp.json()
    assert data.get('error_code') == 'MODERATION_INVALID_CONTENT_TYPE'


@pytest.mark.django_db
def test_ops_13_api_schema_route_name_stable():
    resp = Client().get('/api/schema/')
    assert resp.status_code == 200


@pytest.mark.django_db
def test_ops_14_swagger_visibility_matches_debug():
    resp = Client().get('/api/docs/')
    expected = 200 if settings.DEBUG else 404
    assert resp.status_code == expected


@pytest.mark.django_db
def test_ops_15_redoc_visibility_matches_debug():
    resp = Client().get('/api/redoc/')
    expected = 200 if settings.DEBUG else 404
    assert resp.status_code == expected
