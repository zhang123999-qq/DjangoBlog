"""
安装向导URL配置
"""
from django.urls import path
from . import views

app_name = 'install'

urlpatterns = [
    # 安装首页
    path('', views.install_index, name='index'),
    
    # 快速安装
    path('quick/', views.quick_install, name='quick'),
    
    # 向导式安装
    path('wizard/step1/', views.step1_environment, name='step1'),
    path('wizard/step2/', views.step2_site, name='step2'),
    path('wizard/step3/', views.step3_admin, name='step3'),
    path('wizard/step4/', views.step4_database, name='step4'),
    path('wizard/step5/', views.step5_redis, name='step5'),
    path('wizard/step6/', views.step6_execute, name='step6'),
    
    # AJAX测试
    path('ajax/test-db/', views.test_db_ajax, name='test_db'),
    path('ajax/test-redis/', views.test_redis_ajax, name='test_redis'),
]
