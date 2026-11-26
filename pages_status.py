#!/usr/bin/env python3
"""查看 Pages 站点状态与构建结果。"""
import json
import os
import urllib.error
import urllib.request

_here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_here, ".git_token")) as fh:
    _pat = fh.read().strip()

HDRS = {"Authorization": "Bearer " + _pat, "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"}


def get(path):
    req = urllib.request.Request("https://api.github.com" + path, headers=HDRS)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


st, d = get("/repos/kimnuannuan/cal/pages")
print("pages:", st, {k: d.get(k) for k in ("html_url", "status", "cname", "custom_404")})

st, d = get("/repos/kimnuannuan/cal/pages/builds/latest")
print("latest build:", st, {k: d.get(k) for k in ("status", "error", "duration", "created_at", "updated_at")})
