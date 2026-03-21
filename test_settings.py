#!/usr/bin/env python3
"""
环境配置测试脚本
测试开发环境和生产环境配置
"""

import os
import sys

def test_development():
    """测试开发环境配置"""
    print("\n" + "="*60)
    print("测试开发环境配置 (SQLite)")
    print("="*60)
    
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.development'
    os.environ['DEBUG'] = 'True'
    
    try:
        import django
        django.setup()
        
        from django.conf import settings
        
        print("配置加载成功")
        print(f"   环境: {settings.ENVIRONMENT}")
        print(f"   调试模式: {settings.DEBUG}")
        print(f"   数据库: {settings.DATABASES['default']['ENGINE']}")
        print(f"   缓存: {settings.CACHES['default']['BACKEND']}")
        
        # 测试数据库连接
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result[0] == 1:
                print("数据库连接正常")
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        return False

def test_production():
    """测试生产环境配置"""
    print("\n" + "="*60)
    print("测试生产环境配置 (MySQL + Redis)")
    print("="*60)
    
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'
    os.environ['DEBUG'] = 'False'
    
    # 设置测试用的环境变量
    os.environ.setdefault('DB_NAME', 'djangoblog')
    os.environ.setdefault('DB_USER', 'root')
    os.environ.setdefault('DB_PASSWORD', '')
    os.environ.setdefault('DB_HOST', 'localhost')
    os.environ.setdefault('REDIS_URL', 'redis://127.0.0.1:6379/1')
    
    try:
        import django
        django.setup()
        
        from django.conf import settings
        
        print("配置加载成功")
        print(f"   环境: {settings.ENVIRONMENT}")
        print(f"   调试模式: {settings.DEBUG}")
        print(f"   数据库: {settings.DATABASES['default']['ENGINE']}")
        print(f"   缓存: {settings.CACHES['default']['BACKEND']}")
        
        # 测试 MySQL 连接
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result[0] == 1:
                    print("MySQL 连接正常")
        except Exception as e:
            print(f"MySQL 连接失败 (可能未安装): {e}")
        
        # 测试 Redis 连接
        try:
            from django.core.cache import cache
            cache.set('test_key', 'test_value', 10)
            value = cache.get('test_key')
            if value == 'test_value':
                print("Redis 连接正常")
        except Exception as e:
            print(f"Redis 连接失败 (可能未安装): {e}")
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("="*60)
    print("DjangoBlog 环境配置测试")
    print("="*60)
    
    # 保存原始环境
    original_settings = os.environ.get('DJANGO_SETTINGS_MODULE')
    original_debug = os.environ.get('DEBUG')
    
    results = []
    
    # 测试开发环境
    results.append(('开发环境', test_development()))
    
    # 清除已导入的模块
    modules_to_remove = [key for key in sys.modules.keys() if key.startswith('config') or key.startswith('django')]
    for module in modules_to_remove:
        del sys.modules[module]
    
    # 测试生产环境
    results.append(('生产环境', test_production()))
    
    # 恢复原始环境
    if original_settings:
        os.environ['DJANGO_SETTINGS_MODULE'] = original_settings
    if original_debug:
        os.environ['DEBUG'] = original_debug
    
    # 打印结果
    print("\n" + "="*60)
    print("测试结果")
    print("="*60)
    for name, result in results:
        status = "通过" if result else "失败"
        print(f"   {name}: {status}")
    
    print("="*60)

if __name__ == '__main__':
    main()
