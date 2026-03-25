# UI 现代化重排（Phase 1）

## 范围

- 全站基础样式增强（不改业务逻辑）
- 导航与个人中心排版统一
- 超级管理员后台视觉重排
- 清理部分内联样式与 Bootstrap5 兼容细节

## 改动文件

- `static/css/ui-modern.css`（新增）
- `static/css/admin-modern.css`（新增）
- `templates/base.html`
- `templates/includes/navbar.html`
- `templates/accounts/profile.html`
- `templates/admin/base_site.html`
- `templates/admin/index.html`
- `templates/core/home.html`

## 关键优化点

1. 全站新增 UI token 与组件类
- 统一卡片、圆角、阴影、头像、下拉菜单样式

2. 导航栏与个人中心
- 头像、在线状态点、下拉菜单样式统一
- 去除关键内联样式，转为 class 驱动

3. 超级管理员后台
- 后台主题改为统一现代风格
- index 统计卡颜色体系类化（`is-success/is-warn/...`）
- 删除 index 中重复的内嵌 style block，统一走 `admin-modern.css`

4. Bootstrap5 兼容
- `ml-2` -> `ms-2`

## 验证

- 模板编译加载：`templates-ok`（通过）
- 保持原有 URL/业务逻辑不变

## 后续建议（Phase 2）

- 工具页（tool_list/tool_detail/json_formatter/nat_detector）全面移除内联 style
- 抽离可复用组件 include（卡片头、空状态、统计模块）
- 对 admin change_form 做同主题统一