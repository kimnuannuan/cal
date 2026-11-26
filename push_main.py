#!/usr/bin/env python3
"""推送 main 分支：凭证只从 .git_token 读，不进命令行；推送后把 remote 改回干净 URL。"""
import os
import subprocess

_here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_here, ".git_token")) as fh:
    _pat = fh.read().strip()

_owner = "kimnuannuan"
_repo = "cal"
_scheme = "https://"
_host = "github.com"
clean_url = _scheme + _host + "/" + _owner + "/" + _repo + ".git"
auth_url = _scheme + _owner + ":" + _pat + "@" + _host + "/" + _owner + "/" + _repo + ".git"


def git(*args):
    r = subprocess.run(["git"] + list(args), cwd=_here, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).replace(_pat, "***")


git("remote", "remove", "origin")
code, out = git("remote", "add", "origin", auth_url)
print("add remote:", code, out.strip())

code, out = git("push", "-u", "origin", "main", "--quiet")
print("push:", code, out.strip()[-400:])

git("remote", "set-url", "origin", clean_url)
print("remote 已改回:", git("remote", "-v")[1].strip())
