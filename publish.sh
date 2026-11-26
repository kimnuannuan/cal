#!/usr/bin/env bash
# 生成订阅源（仓库根目录的 shift.ics / ercall.ics）并自校验。不推送。
set -euo pipefail
cd "$(dirname "$0")"

python3 scripts/make_ics.py --name 本人 --month 2026-12 --short \
        --out shift.ics specs/shift.txt
python3 scripts/make_night_ics.py --name 本人 --label 二唤 --month 2026-12 \
        --out ercall.ics specs/ercall.txt

# 日历显示名（订阅后日历列表里看到的名字）
python3 - <<'PY'
import pathlib
fix = {
    'shift.ics':  ('X-WR-CALNAME:2026-12 排班 本人', 'X-WR-CALNAME:排班 2026-12'),
    'ercall.ics': ('X-WR-CALNAME:2026-12 二唤 本人', 'X-WR-CALNAME:二唤 2026-12'),
}
for f, (old, new) in fix.items():
    p = pathlib.Path(f)
    raw = p.read_bytes()
    if old.encode() in raw:
        p.write_bytes(raw.replace(old.encode(), new.encode()))
    print(f, '→', new)
PY

rm -rf dist
echo "生成完毕：$(ls -1 shift.ics ercall.ics | tr '\n' ' ')"
