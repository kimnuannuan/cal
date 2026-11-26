#!/usr/bin/env bash
# 一条命令更新线上订阅：生成 → 校验 → 提交 → 推送（凭证走 .git_token，不进命令行）
set -euo pipefail
cd "$(dirname "$0")"
./publish.sh
git add -A
git -c user.name="hermes" -c user.email="hermes@local" commit -m "update $(date '+%F %H:%M')" || echo "（无变更）"
python3 push_main.py
echo "线上地址："
echo "  白班  https://kimnuannuan.github.io/cal/shift.ics"
echo "  二唤  https://kimnuannuan.github.io/cal/ercall.ics"
