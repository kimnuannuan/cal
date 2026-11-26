#!/usr/bin/env python3
"""夜班（一唤/二唤/三唤）→ .ics 生成器

用户口径（2026-11-26 确认，勿改）：
  * SUMMARY 只写班名，如「二唤」—— 不带时段；
  * 时长 = 当日 17:00 → 当日 24:00，**不跨天**；
  * 文件内**不写 VALARM**（提醒统一由 QQ cron 推送）。

时间用 UTC 表达：17:00 CST = 09:00Z；当日 24:00 CST = 当日 16:00Z。

用法：
    python3 make_night_ics.py --name 金欣星 --label 二唤 --month 2026-12 \
        --out /path/2026-12_金欣星_二唤.ics spec.txt

spec.txt 每行（`#` 注释）：
    2026-12-08|一唤:郑一禾|三唤:王苏
    2026-12-19|一唤:吕添|三唤:罗丽敏
"""
import argparse
import datetime
import pathlib
import sys

WEEKDAY = "一二三四五六日"


def _load(path):
    rows = []
    for line in pathlib.Path(path).read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [x.strip() for x in line.split("|")]
        parts += [""] * (4 - len(parts))
        rows.append(tuple(parts[:4]))
    return rows


def _esc(v):
    return (str(v).replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\r\n", "\\n").replace("\n", "\\n"))


def _fold(line, limit=73):
    out = []
    while len(line.encode()) > limit:
        cut = limit
        while len(line[:cut].encode()) > limit:
            cut -= 1
        out.append(line[:cut])
        line = " " + line[cut:]
    out.append(line)
    return "\r\n".join(out)


def build(name, label, rows, month):
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR", "VERSION:2.0",
        f"PRODID:-//Hermes//NightDuty {month}//CN",
        "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_esc(month + ' ' + label + ' ' + name)}",
        "X-WR-TIMEZONE:Asia/Shanghai",
    ]
    for date_s, peer1, peer3, _ in rows:
        d = datetime.date.fromisoformat(date_s)
        desc = [f"{name}｜{label}值班｜当日 17:00-24:00",
                "负责各院区夜班会诊；联系三唤；三唤负责院外会诊"]
        if peer1:
            desc.append(peer1)
        if peer3:
            desc.append(peer3)
        lines += [
            "BEGIN:VEVENT",
            f"UID:{name}-{label}-{d.strftime('%Y%m%d')}@hermes.local",
            f"DTSTAMP:{stamp}",
            f"DTSTART:{d.strftime('%Y%m%d')}T090000Z",   # 17:00 CST
            f"DTEND:{d.strftime('%Y%m%d')}T160000Z",     # 当日 24:00 CST（不跨天）
            _fold("SUMMARY:" + _esc(label)),
            _fold("LOCATION:" + _esc("浙大一院（各院区夜班会诊）")),
            _fold("DESCRIPTION:" + _esc("｜".join(desc))),
            "TRANSP:OPAQUE",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def verify(path):
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    checks = {
        "无BOM": not raw.startswith(b"\xef\xbb\xbf"),
        "CRLF行尾": raw.count(b"\r\n") >= 5,
        "BEGIN起始": text.startswith("BEGIN:VCALENDAR"),
        "END结尾": text.rstrip().endswith("END:VCALENDAR"),
        "无VALARM": raw.count(b"BEGIN:VALARM") == 0,
        "VEVENT配对": raw.count(b"BEGIN:VEVENT") == raw.count(b"END:VEVENT")
                      and raw.count(b"BEGIN:VEVENT") > 0,
    }
    print("  校验: " + "  ".join(("✓" if v else "✗") + k for k, v in checks.items()))
    return all(checks.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--label", default="二唤")
    ap.add_argument("--out", required=True)
    ap.add_argument("--month", default="")
    ap.add_argument("spec")
    a = ap.parse_args()

    rows = sorted(_load(a.spec), key=lambda r: r[0])
    if not rows:
        print("spec 为空", file=sys.stderr)
        return 2
    month = a.month or rows[0][0][:7]
    print(f"{a.name} {month} {a.label} 共 {len(rows)} 条")
    for date_s, p1, p3, _ in rows:
        d = datetime.date.fromisoformat(date_s)
        print(f"  {d.month:02d}-{d.day:02d} 周{WEEKDAY[d.weekday()]}  {a.label}"
              + (f"（{p1} / {p3}）" if p1 or p3 else ""))

    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(build(a.name, a.label, rows, month).encode("utf-8"))
    print(f"  写出 {out}（{out.stat().st_size} bytes）")
    return 0 if verify(out) else 1


if __name__ == "__main__":
    raise SystemExit(main())
