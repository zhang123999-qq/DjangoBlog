# 快速部署指南

本文档介绍如何使用 `run.py` 脚本快速部署 DjangoBlog。

## 快速开始

### 一键安装

```bash
# 开发环境（默认）
python run.py

# 生产环境
python run.py --prod
```

### 启动服务器

```bash
# 开发服务器
python start.py

# 允许局域网访问
python start.py --lan

# 指定端口
python start.py --port 8080
```

## run.py 详细说明

### 命令行参数

| 参数 | 说明 |
|------|------|
| `--prod` | 生产环境安装（包含 Gunicorn） |
| `--dev` | 开发环境安装（默认） |
| `--skip-migration` | 跳过数据库迁移 |
| `--skip-static` | 跳过静态文件收集 |
| `--no-input` | 非交互模式（使用默认值） |

### 安装步骤

`run.py` 会自动执行以下步骤：

1. **检查系统环境** - 检测 Python 版本和 pip
2. **创建虚拟环境** - 在项目目录创建 `.venv`
3. **安装依赖** - 根据环境安装对应依赖
4. **配置环境变量** - 创建 `.env` 文件
5. **执行数据库迁移** - 创建数据库表
6. **收集静态文件** - 收集到 `staticfiles/`
7. **创建管理员账户** - 交互式创建超级用户
8. **安装 Gunicorn** - 仅生产环境

### 使用示例

#### 场景 1: 本地开发

```bash
# 克隆项目
git clone https://github.com/zhang123999-qq/DjangoBlog.git
cd DjangoBlog

# 一键安装
python run.py

# 启动服务器
python start.py
```

#### 场景 2: 服务器部署

```bash
# 生产环境安装
python run.py --prod

# 启动生产服务器（Linux/Mac）
./start_server.sh

# 或手动启动
source .venv/bin/activate
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

#### 场景 3: Docker 环境

```bash
# 构建镜像
docker build -t djangoblog .

# 运行容器
docker run -p 8000:8000 djangoblog
```

## start.py 详细说明

### 命令行参数

| 参数 | 说明 |
|------|------|
| `--lan` | 允许局域网访问（绑定 0.0.0.0） |
| `--port PORT` | 指定端口（默认 8000） |
| `--no-browser` | 不自动打开浏览器 |
| `--debug` | 启用调试模式 |

### 使用示例

```bash
# 默认启动（仅本机访问）
python start.py

# 局域网访问
python start.py --lan

# 自定义端口
python start.py --port 3000

# 组合使用
python start.py --lan --port 8080
```

## 生成的文件

运行 `run.py` 后会生成以下文件：

```
DjangoBlog/
├── .env                    # 环境变量配置
├── .venv/                  # 虚拟环境目录
├── db.sqlite3              # SQLite 数据库
├── staticfiles/            # 收集的静态文件
├── start_server.sh         # Linux/Mac 启动脚本
└── start_server.bat        # Windows 启动脚本
```

## 环境要求

- Python 3.10+
- pip 或 uv（推荐）
- Git（可选）

## 常见问题

### Q: Python 版本不满足要求？

A: 安装 Python 3.10 或更高版本。推荐使用 Python 3.12。

### Q: pip 安装失败？

A: 尝试使用 uv：
```bash
pip install uv
python run.py
```

### Q: 数据库迁移失败？

A: 检查是否有其他进程占用数据库文件，或删除 `db.sqlite3` 重新运行。

### Q: 静态文件收集失败？

A: 确保 `DEBUG=True` 在开发环境中，或检查 `STATIC_ROOT` 配置。

### Q: 如何重置安装？

A: 删除以下文件/目录后重新运行：
```bash
rm -rf .venv db.sqlite3 .env staticfiles/
python run.py
```

## 手动安装

如果 `run.py` 无法正常工作，可以手动安装：

```bash
# 1. 创建虚拟环境
python -m venv .venv

# 2. 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements/development.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 5. 数据库迁移
python manage.py migrate

# 6. 创建管理员
python manage.py createsuperuser

# 7. 启动服务器
python manage.py runserver
```

## 生产部署建议

1. **使用 HTTPS** - 配置 SSL 证书
2. **设置 DEBUG=False** - 禁用调试模式
3. **修改 SECRET_KEY** - 使用随机生成的密钥
4. **使用 MySQL/PostgreSQL** - 替换 SQLite
5. **配置 Redis** - 启用缓存
6. **使用 Nginx** - 反向代理和静态文件
7. **配置 Supervisor** - 进程守护

详细部署说明请参考 [DEPLOYMENT.md](DEPLOYMENT.md)
