# 贡献指南

感谢你对 DjangoBlog 项目的关注！欢迎参与贡献。

## 🤝 如何贡献

### 报告问题

如果你发现了 bug 或有功能建议：

1. 在 [Issues](https://github.com/zhang123999-qq/DjangoBlog/issues) 页面搜索是否已有相关问题
2. 如果没有，创建新的 Issue，详细描述问题或建议

### 提交代码

1. **Fork 本仓库**

2. **克隆到本地**
   ```bash
   git clone https://github.com/your-username/DjangoBlog.git
   cd DjangoBlog
   ```

3. **创建虚拟环境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate     # Windows
   ```

4. **安装依赖**
   ```bash
   # 使用 pyproject.toml（推荐）
   pip install -e ".[dev]"
   
   # 或使用 requirements
   pip install -r requirements/development.txt
   ```

5. **创建功能分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

6. **进行修改并测试**

7. **提交更改**
   ```bash
   git add .
   git commit -m "Add: your feature description"
   ```

8. **推送到 Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

9. **创建 Pull Request**

## 📝 代码规范

- 遵循 PEP 8 代码风格
- 使用有意义的变量名和函数名
- 添加必要的注释和文档字符串
- 编写单元测试

## 🔧 项目结构

```
DjangoBlog/
├── apps/                 # 应用目录
│   ├── accounts/         # 用户账户
│   ├── blog/             # 博客功能
│   ├── forum/            # 论坛功能
│   ├── tools/            # 工具栏
│   └── install/          # 安装向导
├── config/               # 配置文件
├── templates/            # 模板文件
├── static/               # 静态文件
└── requirements/         # 依赖文件
```

## 🧪 运行测试

```bash
python manage.py test
```

## 📄 许可证

提交代码即表示你同意你的代码将在 MIT 许可证下发布。

---

再次感谢你的贡献！🙏
