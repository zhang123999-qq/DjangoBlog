# ERRORS
## [ERR-20260325-001] deploy-test-gate-bat-encoding-noise

**Logged**: 2026-03-25T23:45:00+08:00
**Priority**: high
**Status**: pending
**Area**: infra

### Summary
`deploy\test-gate.bat` 在当前 Windows 终端出现编码噪声并持续输出乱码，导致批处理执行不可用。

### Error
```
'��' �����ڲ����ⲿ���Ҳ���ǿ����еĳ���
```

### Context
- 触发命令：`deploy\test-gate.bat`
- 行为：进程持续输出乱码，无法正常完成门禁
- 影响：无法直接使用批处理产出可靠门禁结论

### Suggested Fix
1. 为 `test-gate.bat` 提供 UTF-8/ANSI 兼容版本（或纯英文无注释版）
2. 在脚本开头显式设置代码页并验证（如 `chcp 65001 >nul`）
3. 保底方案：提供 PowerShell 版门禁脚本，避免 cmd 编码差异

### Metadata
- Reproducible: yes
- Related Files: deploy/test-gate.bat
- See Also: （无）

---
