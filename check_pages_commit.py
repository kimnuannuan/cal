#!/usr/bin/env python3
"""对比：远端 main 最新 commit 与 Pages 最近一次构建所用 commit。"""
import json
import os
import urllib.error
import urllib.request

_here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_here, ".git_token")) as fh:
    _pat = fh.read().strip()

HDRS = {"Authorization": "Bearer " + _pat, "Accept": "application/vnd.github+json",
        "Content-Type": "application/json", "X-GitHub-Api-Version": "2022-11-28"}


def get(path):
    req = urllib.request.Request("https://api.github.com" + path, headers=HDRS)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.status, json.loads(r.read().decode() or "{}")


def post(path):
    req = urllib.request.Request("https://api.github.com" + path, data=b"{}",
                                method="POST", headers=HDRS)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.status, json.loads(r.read().decode() or "{}")


_, c = get("/repos/kimnuannuan/cal/commits/main")
head_sha = c["sha"]
print("远端 main HEAD:", head_sha[:10], "|", c["commit"]["message"].splitlines()[0])

_, b = get("/repos/kimnuannuan/cal/pages/builds/latest")
print("Pages 最近构建:", b.get("status"), "| commit:", (b.get("commit") or "?")[:10],
      "| ", b.get("created_at"))

if (b.get("commit") or "")[:10] != head_sha[:10]:
    print("→ 构建落后于 HEAD，强制重建")
    st, d = post("/repos/kimnuannuan/cal/pages/builds")
    print("   trigger:", st, d.get("status"))
else:
    print("→ 构建 commit 已是最新")
