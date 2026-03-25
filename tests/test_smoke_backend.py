"""后端烟雾测试（默认应可在本地直接运行）。"""

import pytest
from django.test import Client


@pytest.mark.django_db
def test_home_page_ok():
    client = Client()
    resp = client.get('/')
    assert resp.status_code == 200


@pytest.mark.django_db
def test_blog_list_ok():
    client = Client()
    resp = client.get('/blog/')
    assert resp.status_code == 200


@pytest.mark.django_db
def test_api_schema_ok():
    client = Client()
    resp = client.get('/api/schema/')
    assert resp.status_code == 200
