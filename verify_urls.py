#!/usr/bin/env python3
"""验证两个订阅 URL 的 HTTP 状态与 Content-Type（iOS 订阅只认 text/calendar）。"""
import sys
import time
import urllib.error
import urllib.request

URLS = [
    "https://kimnuannuan.github.io/cal/shift.ics",
    "https://kimnuannuan.github.io/cal/ercall.ics",
]


def head(url):
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "curl/8"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.headers.get("Content-Type"), len(r.read())
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type"), 0
    except Exception as e:  # 网络超时等
        return None, type(e).__name__, 0


for attempt in range(1, 13):
    rows = [(u, head(u)) for u in URLS]
    print(f"--- 第 {attempt} 次 ---")
    ok = True
    for u, (st, ct, n) in rows:
        print(f"  {st} | {ct} | {n} bytes | {u.rsplit('/', 1)[-1]}")
        if st != 200 or not (ct or "").startswith("text/calendar"):
            ok = False
    if ok:
        print("✅ 两个订阅源均可用（200 + text/calendar）")
        sys.exit(0)
    time.sleep(15)
print("⚠️ 超时仍未就绪，检查 Pages 构建或改用 jsDelivr")
sys.exit(1)
