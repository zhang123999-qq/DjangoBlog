#!/bin/bash
# ============================================================
# DjangoBlog 静态资源优化脚本
# 用途：图片 WebP 转换 + 压缩
# 依赖：cwebp (libwebp-tools)
# ============================================================

set -e

# 配置
STATIC_DIR="/www/wwwroot/DjangoBlog/static"
BACKUP_DIR="/www/wwwroot/DjangoBlog/static_backup_$(date +%Y%m%d)"
QUALITY=80

echo "========================================"
echo "DjangoBlog 静态资源优化"
echo "========================================"

# 检查 cwebp 是否安装
if ! command -v cwebp &> /dev/null; then
    echo "[安装] libwebp-tools..."
    apt-get update && apt-get install -y libwebp-tools
fi

# 备份原始文件
echo "[备份] 原始静态文件 -> $BACKUP_DIR"
cp -r "$STATIC_DIR/img" "$BACKUP_DIR"

# 统计
TOTAL=0
SAVED=0

# 转换 PNG/JPG 为 WebP
echo "[转换] PNG/JPG -> WebP (质量: $QUALITY%)"
find "$STATIC_DIR/img" -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \) | while read img; do
    webp_path="${img%.*}.webp"
    
    # 转换
    cwebp -q $QUALITY "$img" -o "$webp_path" 2>/dev/null
    
    # 计算节省空间
    orig_size=$(stat -f%z "$img" 2>/dev/null || stat -c%s "$img")
    webp_size=$(stat -f%z "$webp_path" 2>/dev/null || stat -c%s "$webp_path")
    saved=$((orig_size - webp_size))
    
    echo "  ✓ $(basename "$img") -> $(basename "$webp_path") (节省 $((saved / 1024))KB)"
done

echo ""
echo "========================================"
echo "转换完成！"
echo ""
echo "后续步骤："
echo "1. 检查 WebP 图片是否正常"
echo "2. 修改模板使用 WebP 图片"
echo "3. 运行: python manage.py collectstatic --noinput"
echo "========================================"
