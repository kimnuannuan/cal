#!/usr/bin/env python3
"""强制触发一次 Pages 构建并等待完成。"""
import json
import os
import time
import urllib.error
import urllib.request

_here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_here, ".git_token")) as fh:
    _pat = fh.read().strip()

HDRS = {"Authorization": "Bearer " + _pat, "Accept": "application/vnd.github+json",
        "Content-Type": "application/json", "X-GitHub-Api-Version": "2022-11-28"}
ROOT = "https://api.github.com"


def call(method, path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(ROOT + path, data=data, method=method, headers=HDRS)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


st, d = call("POST", "/repos/kimnuannuan/cal/pages/builds", {})
print("trigger build:", st, d.get("status"), d.get("message") or "")

for i in range(20):
    time.sleep(8)
    st, d = call("GET", "/repos/kimnuannuan/cal/pages/builds/latest")
    print(f"  {i*8+8}s: {d.get('status')} | {d.get('created_at')} -> {d.get('updated_at')} | err={d.get('error')}")
    if d.get("status") == "built":
        break
