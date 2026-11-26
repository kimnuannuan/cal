#!/usr/bin/env bash
# 重新生成 dist/*.ics（订阅源）→ 校验 → 提交并推送
set -euo pipefail
cd "$(dirname "$0")"

python3 scripts/make_ics.py --name 本人 --month 2026-12 --short \
        --out dist/shift.ics specs/shift.txt
python3 scripts/make_night_ics.py --name 本人 --label 二唤 --month 2026-12 \
        --out dist/ercall.ics specs/ercall.txt

# 日历显示名（订阅后 iOS「日历」列表里看到的名字）
python3 - <<'PY'
import pathlib
fix = {
    'dist/shift.ics':  ('X-WR-CALNAME:2026-12 排班 本人',  'X-WR-CALNAME:排班 2026-12'),
    'dist/ercall.ics': ('X-WR-CALNAME:2026-12 二唤 本人',  'X-WR-CALNAME:二唤 2026-12'),
}
for f,(old,new) in fix.items():
    p = pathlib.Path(f); raw = p.read_bytes()
    if old.encode() in raw:
        p.write_bytes(raw.replace(old.encode(), new.encode()))
    print(f, '→', new)
PY

git add -A
git commit -m "update $(date +%F\ %H:%M)" || echo "无变更"
git push
echo "订阅地址（deploy 后 1-2 分钟生效）："
echo "  白班  https://<用户名>.github.io/<仓库名>/shift.ics"
echo "  二唤  https://<用户名>.github.io/<仓库名>/ercall.ics"
