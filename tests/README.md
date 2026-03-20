# DjangoBlog 自动化测试套件

基于 Playwright + Pytest 的端到端自动化测试框架。

## 📁 项目结构

```
tests/
├── conftest.py           # Pytest配置和fixtures
├── test_register.py      # 用户注册测试（含安全测试）
├── test_post.py          # 论坛发帖测试
├── test_article.py       # 文章发布测试
├── test_like.py          # 点赞功能测试
├── test_security.py      # 安全测试套件
├── utils/                # 工具模块
│   ├── __init__.py
│   ├── data_generator.py # 测试数据生成
│   └── wait_for.py       # 自定义等待条件
├── requirements.txt      # 依赖包
└── README.md            # 本文档
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 进入测试目录
cd tests

# 安装Python依赖
pip install -r requirements.txt

# 安装Playwright浏览器
playwright install chromium
```

### 2. 运行测试

```bash
# 运行所有测试
pytest

# 有头模式运行（可见浏览器）
pytest --headless=false

# 指定基础URL
pytest --test-url=http://localhost:8000

# 运行单个测试文件
pytest test_register.py

# 运行特定测试用例
pytest test_register.py::TestRegister::test_register_success

# 并行运行
pytest -n 4

# 生成HTML报告
pytest --html=report.html --self-contained-html

# 运行安全测试
pytest -m security

# 详细输出
pytest -v

# 显示打印输出
pytest -s
```

### 3. 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--headless` | 无头模式运行 | False |
| `--test-url` | 测试基础URL | http://localhost:8000 |
| `--slow-mo` | 慢速操作延迟(ms) | 0 |
| `--timeout` | 默认超时(ms) | 30000 |

## 📝 测试用例说明

### 用户注册测试 (test_register.py)

| 用例 | 说明 |
|------|------|
| test_register_success | 正常注册流程 |
| test_register_existing_username | 已存在用户名注册 |
| test_register_weak_password | 弱密码注册 |
| test_register_password_mismatch | 密码不一致 |
| test_register_invalid_email | 无效邮箱格式 |
| test_register_empty_fields | 空字段提交 |

### 安全测试 (test_security.py)

| 用例 | 说明 |
|------|------|
| test_xss_in_username | XSS攻击测试 |
| test_sql_injection_in_username | SQL注入测试 |
| test_long_username | 超长输入测试 |
| test_special_characters_in_username | 特殊字符测试 |
| test_csrf_token_present | CSRF Token检查 |
| test_sql_injection_login | 登录SQL注入 |
| test_html_injection | HTML注入测试 |
| test_null_byte_injection | 空字节注入测试 |

### 论坛发帖测试 (test_post.py)

| 用例 | 说明 |
|------|------|
| test_create_topic_success | 发布主题 |
| test_create_topic_without_title | 空标题发布 |
| test_create_topic_without_content | 空内容发布 |
| test_view_topic_list | 查看主题列表 |
| test_view_topic_detail | 查看主题详情 |

### 文章发布测试 (test_article.py)

| 用例 | 说明 |
|------|------|
| test_view_article_list | 查看文章列表 |
| test_create_article_success | 发布文章 |
| test_view_article_detail | 查看文章详情 |
| test_article_comment | 文章评论 |
| test_article_category_filter | 分类筛选 |

### 点赞功能测试 (test_like.py)

| 用例 | 说明 |
|------|------|
| test_like_comment | 评论点赞 |
| test_like_forum_reply | 论坛回复点赞 |
| test_like_without_login | 未登录点赞 |
| test_toggle_like | 点赞/取消切换 |

## 🔒 安全测试

安全测试覆盖以下攻击类型：

### 1. 注入攻击
- SQL注入
- HTML注入
- XSS跨站脚本
- 命令注入

### 2. 认证安全
- 弱密码检测
- 会话管理
- 登出清除会话

### 3. 输入验证
- 超长输入
- 特殊字符
- Unicode处理
- 空字节注入

### 4. 防护检查
- CSRF Token
- 点击劫持防护
- 敏感信息泄露

## 📊 测试报告

### HTML报告

```bash
pytest --html=report.html --self-contained-html
```

### Allure报告

```bash
# 生成Allure报告
pytest --alluredir=allure-report

# 查看报告
allure serve allure-report
```

## 🖼️ 失败截图

测试失败时自动截图，保存在 `screenshots/` 目录：
```
screenshots/
├── test_register_success_20260315_150000.png
└── test_create_topic_success_20260315_150100.png
```

## 📝 日志

测试日志保存在 `logs/` 目录：
```
logs/
└── test_20260315_150000.log
```

## ⚙️ 高级用法

### 自定义等待条件

```python
from utils.wait_for import WaitFor

# 等待URL包含指定模式
WaitFor.url_contains(page, '/blog/')

# 等待元素文本变化
WaitFor.element_text_change(locator, original_text)

# 等待元素数量
WaitFor.element_count(page, '.article', 5)
```

### 数据生成

```python
from utils.data_generator import DataGenerator

# 生成用户数据
user = DataGenerator.user_data()

# 生成文章数据
article = DataGenerator.article_data()

# 生成帖子数据
post = DataGenerator.post_data()
```

### 运行特定标记的测试

```bash
# 只运行安全测试
pytest -m security

# 只运行慢测试
pytest -m slow

# 排除慢测试
pytest -m "not slow"
```

## 🔒 最佳实践

1. **元素定位** - 优先使用ID、name、data-testid
2. **显式等待** - 不使用time.sleep()
3. **数据隔离** - 每个测试用例独立生成数据
4. **异常处理** - 关键步骤捕获异常并截图
5. **日志记录** - 记录测试步骤和结果
6. **安全优先** - 所有输入都要验证

## 📞 问题排查

### 浏览器启动失败

```bash
# 重新安装浏览器
playwright install --force chromium
```

### 元素定位失败

1. 使用有头模式查看页面: `pytest --headless=false`
2. 检查页面是否完全加载
3. 使用更精确的选择器

### 测试数据冲突

使用Faker生成唯一数据，避免硬编码。

## 🔧 CI/CD 集成

```yaml
# GitHub Actions 示例
- name: Run tests
  run: |
    pip install -e ".[dev]"
    playwright install chromium
    pytest --headless --html=report.html
```

---

**测试框架版本**: 2.0.0  
**Python要求**: 3.13+  
**最后更新**: 2026-03-15
