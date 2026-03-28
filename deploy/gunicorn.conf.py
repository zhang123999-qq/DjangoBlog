# Gunicorn 生产部署配置
# 放置在项目根目录: gunicorn.conf.py

import multiprocessing
import os

# ============================================
# 服务器绑定
# ============================================
bind = os.environ.get('GUNICORN_BIND', '0.0.0.0:8000')
backlog = 2048

# ============================================
# 工作进程配置
# ============================================
# 推荐公式: CPU核心数 * 2 + 1
workers = int(os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))

# 工作模式: sync, gevent, eventlet, tornado
worker_class = os.environ.get('GUNICORN_WORKER_CLASS', 'gevent')

# 每个 worker 的最大并发连接数 (gevent 模式)
worker_connections = int(os.environ.get('GUNICORN_WORKER_CONNECTIONS', 1000))

# 最大并发请求数
max_requests = int(os.environ.get('GUNICORN_MAX_REQUESTS', 1000))
max_requests_jitter = int(os.environ.get('GUNICORN_MAX_REQUESTS_JITTER', 50))

# ============================================
# 超时设置
# ============================================
timeout = int(os.environ.get('GUNICORN_TIMEOUT', 120))
graceful_timeout = int(os.environ.get('GUNICORN_GRACEFUL_TIMEOUT', 30))
keepalive = int(os.environ.get('GUNICORN_KEEPALIVE', 5))

# ============================================
# 进程配置
# ============================================
proc_name = os.environ.get('GUNICORN_PROC_NAME', 'djangoblog')
preload_app = True
daemon = False
pidfile = None
umask = 0o007
user = None
group = None
tmp_upload_dir = None

# ============================================
# 日志配置
# ============================================
accesslog = os.environ.get('GUNICORN_ACCESS_LOG', 'logs/gunicorn_access.log')
errorlog = os.environ.get('GUNICORN_ERROR_LOG', 'logs/gunicorn_error.log')
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# ============================================
# 安全设置
# ============================================
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# ============================================
# SSL 配置（可选）
# ============================================
# keyfile = '/path/to/keyfile.key'
# certfile = '/path/to/certfile.crt'
# ssl_version = ssl.PROTOCOL_TLSv1_2
# cert_reqs = ssl.CERT_NONE
# ca_certs = None
# ciphers = 'TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256'

# ============================================
# 钩子函数
# ============================================


def on_starting(server):
    """服务器启动时调用"""
    print("DjangoBlog Gunicorn 服务器启动中...")
    print(f"工作进程数: {workers}")
    print(f"工作模式: {worker_class}")
    print(f"绑定地址: {bind}")


def when_ready(server):
    """服务器就绪时调用"""
    print("DjangoBlog Gunicorn 服务器就绪")


def on_exit(server):
    """服务器退出时调用"""
    print("DjangoBlog Gunicorn 服务器关闭")


def pre_fork(server, worker):
    """fork 前调用"""
    pass


def post_fork(server, worker):
    """fork 后调用"""
    # 设置进程名
    try:
        import setproctitle
        setproctitle.setproctitle(f"gunicorn: worker [{worker.pid}]")
    except ImportError:
        pass


def pre_exec(server):
    """exec 前调用"""
    print("DjangoBlog Gunicorn pre_exec")


def worker_int(worker):
    """worker 被中断时调用"""
    print(f"Worker {worker.pid} 被中断")


def worker_abort(worker):
    """worker 被中止时调用"""
    print(f"Worker {worker.pid} 被中止")
