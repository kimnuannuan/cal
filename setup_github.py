#!/usr/bin/env python3
"""一次性：建仓 + 开 Pages。凭证从同目录 .git_token 读取，不经过命令行。"""
import json
import os
import urllib.error
import urllib.request

_here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_here, ".git_token")) as fh:
    _pat = fh.read().strip()

HDRS = {
    "Authorization": "Bearer " + _pat,
    "Accept": "application/vnd.github+json",
    "Content-Type": "application/json",
    "X-GitHub-Api-Version": "2022-11-28",
}
ROOT = "https://api.github.com"


def call(method, path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(ROOT + path, data=data, method=method, headers=HDRS)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


st, d = call("POST", "/user/repos", {
    "name": "cal", "private": False, "auto_init": False,
    "description": "read-only calendar feeds"})
print("create repo:", st, d.get("full_name") or d.get("message"), d.get("errors") or "")

st, d = call("POST", "/repos/kimnuannuan/cal/pages",
             {"source": {"branch": "main", "path": "/"}})
print("enable pages:", st, d.get("html_url") or d.get("message") or d)
