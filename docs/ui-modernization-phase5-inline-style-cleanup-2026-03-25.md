# UI 现代化重排（Phase 5 - Tools 内联样式清扫）

## 目标

对工具页剩余内联样式做收尾清理，统一复用 `tools-modern.css` 中的原子/组件类，并做模板与回归验证。

## 本次改动

- `templates/tools/tool_list.html`
  - `clear-search` / `search-hint` 初始隐藏由 inline 改为 `u-hidden`
  - 搜索与分类图标颜色统一使用 CSS 变量表达（动态色值保留）
  - 工具描述字号统一类 `tool-desc-sm`
  - 清理模板尾部残留脚本碎片，修复潜在 `endblock` 语法错误

- `templates/tools/nat_detector.html`
  - 结果区初始隐藏改为 `u-hidden`

- `templates/tools/ip_detector.html`
  - 信息列宽由 inline 改为 `u-cell-w-80`

- `templates/tools/gitignore_generator.html`
  - 空态大图标样式改为 `u-icon-40`

## 验证

1) 模板编译加载（逐个）
- `tools/tool_list.html`
- `tools/tool_detail.html`
- `tools/includes/result_blocks.html`
- `tools/ip_detector.html`
- `tools/nat_detector.html`
- `tools/gitignore_generator.html`
- `tools/json_formatter_enhanced.html`

结果：全部 `ok`

2) 后端回归抽测
- `uv run pytest -q tests/test_core_backend_suite.py tests/test_core_backend_suite_ext.py tests/test_core_backend_suite_ops.py --maxfail=1`
- 结果：`37 passed`

## 备注

- 工具页中仍保留少量 `style="--cat-color: ..."`，属于动态主题色传参（有意保留）。
- 继续遵循策略：仅本地提交，不 push。