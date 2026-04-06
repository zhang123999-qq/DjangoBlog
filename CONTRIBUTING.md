# 贡献指南

感谢你对 DjangoBlog 项目的关注！本文档将帮助你了解如何参与项目贡献。

---

## 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发环境搭建](#开发环境搭建)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [Pull Request 流程](#pull-request-流程)
- [问题反馈](#问题反馈)

---

## 行为准则

- 尊重所有贡献者
- 保持建设性的讨论
- 接受建设性批评
- 关注对社区最有利的事情

---

## 如何贡献

### 贡献方式

1. **报告 Bug** - 提交 Issue 描述问题
2. **建议新功能** - 提交 Issue 描述需求
3. **改进文档** - 修复错别字、补充说明
4. **提交代码** - 修复 Bug 或实现新功能

### 开始之前

- 检查 [Issues](https://github.com/zhang123999-qq/DjangoBlog/issues) 是否已有相同问题
- 阅读现有代码，了解项目架构
- 大型改动建议先开 Issue 讨论

---

## 开发环境搭建

### 1. Fork 并克隆仓库

```bash
# Fork 后克隆你的仓库
git clone https://github.com/YOUR_USERNAME/DjangoBlog.git
cd DjangoBlog

# 添加上游仓库
git remote add upstream https://github.com/zhang123999-qq/DjangoBlog.git
```

### 2. 创建虚拟环境

```bash
# 使用 uv（推荐）
uv venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate     # Windows

# 安装开发依赖
uv pip install -r requirements/development.txt
```

### 3. 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑 .env，设置必要配置
# 开发环境建议设置：
DEBUG=True
DEPLOY_MODE=host
DB_HOST=localhost
```

### 4. 初始化数据库

```bash
# 创建数据库迁移
uv run python manage.py migrate

# 创建管理员账户
uv run python manage.py createsuperuser

# 启动开发服务器
uv run python manage.py runserver
```

### 5. 运行测试

```bash
# 运行所有测试
uv run pytest -q

# 运行特定测试文件
uv run pytest apps/blog/tests/ -v

# 检查代码质量
uv run python manage.py check
uv run flake8 apps/
```

### 6. 安装 pre-commit 钩子

```bash
# 安装 pre-commit
uv pip install pre-commit

# 安装 Git 钩子
pre-commit install

# 手动运行所有检查
pre-commit run --all-files
```

pre-commit 将在每次提交时自动运行：
- black：代码格式化
- isort：导入排序
- flake8：代码风格检查
- mypy：类型检查
- bandit：安全检查

---

## 代码规范

### Python 代码风格

- 遵循 [PEP 8](https://peps.python.org/pep-0008/) 规范
- 使用 `black` 格式化代码
- 使用 `flake8` 检查代码风格
- 使用 `mypy` 进行类型检查
- 使用 `pre-commit` 自动检查

```bash
# 格式化代码
black apps/

# 检查风格
flake8 apps/

# 类型检查
mypy apps/

# 一键运行所有检查（推荐）
pre-commit run --all-files
```

### 代码注释

- 函数和类需要 docstring
- 复杂逻辑需要行内注释
- 使用中文注释（项目主要面向中文用户）

```python
def get_published_posts(category_id: int) -> QuerySet:
    """获取指定分类下的已发布文章列表。
    
    Args:
        category_id: 分类 ID
        
    Returns:
        已发布文章的 QuerySet
    """
    return Post.objects.filter(
        category_id=category_id,
        status='published'
    ).select_related('author', 'category')
```

### Django 最佳实践

- 使用 CBV（类视图）而非 FBV
- 模型字段添加 `verbose_name` 和 `help_text`
- 使用 `select_related` / `prefetch_related` 优化查询
- 敏感配置使用环境变量

---

## 提交规范

### Commit 消息格式

使用 [Conventional Commits](https://www.conventionalcommits.org/zh-hans/) 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

| 类型 | 说明 |
|------|------|
| feat | 新功能 |
| fix | Bug 修复 |
| docs | 文档更新 |
| style | 代码格式（不影响功能） |
| refactor | 重构（不新增功能或修复 Bug） |
| perf | 性能优化 |
| test | 测试相关 |
| chore | 构建/工具相关 |

### 示例

```bash
# 新功能
git commit -m "feat(blog): 添加文章点赞功能"

# Bug 修复
git commit -m "fix(forum): 修复主题回复计数不准确的问题"

# 文档更新
git commit -m "docs: 更新部署指南，添加 SSL 配置说明"

# 性能优化
git commit -m "perf(blog): 优化首页文章列表查询性能"
```

---

## Pull Request 流程

### 1. 创建分支

```bash
# 从 main 创建功能分支
git checkout main
git pull upstream main
git checkout -b feature/your-feature-name
```

### 2. 开发并提交

```bash
# 编写代码...
git add .
git commit -m "feat: 添加新功能"
```

### 3. 推送到 Fork

```bash
git push origin feature/your-feature-name
```

### 4. 创建 Pull Request

1. 访问你 Fork 的仓库页面
2. 点击 "Compare & pull request"
3. 填写 PR 描述：
   - 改动内容说明
   - 关联的 Issue（如有）
   - 测试结果

### 5. PR 检查清单

- [ ] 代码通过 `pre-commit` 检查
- [ ] 测试通过 `pytest`
- [ ] 新功能有对应测试
- [ ] 文档已更新（如需要）
- [ ] Commit 消息符合规范

### 6. 代码审查

- 响应审查意见
- 按要求修改代码
- 保持耐心和礼貌

---

## 问题反馈

### Bug 报告

提交 Issue 时请包含：

1. **环境信息**
   - Python 版本
   - Django 版本
   - 操作系统
   - 部署方式（Docker / 本地）

2. **复现步骤**
   - 详细的操作步骤
   - 预期结果
   - 实际结果

3. **错误信息**
   - 完整的错误堆栈
   - 相关日志

### 功能建议

提交 Issue 时请说明：

1. **需求描述** - 你希望实现什么功能
2. **使用场景** - 为什么需要这个功能
3. **实现思路** - 如果有想法的话

---

## 联系方式

- GitHub Issues: https://github.com/zhang123999-qq/DjangoBlog/issues
- GitHub Discussions: https://github.com/zhang123999-qq/DjangoBlog/discussions

---

再次感谢你的贡献！ 💕
