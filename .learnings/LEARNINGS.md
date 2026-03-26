# LEARNINGS
## [LRN-20260325-001] best_practice

**Logged**: 2026-03-25T23:45:30+08:00
**Priority**: high
**Status**: pending
**Area**: frontend

### Summary
模板现代化重构中，先抽公共样式层再逐模板迁移，可显著降低返工。

### Details
本次 UI 改造采用了“先建立样式基础设施，再做模板替换”的顺序：
- 先新增 `ui-modern.css` / `admin-modern.css` / `tools-modern.css`
- 再逐页把 inline style 替换为原子类/组件类
这种方式使后续模板改造速度加快、风险降低，且便于统一视觉 token。

### Suggested Action
今后所有前端改造默认采用：
1) 建立公共样式层
2) 小步替换模板
3) 每阶段模板编译 + 回归用例验证

### Metadata
- Source: conversation
- Related Files: static/css/ui-modern.css, static/css/admin-modern.css, static/css/tools-modern.css
- Tags: ui, css-architecture, refactor
- Pattern-Key: best_practice.css_layer_first
- Recurrence-Count: 1
- First-Seen: 2026-03-25
- Last-Seen: 2026-03-25

---

## [LRN-20260325-002] best_practice

**Logged**: 2026-03-25T23:46:00+08:00
**Priority**: high
**Status**: pending
**Area**: frontend

### Summary
超长 Django 模板应组件化（include）以降低语法错误与维护成本。

### Details
`tool_detail.html` 的结果渲染分支过长，历史上多次出现尾部残片/`endblock` 异常风险。拆分到 `templates/tools/includes/result_blocks.html` 后：
- 主模板职责清晰（布局/表单/侧栏）
- 结果类型扩展只改 include
- 模板编译问题更易定位

### Suggested Action
将“超长条件渲染模板组件化”写入工作规范：当 if/elif 分支超过阈值（如 >120 行）默认拆分 include。

### Metadata
- Source: conversation
- Related Files: templates/tools/tool_detail.html, templates/tools/includes/result_blocks.html
- Tags: django-template, maintainability, componentization
- Pattern-Key: best_practice.template_componentize_long_branch
- Recurrence-Count: 1
- First-Seen: 2026-03-25
- Last-Seen: 2026-03-25

---

## [LRN-20260325-003] best_practice

**Logged**: 2026-03-25T23:46:30+08:00
**Priority**: medium
**Status**: pending
**Area**: tests

### Summary
发布门禁脚本不可用时，应执行“等效门禁命令矩阵”保障结论可追溯。

### Details
当 `deploy/test-gate.bat` 受终端编码影响不可稳定执行，改为手动逐项执行等效命令（py_compile / check / deploy-check / mypy / flake8 / regression pytest），并形成文档化验收记录，保证结果可信且可复核。

### Suggested Action
在发布文档中固化“脚本故障降级流程”，并补充命令模板与验收判定标准。

### Metadata
- Source: conversation
- Related Files: docs/ui-modernization-phase6-final-gate-2026-03-25.md, deploy/test-gate.bat
- Tags: release-gate, fallback, reliability
- Pattern-Key: best_practice.release_gate_fallback_matrix
- Recurrence-Count: 1
- First-Seen: 2026-03-25
- Last-Seen: 2026-03-25

---
