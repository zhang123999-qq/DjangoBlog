#!/bin/bash
# ============================================
# DjangoBlog 依赖修复推送脚本
# 功能：推送 fix/dependency-compatibility 分支到 GitHub
# ============================================

set -e  # 遇到错误立即退出

# 配置
REPO_URL="https://github.com/zhang123999-qq/DjangoBlog.git"
BRANCH="fix/dependency-compatibility"

echo "=========================================="
echo "DjangoBlog 依赖修复推送脚本"
echo "=========================================="

# 检查当前目录
if [ ! -d ".git" ]; then
    echo "❌ 错误：当前目录不是 Git 仓库"
    echo "请在 DjangoBlog 项目根目录运行此脚本"
    exit 1
fi

# 检查当前分支
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
    echo "⚠️  警告：当前分支是 $CURRENT_BRANCH，不是 $BRANCH"
    echo "正在切换到 $BRANCH 分支..."
    git checkout $BRANCH
fi

# 显示待推送的提交
echo ""
echo "📋 待推送的提交："
git log --oneline origin/main..HEAD

echo ""
echo "=========================================="
echo "请选择认证方式："
echo "=========================================="
echo "1. 使用 GitHub Token (HTTPS)"
echo "2. 使用 SSH 密钥"
echo "3. 使用 GitHub CLI (gh)"
echo "4. 手动复制命令"
echo ""

read -p "请输入选项 (1-4): " choice

case $choice in
    1)
        echo ""
        echo "📝 使用 GitHub Token 认证"
        echo "----------------------------------------"
        echo "请访问: https://github.com/settings/tokens"
        echo "创建 Personal Access Token (需要 repo 权限)"
        echo ""
        read -p "请输入 GitHub Token: " GITHUB_TOKEN
        
        if [ -z "$GITHUB_TOKEN" ]; then
            echo "❌ Token 不能为空"
            exit 1
        fi
        
        # 临时设置远程 URL（包含 token）
        git remote set-url origin https://$GITHUB_TOKEN@github.com/zhang123999-qq/DjangoBlog.git
        
        echo "🚀 推送中..."
        git push origin $BRANCH
        
        # 恢复原始 URL（移除 token）
        git remote set-url origin https://github.com/zhang123999-qq/DjangoBlog.git
        
        echo "✅ 推送成功！"
        ;;
        
    2)
        echo ""
        echo "📝 使用 SSH 密钥认证"
        echo "----------------------------------------"
        
        # 检查 SSH 密钥
        if [ ! -f ~/.ssh/id_rsa ] && [ ! -f ~/.ssh/id_ed25519 ]; then
            echo "⚠️  未找到 SSH 密钥"
            echo "请先生成 SSH 密钥："
            echo "  ssh-keygen -t ed25519 -C 'your_email@example.com'"
            echo "然后添加到 GitHub: https://github.com/settings/keys"
            exit 1
        fi
        
        # 切换到 SSH URL
        git remote set-url origin git@github.com:zhang123999-qq/DjangoBlog.git
        
        echo "🚀 推送中..."
        git push origin $BRANCH
        
        # 恢复 HTTPS URL
        git remote set-url origin https://github.com/zhang123999-qq/DjangoBlog.git
        
        echo "✅ 推送成功！"
        ;;
        
    3)
        echo ""
        echo "📝 使用 GitHub CLI 认证"
        echo "----------------------------------------"
        
        # 检查 gh CLI
        if ! command -v gh &> /dev/null; then
            echo "❌ 未安装 GitHub CLI"
            echo "请安装: https://cli.github.com/"
            exit 1
        fi
        
        # 检查认证状态
        if ! gh auth status &> /dev/null; then
            echo "请先认证 GitHub CLI："
            gh auth login
        fi
        
        echo "🚀 推送中..."
        git push origin $BRANCH
        
        echo "✅ 推送成功！"
        ;;
        
    4)
        echo ""
        echo "📝 手动推送命令"
        echo "----------------------------------------"
        echo ""
        echo "# 方式 A: 使用 GitHub Token"
        echo "git remote set-url origin https://YOUR_TOKEN@github.com/zhang123999-qq/DjangoBlog.git"
        echo "git push origin $BRANCH"
        echo "git remote set-url origin https://github.com/zhang123999-qq/DjangoBlog.git"
        echo ""
        echo "# 方式 B: 使用 SSH"
        echo "git remote set-url origin git@github.com:zhang123999-qq/DjangoBlog.git"
        echo "git push origin $BRANCH"
        echo "git remote set-url origin https://github.com/zhang123999-qq/DjangoBlog.git"
        echo ""
        echo "# 方式 C: 使用 gh CLI"
        echo "gh auth login"
        echo "git push origin $BRANCH"
        echo ""
        exit 0
        ;;
        
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "🎉 推送完成！"
echo "=========================================="
echo ""
echo "📋 后续步骤："
echo ""
echo "1️⃣  创建 Pull Request："
echo "   访问: https://github.com/zhang123999-qq/DjangoBlog/compare/$BRANCH"
echo "   点击 'Create pull request'"
echo ""
echo "2️⃣  PR 标题："
echo "   fix: 限制django-filter版本范围，确保Django 4.2兼容性"
echo ""
echo "3️⃣  PR 描述："
echo '   ## 问题'
echo '   PR #24 (Dependabot) 要求将 django-filter 从 >=23.0 更新到 >=25.2，'
echo '   但 django-filter 25.2 放弃了对 Django <5.2 LTS 的支持。'
echo ''
echo '   ## 解决方案'
echo '   限制 django-filter 版本范围为 >=23.0,<25.0，确保与 Django 4.2 LTS 兼容。'
echo ''
echo '   ## 影响'
echo '   - 防止未来 Dependabot 创建不兼容的 PR'
echo '   - 保持项目在 Django 4.2 LTS 上的稳定运行'
echo ""
echo "4️⃣  关闭 PR #24："
echo "   访问: https://github.com/zhang123999-qq/DjangoBlog/pull/24"
echo "   点击 'Close pull request'"
echo "   添加评论："
echo '   关闭原因：django-filter 25.2 放弃了对 Django <5.2 LTS 的支持。'
echo '   为保持兼容性，已限制版本范围为 >=23.0,<25.0。'
echo ""
echo "=========================================="
