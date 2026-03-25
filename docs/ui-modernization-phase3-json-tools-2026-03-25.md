# UI 现代化重排（Phase 3 - JSON 工具页）

## 目标

将 `json_formatter_enhanced.html` 从历史混乱模板重构为现代可维护结构，统一到工具页设计语言。

## 改动

- 重写文件：`templates/tools/json_formatter_enhanced.html`

## 关键优化

1. 模板结构标准化
- 统一使用 `base.html` + `content/extra_css/extra_js` block
- 与工具页一致的面包屑与容器排版

2. 编辑器区域现代化
- 双栏 Monaco 编辑器
- 实时字符/行数统计
- 格式化 / 压缩 / 清空 / 示例 / 复制
- 快捷键 `Ctrl+Enter` 格式化

3. 交互反馈优化
- 统一 toast 组件（成功/错误）
- 移除旧版分散脚本片段与样式残留

4. 业务安全性
- 顶层排序仅对 object 生效，避免数组误处理
- JSON 异常统一错误提示

## 验证

- 模板编译：`tools-phase3-templates-ok`
- 回归抽测：`uv run pytest -q tests/test_core_backend_suite.py --maxfail=1` -> `10 passed`