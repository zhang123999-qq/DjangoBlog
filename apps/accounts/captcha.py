"""
验证码生成和验证工具

修复: 使用 secrets 模块替代 random，防止随机数可预测攻击
"""
import secrets
from PIL import Image, ImageDraw, ImageFont
import io
import base64


def generate_captcha(code_length=6):
    """生成数字验证码（使用密码学安全的随机数）"""
    # 使用 secrets 模块生成6位数字验证码（100万种组合，防暴力破解）
    code = ''.join(secrets.choice('0123456789') for _ in range(code_length))

    # 创建验证码图片
    width, height = 120, 40
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)

    # 绘制干扰线
    for _ in range(5):
        start = (secrets.randbelow(120), secrets.randbelow(40))
        end = (secrets.randbelow(120), secrets.randbelow(40))
        draw.line([start, end], fill=(100, 100, 100), width=1)

    # 绘制噪点
    for _ in range(50):
        x = secrets.randbelow(120)
        y = secrets.randbelow(40)
        draw.point((x, y), fill=(150, 150, 150))

    # 绘制验证码文本
    try:
        # 尝试使用系统字体
        font = ImageFont.truetype('arial.ttf', 30)
    except Exception:
        # 如果系统字体不可用，使用默认字体
        font = ImageFont.load_default()

    # 使用font.getbbox()替代draw.textsize()
    bbox = font.getbbox(code)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    draw.text((x, y), code, fill=(0, 0, 0), font=font)

    # 将图片转换为base64
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return code, image_base64


def validate_captcha(request, code):
    """验证验证码"""
    # 在测试环境中跳过验证码验证
    from django.conf import settings
    if getattr(settings, 'TESTING', False):
        return True

    stored_code = request.session.get('captcha_code')
    if not stored_code:
        return False

    # 确保类型一致，都转换为字符串比较
    stored_code = str(stored_code)
    code = str(code)

    if stored_code != code:
        return False

    # 验证成功后销毁验证码，防止重复使用
    del request.session['captcha_code']
    return True
