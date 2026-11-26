#!/usr/bin/env python3
"""排班 → .ics 生成器（UTF-8 无 BOM / CRLF / 全天事件 / 前一天 20:00 提醒 / 自校验）

用法:
    python3 make_ics.py --name 金欣星 --out /home/ubuntu/schedules/2026-12_金欣星_排班.ics spec.txt

spec.txt 每行一条（`#` 开头为注释，空行忽略）:
    2026-12-03|余杭|手术
    2026-12-12|庆春|门诊+会诊|全天
    2026-12-25|庆春|门诊·上午|下午休

也接受 JSON: [{"date":"2026-12-03","place":"余杭","duty":"手术","note":""}, ...]

输出: 写文件 + 打印 日期/星期/院区·班型 摘要 + 结构校验结果。
"""
import argparse
import datetime
import json
import pathlib
import sys

WEEKDAY = "一二三四五六日"
PLACES = {
    "余杭": "浙大一院 余杭院区",
    "庆春": "浙大一院 庆春院区",
    "钱塘": "浙大一院 钱塘院区",
    "之江": "浙大一院 之江院区",
}

# 用户 2026-11-26 定的标题缩写口径：院区首字 + 门/术/病 + （有会诊时加“会”）
#   余杭·手术=余术  钱塘·门诊+会诊=钱门会  庆春·病理=庆病  之江·门诊=之门
DUTY_ABBR = {"门诊": "门", "手术": "术", "病理": "病", "门诊·上午": "门上"}


def abbr(place: str, duty: str) -> str:
    """院区首字 + 门/术/病 +（会诊时加“会”）。"""
    head = place[0] if place else ""
    base = duty.replace("+会诊", "").strip()   # 先剥掉“+会诊”，再查表
    body = DUTY_ABBR.get(base)
    if body is None:
        body = base  # 未知班型原样保留，便于人工发现
    tail = "会" if "会诊" in duty else ""
    return f"{head}{body}{tail}"


def _load(spec_path: str):
    p = pathlib.Path(spec_path)
    txt = p.read_text(encoding="utf-8-sig")
    rows = []
    if p.suffix.lower() == ".json":
        for r in json.loads(txt):
            rows.append((r["date"], r["place"], r["duty"], r.get("note", "") or ""))
    else:
        for line in txt.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [x.strip() for x in line.split("|")]
            parts += [""] * (4 - len(parts))
            rows.append(tuple(parts[:4]))
    return rows


def _esc(value: str) -> str:
    """RFC 5545 TEXT 转义。"""
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
    )


def _fold(line: str, limit: int = 73) -> str:
    """按 RFC 5545 折行（续行以单个空格开头），避免客户端截断长行。"""
    out = []
    while len(line.encode("utf-8")) > limit:
        cut = limit
        while len(line[:cut].encode("utf-8")) > limit:
            cut -= 1
        out.append(line[:cut])
        line = " " + line[cut:]
    out.append(line)
    return "\r\n".join(out)


def build(name: str, rows, cal_month: str, alarm: bool = False, short: bool = False) -> str:
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:-//Hermes//Duty {cal_month}//CN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_esc(cal_month + ' 排班 ' + name)}",
        "X-WR-TIMEZONE:Asia/Shanghai",
    ]
    for date_s, place, duty, note in rows:
        d = datetime.date.fromisoformat(date_s)
        d_end = d + datetime.timedelta(days=1)
        full = f"{place}·{duty}"
        summary = abbr(place, duty) if short else full
        desc_bits = [f"{name}｜{cal_month} 排班｜来源 科室周排班表"]
        if short:
            desc_bits.append(full)
        if note:
            desc_bits.append(note)
        lines += [
            "BEGIN:VEVENT",
            f"UID:{name}-{d.strftime('%Y%m%d')}@hermes.local",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{d.strftime('%Y%m%d')}",
            f"DTEND;VALUE=DATE:{d_end.strftime('%Y%m%d')}",
            _fold("SUMMARY:" + _esc(summary)),
            _fold("LOCATION:" + _esc(PLACES.get(place, "浙大一院 " + place + "院区"))),
            _fold("DESCRIPTION:" + _esc("｜".join(desc_bits))),
            "TRANSP:OPAQUE",
            "END:VEVENT",
        ]
        if alarm:
            lines.insert(-1, "BEGIN:VALARM")
            lines.insert(-1, "TRIGGER:-PT15H")
            lines.insert(-1, "ACTION:DISPLAY")
            lines.insert(-1, "DESCRIPTION:明天有排班")
            lines.insert(-1, "END:VALARM")
    lines.append("END:VCALENDAR")
    # CRLF 行尾；不写 BOM
    return "\r\n".join(lines) + "\r\n"


def verify(path: pathlib.Path, alarm: bool = False) -> bool:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    checks = {
        "无BOM": not raw.startswith(b"\xef\xbb\xbf"),
        "CRLF行尾": raw.count(b"\r\n") >= 10,
        "BEGIN起始": text.startswith("BEGIN:VCALENDAR"),
        "END结尾": text.rstrip().endswith("END:VCALENDAR"),
        ("VALARM配对" if alarm else "无VALARM"): (
            raw.count(b"BEGIN:VALARM") == raw.count(b"END:VALARM") > 0
            if alarm else raw.count(b"BEGIN:VALARM") == 0
        ),
        "VEVENT配对": raw.count(b"BEGIN:VEVENT") == raw.count(b"END:VEVENT"),
    }
    ok = all(checks.values())
    print("  校验: " + "  ".join(("✓" if v else "✗") + k for k, v in checks.items()))
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, help="姓名，如 金欣星")
    ap.add_argument("--out", required=True, help="输出 .ics 路径")
    ap.add_argument("--month", default="", help="日历名月份，如 2026-12；省略则取首条日期")
    ap.add_argument("--alarm", action="store_true",
                    help="在 ics 内写 VALARM（默认不写：提醒统一走 QQ cron，避免重复）")
    ap.add_argument("--short", action="store_true",
                    help="标题用缩写（余术/钱门会/庆门），全称仍写进 DESCRIPTION")
    ap.add_argument("spec", help="spec.txt 或 spec.json")
    a = ap.parse_args()

    rows = _load(a.spec)
    if not rows:
        print("spec 为空", file=sys.stderr)
        return 2
    month = a.month or rows[0][0][:7]

    rows.sort(key=lambda r: r[0])
    print(f"{a.name} {month} 共 {len(rows)} 条")
    for date_s, place, duty, note in rows:
        d = datetime.date.fromisoformat(date_s)
        print(f"  {d.month:02d}-{d.day:02d} 周{WEEKDAY[d.weekday()]}  {place}·{duty}" + (f"（{note}）" if note else ""))

    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(build(a.name, rows, month, a.alarm, a.short).encode("utf-8"))
    print(f"  写出 {out}（{out.stat().st_size} bytes）")
    return 0 if verify(out, a.alarm) else 1


if __name__ == "__main__":
    raise SystemExit(main())
