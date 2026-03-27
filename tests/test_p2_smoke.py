"""P2 最小冒烟测试：首页、登录、发帖、工具接口。"""

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.models import User
from apps.blog.models import Category, Post
from apps.tools.models import ToolConfig


@pytest.mark.django_db
def test_homepage_smoke_ok():
    user = User.objects.create_user(username='u_home', email='u_home@example.com', password='Pass12345!')
    category = Category.objects.create(name='默认分类', slug='default-category')
    Post.objects.create(
        title='首页测试文章',
        slug='home-smoke-post',
        summary='summary',
        content='content',
        author=user,
        category=category,
        status='published',
    )

    client = Client()
    resp = client.get('/')
    assert resp.status_code == 200


@pytest.mark.django_db
def test_login_page_smoke_ok():
    client = Client()
    resp = client.get(reverse('accounts:login'))
    assert resp.status_code == 200


@pytest.mark.django_db
def test_post_create_page_requires_login_and_then_ok():
    user = User.objects.create_user(username='u_post', email='u_post@example.com', password='Pass12345!')

    client = Client()
    # 未登录应重定向到登录页
    resp = client.get(reverse('blog:post_create'))
    assert resp.status_code in (302, 301)

    # 登录后可访问创建页
    assert client.login(username='u_post', password='Pass12345!')
    resp2 = client.get(reverse('blog:post_create'))
    assert resp2.status_code == 200


@pytest.mark.django_db
def test_tools_api_schema_smoke_ok():
    # 准备工具数据（确保工具页面不为空）
    ToolConfig.objects.create(slug='dummy-tool', name='Dummy Tool', is_enabled=True)

    client = Client()

    # 工具列表页面
    tools_resp = client.get('/tools/')
    assert tools_resp.status_code == 200

    # 工具接口（OpenAPI schema）
    schema_resp = client.get('/api/schema/')
    assert schema_resp.status_code == 200
