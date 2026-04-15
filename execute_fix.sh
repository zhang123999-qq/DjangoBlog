#!/bin/bash
# ============================================
# 一键执行：DjangoBlog 依赖修复
# ============================================

echo "=========================================="
echo "DjangoBlog 依赖修复 - 一键执行"
echo "=========================================="

# 切换到项目目录
cd /mnt/f/DjangoBlog

# 检查是否在正确的分支
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "fix/dependency-compatibility" ]; then
    echo "❌ 错误：当前分支是 $CURRENT_BRANCH"
    echo "请切换到 fix/dependency-compatibility 分支"
    exit 1
fi

# 检查是否有未提交的更改
if git diff-index --quiet HEAD --; then
    echo "✅ 工作区干净"
else
    echo "⚠️  有未提交的更改"
    git status --short
fi

# 显示待推送的提交
echo ""
echo "📋 待推送的提交："
git log --oneline origin/main..HEAD

echo ""
echo "=========================================="
echo "修改摘要"
echo "=========================================="
echo ""
echo "修改文件："
echo "  1. pyproject.toml"
echo "  2. requirements/base.txt"
echo ""
echo "修改内容："
echo "  django-filter>=23.0 → django-filter>=23.0,<25.0"
echo ""
echo "原因："
echo "  django-filter 25.2 放弃了对 Django <5.2 LTS 的支持"
echo ""

# 显示下一步操作
echo "=========================================="
echo "下一步操作"
echo "=========================================="
echo ""
echo "请选择推送方式："
echo ""
echo "1️⃣  使用 GitHub Token (HTTPS)"
echo "   命令："
echo "   git remote set-url origin https://YOUR_TOKEN@github.com/zhang123999-qq/DjangoBlog.git"
echo "   git push origin fix/dependency-compatibility"
echo ""
echo "2️⃣  使用 SSH"
echo "   命令："
echo "   git remote set-url origin git@github.com:zhang123999-qq/DjangoBlog.git"
echo "   git push origin fix/dependency-compatibility"
echo ""
echo "3️⃣  运行完整脚本"
echo "   命令："
echo "   ./push_fix.sh"
echo ""
echo "=========================================="
echo "推送后操作"
echo "=========================================="
echo ""
echo "📌 创建 PR："
echo "   https://github.com/zhang123999-qq/DjangoBlog/compare/fix/dependency-compatibility"
echo ""
echo "📌 关闭 PR #24："
echo "   https://github.com/zhang123999-qq/DjangoBlog/pull/24"
echo ""
echo "📌 PR 模板："
echo "   查看 PR_TEMPLATE.md"
echo ""
echo "=========================================="
