"""
测试数据生成工具 - 使用Faker生成随机测试数据
"""
from faker import Faker
import random
import string

# 创建中文Faker实例
faker_cn = Faker('zh_CN')
faker_en = Faker('en_US')


class DataGenerator:
    """测试数据生成器"""
    
    @staticmethod
    def username() -> str:
        """生成随机用户名"""
        # 用户名: 字母开头，包含字母和数字
        prefix = faker_en.first_name().lower()
        suffix = ''.join(random.choices(string.digits, k=4))
        return f"{prefix}{suffix}"
    
    @staticmethod
    def email() -> str:
        """生成随机邮箱"""
        return faker_cn.email()
    
    @staticmethod
    def password(length: int = 12) -> str:
        """生成随机密码"""
        # 确保密码包含大小写字母、数字和特殊字符
        lower = random.choices(string.ascii_lowercase, k=2)
        upper = random.choices(string.ascii_uppercase, k=2)
        digits = random.choices(string.digits, k=2)
        special = random.choices('!@#$%', k=2)
        remaining = random.choices(string.ascii_letters + string.digits, k=length - 8)
        
        password_chars = lower + upper + digits + special + remaining
        random.shuffle(password_chars)
        return ''.join(password_chars)
    
    @staticmethod
    def title() -> str:
        """生成随机标题"""
        return faker_cn.sentence(nb_words=6)
    
    @staticmethod
    def content(paragraphs: int = 3) -> str:
        """生成随机内容"""
        return '\n\n'.join(faker_cn.paragraphs(nb=paragraphs))
    
    @staticmethod
    def short_text(max_length: int = 100) -> str:
        """生成短文本"""
        return faker_cn.text(max_nb_chars=max_length)
    
    @staticmethod
    def tag() -> str:
        """生成随机标签"""
        tags = ['技术', '生活', '编程', 'Python', 'Django', '前端', '后端', 
                '数据库', 'Linux', 'Web', 'AI', '机器学习', '安全', '测试']
        return random.choice(tags)
    
    @staticmethod
    def category() -> str:
        """生成随机分类"""
        categories = ['技术分享', '教程', '心得', '问答', '讨论', '资源']
        return random.choice(categories)
    
    @staticmethod
    def user_data() -> dict:
        """生成完整的用户数据"""
        return {
            'username': DataGenerator.username(),
            'email': DataGenerator.email(),
            'password': DataGenerator.password(),
            'nickname': faker_cn.name()
        }
    
    @staticmethod
    def post_data() -> dict:
        """生成帖子数据"""
        return {
            'title': DataGenerator.title(),
            'content': DataGenerator.content(3),
            'category': DataGenerator.category()
        }
    
    @staticmethod
    def article_data() -> dict:
        """生成文章数据"""
        return {
            'title': DataGenerator.title(),
            'summary': DataGenerator.short_text(150),
            'content': DataGenerator.content(5),
            'category': DataGenerator.category(),
            'tags': [DataGenerator.tag() for _ in range(random.randint(1, 3))]
        }
    
    @staticmethod
    def comment() -> str:
        """生成评论内容"""
        return faker_cn.sentence()
