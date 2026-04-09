"""
验证码生成和验证工具

安全特性:
- 使用 secrets 模块替代 random，防止随机数可预测攻击
- 字母数字混合验证码，排除易混淆字符
- 验证码 5 分钟过期
- 同一 IP 3 次错误后锁定 5 分钟
- 验证后销毁，防止重放攻击
"""
import secrets
import time
import hashlib
import logging
import os
from PIL import Image, ImageDraw, ImageFont
import io
import base64

logger = logging.getLogger(__name__)

# 验证码字符集（排除易混淆字符: 0/O, 1/I/l/L）
CAPTCHA_CHARS = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'

# 验证码有效期（秒）
CAPTCHA_EXPIRE_SECONDS = 300  # 5 分钟

# 最大尝试次数
MAX_ATTEMPTS = 3

# 尝试锁定时间（秒）
LOCKOUT_SECONDS = 300  # 5 分钟


def get_client_ip(request):
    """获取客户端真实 IP 地址"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip


def get_attempt_cache_key(ip):
    """获取尝试次数缓存 key"""
    return f'captcha_attempts:{ip}'


def get_lockout_cache_key(ip):
    """获取锁定缓存 key"""
    return f'captcha_lockout:{ip}'


def is_locked_out(request):
    """检查 IP 是否被锁定"""
    from django.core.cache import cache
    ip = get_client_ip(request)
    lockout_key = get_lockout_cache_key(ip)
    return cache.get(lockout_key) is not None


def record_failed_attempt(request):
    """记录验证失败尝试"""
    from django.core.cache import cache
    ip = get_client_ip(request)
    attempt_key = get_attempt_cache_key(ip)
    
    attempts = cache.get(attempt_key, 0) + 1
    cache.set(attempt_key, attempts, LOCKOUT_SECONDS)
    
    if attempts >= MAX_ATTEMPTS:
        # 达到最大次数，锁定 IP
        lockout_key = get_lockout_cache_key(ip)
        cache.set(lockout_key, True, LOCKOUT_SECONDS)
        logger.warning(f'验证码尝试次数过多，IP {ip} 已锁定 5 分钟')
    
    return attempts


def clear_attempts(request):
    """清除尝试记录"""
    from django.core.cache import cache
    ip = get_client_ip(request)
    attempt_key = get_attempt_cache_key(ip)
    cache.delete(attempt_key)


def generate_captcha(code_length=6):
    """
    生成验证码（字母数字混合，使用密码学安全的随机数）
    
    Args:
        code_length: 验证码长度，默认 6 位
        
    Returns:
        tuple: (验证码明文, base64 图片)
    """
    # 使用 secrets 模块生成验证码
    # 字符集 31 个字符，6 位 = 31^6 = 8.87 亿种组合
    code = ''.join(secrets.choice(CAPTCHA_CHARS) for _ in range(code_length))

    # 创建验证码图片
    width, height = 120, 40
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)

    # 绘制干扰线（增加到 8 条）
    for _ in range(8):
        start = (secrets.randbelow(120), secrets.randbelow(40))
        end = (secrets.randbelow(120), secrets.randbelow(40))
        color = (secrets.randbelow(100) + 50, secrets.randbelow(100) + 50, secrets.randbelow(100) + 50)
        draw.line([start, end], fill=color, width=1)

    # 绘制噪点（增加到 100 个）
    for _ in range(100):
        x = secrets.randbelow(120)
        y = secrets.randbelow(40)
        color = (secrets.randbelow(150) + 50, secrets.randbelow(150) + 50, secrets.randbelow(150) + 50)
        draw.point((x, y), fill=color)

    # 尝试加载字体（按优先级尝试多个路径）
    font = None
    font_paths = [
        # 项目打包字体（推荐）
        os.path.join(os.path.dirname(__file__), 'fonts', 'captcha.ttf'),
        # Windows 系统字体
        'C:/Windows/Fonts/arial.ttf',
        'C:/Windows/Fonts/consola.ttf',
        # Linux 系统字体
        '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
        '/usr/share/fonts/truetype/freefont/FreeMono.ttf',
        # macOS 系统字体
        '/System/Library/Fonts/Menlo.ttc',
    ]
    
    for font_path in font_paths:
        try:
            font = ImageFont.truetype(font_path, 28)
            break
        except Exception:
            continue
    
    if font is None:
        font = ImageFont.load_default()
    
    # 计算起始位置
    char_width = width // code_length
    x_offset = 10
    
    for i, char in enumerate(code):
        # 随机颜色（深色系）
        color = (secrets.randbelow(50), secrets.randbelow(50), secrets.randbelow(100) + 50)
        # 轻微随机偏移
        y_offset = secrets.randbelow(8) + 4
        draw.text((x_offset + i * char_width, y_offset), char, fill=color, font=font)

    # 将图片转换为 base64
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return code, image_base64


def store_captcha(request, code):
    """
    存储验证码到 session
    
    Args:
        request: Django 请求对象
        code: 验证码明文
    """
    # 存储验证码 hash（不存储明文）
    code_hash = hashlib.sha256(code.upper().encode()).hexdigest()
    
    request.session['captcha_code'] = {
        'hash': code_hash,
        'expires_at': time.time() + CAPTCHA_EXPIRE_SECONDS,
    }


def validate_captcha(request, code):
    """
    验证验证码
    
    Args:
        request: Django 请求对象
        code: 用户输入的验证码
        
    Returns:
        tuple: (是否验证成功, 错误消息)
    """
    from django.conf import settings
    from django.core.cache import cache
    
    # 测试环境跳过验证码验证
    if getattr(settings, 'TESTING', False):
        return True, None
    
    # 检查 IP 是否被锁定
    if is_locked_out(request):
        return False, '验证码错误次数过多，请 5 分钟后再试'
    
    # 获取存储的验证码
    stored = request.session.get('captcha_code')
    if not stored:
        return False, '验证码已过期，请刷新页面'
    
    # 检查是否过期
    if time.time() > stored.get('expires_at', 0):
        # 清除过期验证码
        del request.session['captcha_code']
        return False, '验证码已过期，请刷新页面'
    
    # 计算 hash 并比较（忽略大小写）
    code_hash = hashlib.sha256(code.upper().encode()).hexdigest()
    
    if stored['hash'] != code_hash:
        # 验证失败，记录尝试次数
        attempts = record_failed_attempt(request)
        remaining = MAX_ATTEMPTS - attempts
        
        if remaining > 0:
            return False, f'验证码错误，还剩 {remaining} 次机会'
        else:
            return False, '验证码错误次数过多，请 5 分钟后再试'
    
    # 验证成功，清除验证码和尝试记录
    del request.session['captcha_code']
    clear_attempts(request)
    
    return True, None
