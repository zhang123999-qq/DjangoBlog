#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
一键设置 DjangoBlog 页脚备案号。

默认修改文件：templates/includes/footer.html

用法示例：
  uv run python scripts/set_beian_footer.py --number "粤ICP备12345678号"
  uv run python scripts/set_beian_footer.py --number "粤ICP备12345678号" --url "https://beian.miit.gov.cn/"
  uv run python scripts/set_beian_footer.py --remove
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_FOOTER = BASE_DIR / "templates" / "includes" / "footer.html"

BEGIN_MARKER = "<!-- BEIAN_BLOCK:BEGIN -->"
END_MARKER = "<!-- BEIAN_BLOCK:END -->"


def safe_print(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "ignore").decode("ascii"))


def build_beian_block(number: str, url: str) -> str:
    number_escaped = html.escape(number, quote=True)
    url_escaped = html.escape(url, quote=True)

    link_html = (
        f'<a href="{url_escaped}" class="text-gray-400 hover:text-white transition-all" '
        f'target="_blank" rel="noopener noreferrer">{number_escaped}</a>'
    )

    return (
        f"\n{BEGIN_MARKER}\n"
        f"<div class=\"row mt-2\">\n"
        f"    <div class=\"col-12\">\n"
        f"        <p class=\"text-gray-400 mb-0\">备案号：{link_html}</p>\n"
        f"    </div>\n"
        f"</div>\n"
        f"{END_MARKER}\n"
    )


def remove_existing_block(content: str) -> tuple[str, bool]:
    pattern = re.compile(
        rf"\n?{re.escape(BEGIN_MARKER)}.*?{re.escape(END_MARKER)}\n?",
        flags=re.DOTALL,
    )
    new_content, n = pattern.subn("\n", content, count=1)
    return new_content, n > 0


def upsert_beian(content: str, block: str) -> tuple[str, str]:
    # 先移除旧块，保证幂等
    cleaned, existed = remove_existing_block(content)

    insert_point = cleaned.rfind("</footer>")
    if insert_point == -1:
        raise ValueError("未找到 </footer>，无法插入备案信息")

    new_content = cleaned[:insert_point] + block + cleaned[insert_point:]
    return new_content, "updated" if existed else "inserted"


def backup_file(path: Path) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_suffix(path.suffix + f".bak.{stamp}")
    shutil.copy2(path, backup_path)
    return backup_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="一键设置页脚备案号")
    parser.add_argument(
        "--number",
        help="备案号，例如：粤ICP备12345678号。与 --remove 二选一",
    )
    parser.add_argument(
        "--url",
        default="https://beian.miit.gov.cn/",
        help="备案号跳转链接，默认工信部备案查询页",
    )
    parser.add_argument(
        "--path",
        default=str(DEFAULT_FOOTER),
        help="footer.html 路径，默认 templates/includes/footer.html",
    )
    parser.add_argument("--remove", action="store_true", help="删除已写入的备案块")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不写入")
    parser.add_argument("--no-backup", action="store_true", help="写入前不创建备份")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.remove and args.number:
        safe_print("[错误] --remove 与 --number 不能同时使用")
        return 1

    if not args.remove and not args.number:
        safe_print("[错误] 请提供 --number，或使用 --remove")
        return 1

    footer_path = Path(args.path).expanduser().resolve()
    if not footer_path.exists():
        safe_print(f"[错误] 文件不存在: {footer_path}")
        return 1

    original = footer_path.read_text(encoding="utf-8")

    if args.remove:
        new_content, removed = remove_existing_block(original)
        if not removed:
            safe_print("[提示] 未发现已写入的备案块，无需删除")
            return 0
        action = "removed"
    else:
        block = build_beian_block(args.number.strip(), args.url.strip())
        try:
            new_content, action = upsert_beian(original, block)
        except ValueError as exc:
            safe_print(f"[错误] {exc}")
            return 1

    if new_content == original:
        safe_print("[提示] 内容无变化")
        return 0

    if args.dry_run:
        safe_print(f"[预览] 变更类型: {action}")
        safe_print("[预览] 使用 --dry-run，未写入文件")
        return 0

    if not args.no_backup:
        bak = backup_file(footer_path)
        safe_print(f"[备份] 已创建: {bak}")

    footer_path.write_text(new_content, encoding="utf-8")
    safe_print(f"[完成] 已{action}备案信息: {footer_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
