from django.core.management.base import BaseCommand
from django.conf import settings
from moderation.baidu_moderation import moderate_text, get_baidu_client


class Command(BaseCommand):
    """
    测试百度内容审核 API

    使用方式:
        python manage.py test_baidu_moderation "测试文本"
        python manage.py test_baidu_moderation --check
    """

    help = "测试百度内容审核 API"

    def add_arguments(self, parser):
        parser.add_argument(
            "text",
            nargs="?",
            type=str,
            help="要测试的文本内容",
        )
        parser.add_argument(
            "--check",
            action="store_true",
            help="检查百度 API 配置状态",
        )

    def handle(self, *args, **kwargs):
        text = kwargs.get("text")
        check_only = kwargs.get("check")

        # 检查配置状态
        if check_only or not text:
            self.stdout.write("=" * 50)
            self.stdout.write("百度内容审核 API 配置状态")
            self.stdout.write("=" * 50)

            if settings.BAIDU_MODERATION_ENABLED:
                self.stdout.write(self.style.SUCCESS("[OK] 百度内容审核已启用"))
                self.stdout.write(f"  APP_ID: {settings.BAIDU_APP_ID[:4]}****")
            else:
                self.stdout.write(self.style.WARNING("[X] 百度内容审核未启用"))
                self.stdout.write("")
                self.stdout.write("请在 .env 文件中配置以下参数:")
                self.stdout.write("  BAIDU_APP_ID=你的APP_ID")
                self.stdout.write("  BAIDU_API_KEY=你的API_KEY")
                self.stdout.write("  BAIDU_SECRET_KEY=你的SECRET_KEY")
                self.stdout.write("")
                self.stdout.write("申请地址: https://console.bce.baidu.com/ai/#/ai/antiporn/overview/index")

            # 测试客户端连接
            client = get_baidu_client()
            if client:
                self.stdout.write(self.style.SUCCESS("[OK] API 客户端初始化成功"))
            else:
                self.stdout.write(self.style.ERROR("[X] API 客户端初始化失败"))

            return

        # 测试文本审核
        self.stdout.write(f'测试文本: "{text}"')
        self.stdout.write("-" * 50)

        status, details = moderate_text(text)

        self.stdout.write(f"审核结果: {status}")
        self.stdout.write("详细信息:")

        import json

        self.stdout.write(json.dumps(details, ensure_ascii=False, indent=2))

        if status == "approved":
            self.stdout.write(self.style.SUCCESS("\n[OK] 内容合规"))
        elif status == "rejected":
            self.stdout.write(self.style.ERROR("\n[X] 内容违规"))
        else:
            self.stdout.write(self.style.WARNING("\n[?] 需人工审核"))
