"""
安装向导视图
"""
import os
import sys
import platform
import logging
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.management import call_command
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from apps.accounts.models import User
from apps.core.models import SiteConfig
from .forms import (
    Step1EnvironmentForm, Step2SiteForm, Step3AdminForm,
    Step4DatabaseForm, Step5RedisForm, QuickInstallForm
)

logger = logging.getLogger(__name__)


def get_system_info():
    """获取系统信息"""
    return {
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'django_version': '4.2',
        'os': platform.system(),
        'os_version': platform.release(),
    }


def test_database_connection(db_config):
    """测试数据库连接"""
    try:
        if db_config['ENGINE'] == 'django.db.backends.sqlite3':
            db_path = os.path.dirname(db_config['NAME'])
            if db_path and not os.path.exists(db_path):
                os.makedirs(db_path)
            return True, "✅ SQLite数据库配置有效"
        
        # MySQL/PostgreSQL连接测试
        if 'mysql' in db_config['ENGINE']:
            try:
                import pymysql
                pymysql.install_as_MySQLdb()
                conn = pymysql.connect(
                    host=db_config['HOST'] or 'localhost',
                    port=int(db_config['PORT'] or 3306),
                    user=db_config['USER'] or '',
                    password=db_config['PASSWORD'] or '',
                    database=db_config['NAME'],
                    charset='utf8mb4',
                    connect_timeout=5
                )
                conn.close()
                return True, "✅ MySQL数据库连接成功"
            except ImportError:
                return False, "❌ 未安装pymysql库，请运行: pip install pymysql"
        return True, "✅ 数据库配置有效"
    except Exception as e:
        return False, f"❌ 数据库连接失败: {str(e)}"


def test_redis_connection(redis_config):
    """测试Redis连接"""
    try:
        import redis
        r = redis.Redis(
            host=redis_config.get('host', 'localhost'),
            port=int(redis_config.get('port', 6379)),
            password=redis_config.get('password') or None,
            db=int(redis_config.get('db', 0)),
            socket_connect_timeout=5
        )
        r.ping()
        return True, "✅ Redis连接成功"
    except ImportError:
        return False, "❌ 未安装redis库，请运行: pip install redis"
    except Exception as e:
        return False, f"❌ Redis连接失败: {str(e)}"


def write_env_file(env_data, base_dir):
    """写入.env文件"""
    try:
        env_path = os.path.join(base_dir, '.env')
        
        # 生成SECRET_KEY
        if 'SECRET_KEY' not in env_data:
            from django.core.management.utils import get_random_secret_key
            env_data['SECRET_KEY'] = get_random_secret_key()
        
        # 构建env内容
        lines = [
            "# Django 配置",
            f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]
        
        for key, value in env_data.items():
            if value is not None:
                lines.append(f"{key}={value}")
        
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        return True, "✅ 配置文件写入成功"
    except Exception as e:
        return False, f"❌ 写入配置文件失败: {str(e)}"


def create_install_lock():
    """创建安装锁文件"""
    lock_path = os.path.join(BASE_DIR, 'installed.lock')
    with open(lock_path, 'w', encoding='utf-8') as f:
        f.write(f"Installed at: {datetime.now().isoformat()}\n")
        f.write(f"Python: {sys.version}\n")


# 全局变量
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def install_context(request):
    """安装上下文"""
    return {
        'base_dir': BASE_DIR,
        'system_info': get_system_info(),
        'is_installed': os.path.exists(os.path.join(BASE_DIR, 'installed.lock')),
    }


def check_installed(func):
    """检查是否已安装装饰器"""
    def wrapper(request, *args, **kwargs):
        if os.path.exists(os.path.join(BASE_DIR, 'installed.lock')):
            messages.info(request, '网站已安装，如需重新安装请删除 installed.lock 文件')
            return redirect('/')
        return func(request, *args, **kwargs)
    return wrapper


@check_installed
def install_index(request):
    """安装首页 - 选择安装模式"""
    return render(request, 'install/index.html', {
        'system_info': get_system_info(),
    })


@check_installed
def quick_install(request):
    """快速安装"""
    if request.method == 'POST':
        try:
            # 获取表单数据
            site_name = request.POST.get('site_name', 'Django Blog')
            allowed_hosts = request.POST.get('allowed_hosts', 'localhost,127.0.0.1,0.0.0.0,*')
            db_engine = request.POST.get('db_engine', 'sqlite')
            use_redis = request.POST.get('use_redis') == 'on'
            admin_username = request.POST.get('admin_username', 'admin')
            admin_email = request.POST.get('admin_email', '')
            admin_password = request.POST.get('admin_password', '')
            
            # 构建环境变量
            env_data = {
                'DEBUG': 'True',
                'ALLOWED_HOSTS': allowed_hosts,
                'SITE_NAME': site_name,
            }
            
            # 数据库配置
            if db_engine == 'mysql':
                db_name = request.POST.get('db_name_mysql', 'djangoblog')
                db_user = request.POST.get('db_user', 'root')
                db_password = request.POST.get('db_password', '')
                db_host = request.POST.get('db_host', 'localhost')
                db_port = request.POST.get('db_port', '3306')
                
                # 测试数据库连接
                db_config = {
                    'ENGINE': 'django.db.backends.mysql',
                    'NAME': db_name,
                    'USER': db_user,
                    'PASSWORD': db_password,
                    'HOST': db_host,
                    'PORT': db_port,
                }
                success, message = test_database_connection(db_config)
                if not success:
                    messages.error(request, message)
                    return render(request, 'install/quick_install.html', {})
                
                env_data['DB_ENGINE'] = 'django.db.backends.mysql'
                env_data['DB_NAME'] = db_name
                env_data['DB_USER'] = db_user
                env_data['DB_PASSWORD'] = db_password
                env_data['DB_HOST'] = db_host
                env_data['DB_PORT'] = db_port
            else:
                db_name = request.POST.get('db_name', 'db.sqlite3')
                env_data['DB_ENGINE'] = 'django.db.backends.sqlite3'
                env_data['DB_NAME'] = db_name
            
            # Redis 配置
            if use_redis:
                redis_host = request.POST.get('redis_host', 'localhost')
                redis_port = request.POST.get('redis_port', '6379')
                redis_password = request.POST.get('redis_password', '')
                redis_db = request.POST.get('redis_db', '0')
                
                # 测试 Redis 连接
                redis_config = {
                    'host': redis_host,
                    'port': redis_port,
                    'password': redis_password,
                    'db': redis_db,
                }
                success, message = test_redis_connection(redis_config)
                if not success:
                    messages.warning(request, f'{message}，将继续安装但不启用Redis')
                    use_redis = False
                else:
                    env_data['USE_REDIS'] = 'True'
                    env_data['REDIS_URL'] = f'redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}' if redis_password else f'redis://{redis_host}:{redis_port}/{redis_db}'
            
            # 1. 写入.env
            write_env_file(env_data, BASE_DIR)
            
            # 2. 执行迁移
            call_command('migrate', '--run-syncdb', verbosity=0)
            
            # 3. 创建管理员
            if not User.objects.filter(username=admin_username).exists():
                User.objects.create_superuser(
                    username=admin_username,
                    email=admin_email,
                    password=admin_password
                )
            
            # 4. 初始化默认数据
            try:
                call_command('init_default_data', verbosity=0)
            except Exception as e:
                logger.warning(f"初始化默认数据失败: {str(e)}")
            
            # 5. 创建网站配置
            SiteConfig.objects.update_or_create(
                id=1,
                defaults={
                    'site_name': site_name,
                    'is_installed': True
                }
            )
            
            # 6. 创建锁文件
            create_install_lock()
            
            messages.success(request, '🎉 安装成功！请登录管理后台。')
            return redirect('/accounts/login/')
            
        except Exception as e:
            logger.error(f"安装失败: {str(e)}")
            messages.error(request, f'安装失败: {str(e)}')
    
    return render(request, 'install/quick_install.html', {})


@check_installed
def step1_environment(request):
    """步骤1：环境检查"""
    if request.method == 'POST':
        form = Step1EnvironmentForm(request.POST)
        if form.is_valid():
            request.session['install_step1'] = True
            return redirect('install:step2')
    else:
        form = Step1EnvironmentForm()
    
    return render(request, 'install/step1_environment.html', {
        'form': form,
        'system_info': get_system_info(),
        'step': 1,
        'total_steps': 6,
    })


@check_installed
def step2_site(request):
    """步骤2：网站配置"""
    if not request.session.get('install_step1'):
        return redirect('install:step1')
    
    if request.method == 'POST':
        form = Step2SiteForm(request.POST)
        if form.is_valid():
            request.session['install_step2'] = form.cleaned_data
            return redirect('install:step3')
    else:
        form = Step2SiteForm()
    
    return render(request, 'install/step2_site.html', {
        'form': form,
        'step': 2,
        'total_steps': 6,
    })


@check_installed
def step3_admin(request):
    """步骤3：管理员配置"""
    if not request.session.get('install_step2'):
        return redirect('install:step2')
    
    if request.method == 'POST':
        form = Step3AdminForm(request.POST)
        if form.is_valid():
            request.session['install_step3'] = form.cleaned_data
            return redirect('install:step4')
    else:
        form = Step3AdminForm()
    
    return render(request, 'install/step3_admin.html', {
        'form': form,
        'step': 3,
        'total_steps': 6,
    })


@check_installed
def step4_database(request):
    """步骤4：数据库配置"""
    if not request.session.get('install_step3'):
        return redirect('install:step3')
    
    if request.method == 'POST':
        form = Step4DatabaseForm(request.POST)
        if form.is_valid():
            # 测试连接
            db_config = {
                'ENGINE': form.cleaned_data['db_engine'],
                'NAME': form.cleaned_data['db_name'],
                'USER': form.cleaned_data.get('db_user', ''),
                'PASSWORD': form.cleaned_data.get('db_password', ''),
                'HOST': form.cleaned_data.get('db_host', ''),
                'PORT': form.cleaned_data.get('db_port', ''),
            }
            
            success, message = test_database_connection(db_config)
            if not success:
                messages.error(request, message)
                return render(request, 'install/step4_database.html', {
                    'form': form,
                    'step': 4,
                    'total_steps': 6,
                })
            
            request.session['install_step4'] = form.cleaned_data
            return redirect('install:step5')
    else:
        form = Step4DatabaseForm()
    
    return render(request, 'install/step4_database.html', {
        'form': form,
        'step': 4,
        'total_steps': 6,
    })


@check_installed
def step5_redis(request):
    """步骤5：Redis配置"""
    if not request.session.get('install_step4'):
        return redirect('install:step4')
    
    if request.method == 'POST':
        form = Step5RedisForm(request.POST)
        if form.is_valid():
            # 如果启用Redis，测试连接
            if form.cleaned_data.get('use_redis'):
                success, message = test_redis_connection(form.cleaned_data)
                if not success:
                    messages.warning(request, f'{message}，将继续安装但不启用Redis')
                    form.cleaned_data['use_redis'] = False
            
            request.session['install_step5'] = form.cleaned_data
            return redirect('install:step6')
    else:
        form = Step5RedisForm()
    
    return render(request, 'install/step5_redis.html', {
        'form': form,
        'step': 5,
        'total_steps': 6,
    })


@check_installed
def step6_execute(request):
    """步骤6：执行安装"""
    if not request.session.get('install_step5'):
        return redirect('install:step5')
    
    if request.method == 'POST':
        try:
            # 执行安装
            # 获取网站配置（包含allowed_hosts）
            site_config = request.session.get('install_step2', {})
            allowed_hosts = site_config.get('allowed_hosts', 'localhost,127.0.0.1,0.0.0.0,*')
            
            env_data = {
                'DEBUG': 'True',
                'ALLOWED_HOSTS': allowed_hosts,
            }
            
            # 网站配置
            site_config = request.session.get('install_step2', {})
            env_data['SITE_NAME'] = site_config.get('site_name', 'Django Site')
            
            # 数据库配置
            db_config = request.session.get('install_step4', {})
            if db_config.get('db_engine') == 'django.db.backends.sqlite3':
                env_data['DATABASE_URL'] = f"sqlite://{db_config.get('db_name', 'db.sqlite3')}"
            
            # Redis配置
            redis_config = request.session.get('install_step5', {})
            if redis_config.get('use_redis'):
                env_data['REDIS_URL'] = f"redis://{redis_config.get('redis_host', 'localhost')}:{redis_config.get('redis_port', '6379')}/{redis_config.get('redis_db', 0)}"
            
            # 写入.env
            write_env_file(env_data, BASE_DIR)
            
            # 执行迁移
            call_command('migrate', '--run-syncdb', verbosity=0)
            
            # 创建管理员
            admin_config = request.session.get('install_step3', {})
            if not User.objects.filter(username=admin_config['admin_username']).exists():
                User.objects.create_superuser(
                    username=admin_config['admin_username'],
                    email=admin_config['admin_email'],
                    password=admin_config['admin_password1']
                )
            
            # 创建网站配置
            SiteConfig.objects.update_or_create(
                id=1,
                defaults={
                    'site_name': site_config.get('site_name', 'Django Site'),
                    'site_title': site_config.get('site_title', ''),
                    'site_description': site_config.get('site_description', ''),
                    'is_installed': True
                }
            )
            
            # 初始化默认数据（分类、标签、板块）
            try:
                call_command('init_default_data', verbosity=0)
            except Exception as e:
                logger.warning(f"初始化默认数据失败: {str(e)}")
            
            # 创建锁文件
            create_install_lock()
            
            # 清理session
            request.session.flush()
            
            return render(request, 'install/success.html', {
                'admin_username': admin_config.get('admin_username', 'admin'),
            })
            
        except Exception as e:
            logger.error(f"安装失败: {str(e)}")
            messages.error(request, f'安装失败: {str(e)}')
    
    return render(request, 'install/step6_execute.html', {
        'step': 6,
        'total_steps': 6,
    })


@require_GET
def test_db_ajax(request):
    """AJAX测试数据库连接"""
    db_config = {
        'ENGINE': request.GET.get('engine', 'sqlite'),
        'NAME': request.GET.get('name', ''),
        'USER': request.GET.get('user', ''),
        'PASSWORD': request.GET.get('password', ''),
        'HOST': request.GET.get('host', ''),
        'PORT': request.GET.get('port', ''),
    }
    
    success, message = test_database_connection(db_config)
    return JsonResponse({'success': success, 'message': message})


@require_GET
def test_redis_ajax(request):
    """AJAX测试Redis连接"""
    redis_config = {
        'host': request.GET.get('host', 'localhost'),
        'port': request.GET.get('port', '6379'),
        'password': request.GET.get('password', ''),
        'db': request.GET.get('db', '0'),
    }
    
    success, message = test_redis_connection(redis_config)
    return JsonResponse({'success': success, 'message': message})
