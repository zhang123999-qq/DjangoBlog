# 测试文档

## 概述

DjangoBlog 使用 Playwright + pytest 进行自动化测试，采用页面对象模型（POM）设计模式，提高测试的可维护性和可扩展性。

## 测试框架特性

- ✅ **验证码自动处理** - 支持测试验证码、OCR识别
- ✅ **页面对象模型** - 将页面元素封装成对象，易于维护
- ✅ **智能等待** - 自动等待元素加载，提高稳定性
- ✅ **重试机制** - 失败自动重试，提高可靠性
- ✅ **截图记录** - 失败自动截图，便于调试
- ✅ **模块化设计** - 易于扩展新的测试用例

## 目录结构

```
tests/
├── conftest.py           # Pytest配置、fixtures
├── README.md             # 本文档
├── test_auth.py          # 认证测试（登录/注册）
├── test_blog.py          # 博客功能测试
├── test_security.py      # 安全测试
├── test_register.py      # 注册测试（旧版，保留）
├── utils/                # 工具模块
│   ├── helpers.py        # 辅助工具类
│   ├── page_objects.py   # 页面对象模型
│   └── data_generator.py # 测试数据生成
├── logs/                 # 测试日志
└── screenshots/          # 失败截图
```

## 快速开始

### 安装依赖

```bash
# 安装项目依赖
uv pip install -r requirements/development.txt

# 安装Playwright浏览器
uv run playwright install chromium
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行冒烟测试
pytest tests/ -v -m smoke

# 运行认证测试
pytest tests/ -v -m auth

# 运行安全测试
pytest tests/ -v -m security

# 运行博客测试
pytest tests/ -v -m blog
```

### 命令行参数

```bash
# 无头模式（不显示浏览器）
pytest tests/ -v --headless

# 指定测试URL
pytest tests/ -v --test-url=http://localhost:8000

# 慢速执行（调试用）
pytest tests/ -v --slow-mo=500

# 设置超时时间
pytest tests/ -v --timeout=60000

# 设置重试次数
pytest tests/ -v --retries=3

# 测试验证码
pytest tests/ -v --test-captcha="test"
```

## 测试标记

| 标记 | 说明 |
|------|------|
| `@pytest.mark.smoke` | 冒烟测试，核心功能验证 |
| `@pytest.mark.auth` | 认证相关测试 |
| `@pytest.mark.blog` | 博客功能测试 |
| `@pytest.mark.forum` | 论坛功能测试 |
| `@pytest.mark.tools` | 工具栏测试 |
| `@pytest.mark.security` | 安全测试 |
| `@pytest.mark.integration` | 集成测试 |
| `@pytest.mark.slow` | 慢速测试 |

## 页面对象模型

### 使用示例

```python
from utils.page_objects import LoginPage, HomePage

def test_login(login_page: LoginPage):
    """测试登录"""
    # 打开登录页面
    login_page.open()
    
    # 执行登录
    login_page.login('admin', 'password', 'test')
    
    # 验证结果
    assert login_page.is_login_success()
```

### 可用的页面对象

| 对象 | 说明 | Fixture名称 |
|------|------|-------------|
| `LoginPage` | 登录页面 | `login_page` |
| `RegisterPage` | 注册页面 | `register_page` |
| `HomePage` | 首页 | `home_page` |
| `BlogPage` | 博客页面 | - |
| `UserFlow` | 用户流程封装 | `user_flow` |

## 验证码处理

### 自动处理

测试框架会自动处理验证码：

1. 检测是否存在验证码输入框
2. 尝试测试验证码（`test`, `1234`, `0000` 等）
3. 如果安装了Tesseract OCR，尝试识别验证码图片

### 手动指定

```bash
# 指定测试验证码
pytest tests/ -v --test-captcha="test"

# 在代码中使用
login_page.login('admin', 'password', captcha='test')
```

### 禁用验证码（开发环境）

在 `.env` 中设置：

```env
CAPTCHA_ENABLED=False
```

## 辅助工具

### CaptchaHandler

```python
from utils.helpers import CaptchaHandler

captcha = CaptchaHandler(test_mode=True)
success, text = captcha.solve_captcha(page, 'img.captcha', 'input[name="captcha"]')
```

### WaitHelper

```python
from utils.helpers import WaitHelper

wait = WaitHelper(page)

# 等待元素
wait.wait_for_element('.my-element')

# 等待URL包含文本
wait.wait_for_url_contains('dashboard')

# 等待页面文本
wait.wait_for_text('登录成功')
```

### RetryHelper

```python
from utils.helpers import RetryHelper

# 失败重试
result = RetryHelper.retry_on_failure(
    lambda: some_function(),
    max_retries=3,
    delay=1.0
)
```

## 测试数据生成

```python
from utils.data_generator import DataGenerator

# 生成用户数据
user = DataGenerator.user_data()
# {'username': 'user_abc123', 'email': 'abc@test.com', 'password': 'Test123456!'}

# 生成邮箱
email = DataGenerator.email()

# 生成用户名
username = DataGenerator.username()
```

## 调试技巧

### 截图调试

测试失败时会自动截图，保存在 `tests/screenshots/`

### 日志调试

```bash
# 查看详细日志
cat tests/logs/test_*.log
```

### 交互式调试

```python
# 在测试中设置断点
def test_something(page):
    page.goto('/login')
    # 调试：在这里暂停
    import pdb; pdb.set_trace()
```

### 慢速执行

```bash
# 慢速执行，方便观察
pytest tests/ -v --slow-mo=1000 --headless=false
```

## 编写新测试

### 创建新的测试文件

```python
# tests/test_new_feature.py
import pytest
import logging
from playwright.sync_api import Page

logger = logging.getLogger(__name__)

@pytest.mark.smoke
def test_new_feature(page: Page, base_url: str):
    """测试新功能"""
    logger.info("测试新功能")
    
    page.goto(f"{base_url}/new-feature/")
    page.wait_for_load_state('networkidle')
    
    # 断言
    assert page.title() is not None
```

### 创建新的页面对象

```python
# tests/utils/page_objects.py

class NewFeaturePage(BasePage):
    """新功能页面对象"""
    
    SOME_INPUT = 'input[name="some_field"]'
    SUBMIT_BTN = 'button[type="submit"]'
    
    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)
        self.path = "/new-feature/"
    
    def open(self) -> 'NewFeaturePage':
        self.navigate(self.path)
        return self
    
    def do_something(self, value: str) -> 'NewFeaturePage':
        self.page.fill(self.SOME_INPUT, value)
        self.page.click(self.SUBMIT_BTN)
        self.wait.wait_for_navigation()
        return self
```

## 最佳实践

1. **使用页面对象模型** - 不要直接在测试中操作元素选择器
2. **使用Fixtures** - 利用pytest fixtures管理测试依赖
3. **添加日志** - 记录测试步骤，便于调试
4. **使用标记** - 合理使用测试标记，便于筛选执行
5. **参数化测试** - 使用 `@pytest.mark.parametrize` 减少重复代码
6. **独立测试** - 每个测试应该独立，不依赖其他测试的结果
7. **清理数据** - 测试完成后清理创建的数据

## 持续集成

### GitHub Actions

```yaml
- name: Run tests
  run: |
    pytest tests/ -v --headless --timeout=60000
```

### 生成HTML报告

```bash
pytest tests/ -v --html=tests/report.html --self-contained-html
```

## 常见问题

### Q: 验证码测试失败？

A: 检查是否设置了测试验证码或禁用了验证码功能。

### Q: 元素找不到？

A: 使用 `--slow-mo` 参数慢速执行，观察页面加载情况。

### Q: 测试不稳定？

A: 使用 `WaitHelper` 智能等待，而不是固定等待时间。

### Q: 如何测试需要登录的功能？

A: 使用 `logged_in_page` fixture，它会自动登录。
