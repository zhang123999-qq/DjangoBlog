"""Test-5: 认证与审核接口后端回归（无浏览器依赖）。"""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client


@pytest.mark.django_db
def test_auth_01_register_get_ok():
    resp = Client().get('/accounts/register/')
    assert resp.status_code in (200, 302)


@pytest.mark.django_db
def test_auth_02_login_get_ok():
    resp = Client().get('/accounts/login/')
    assert resp.status_code in (200, 302)


@pytest.mark.django_db
def test_auth_03_logout_redirect_for_anonymous():
    resp = Client().get('/accounts/logout/')
    assert resp.status_code in (200, 301, 302, 405)


@pytest.mark.django_db
def test_auth_04_create_user_model_ok():
    User = get_user_model()
    u = User.objects.create_user(username='u_test5', email='u_test5@example.com', password='Pass123!@#')
    assert u.pk is not None


@pytest.mark.django_db
def test_auth_05_user_password_check_ok():
    User = get_user_model()
    u = User.objects.create_user(username='u_test5_pwd', email='u_test5_pwd@example.com', password='Pass123!@#')
    assert u.check_password('Pass123!@#') is True


@pytest.mark.django_db
def test_auth_06_api_moderation_metrics_requires_auth():
    resp = Client().get('/api/moderation/metrics/?minutes=10')
    assert resp.status_code in (401, 403)


@pytest.mark.django_db
def test_auth_07_api_moderation_approve_requires_auth():
    resp = Client().post('/api/moderation/approve/comment/1/')
    assert resp.status_code in (401, 403)


@pytest.mark.django_db
def test_auth_08_api_moderation_reject_requires_auth():
    resp = Client().post('/api/moderation/reject/comment/1/', data={'review_note': 'x'})
    assert resp.status_code in (401, 403)


@pytest.mark.django_db
def test_auth_09_api_upload_status_guarded_or_not_found():
    resp = Client().get('/api/upload/status/not-exist-id/')
    assert resp.status_code in (403, 404, 400)


@pytest.mark.django_db
def test_auth_10_api_schema_open():
    resp = Client().get('/api/schema/')
    assert resp.status_code == 200


@pytest.mark.django_db
def test_auth_11_tools_home_open():
    resp = Client().get('/tools/')
    assert resp.status_code == 200


@pytest.mark.django_db
def test_auth_12_forum_home_open():
    resp = Client().get('/forum/')
    assert resp.status_code == 200
