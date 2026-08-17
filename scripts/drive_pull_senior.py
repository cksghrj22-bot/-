#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""드라이브 '앳나운영상/사모님' 폴더 통째 수거 → _clips_pool/senior_new/

⚠️ 이 스크립트는 remote_cmd_watch(샌드박스 밖)에서 돌려야 한다.
   codex_dispatch 로 돌리면 CODEX_SANDBOX_NETWORK_DISABLED=1 때문에 DNS 가 죽는다.
   실행: _terminal_inbox/CMD_*.json → {"cmd":"python_script","args":["drive_pull_senior.py"]}

MCP 커넥터와 달리 용량 제한이 없다(스트리밍 저장).
"""
import json, os, sys, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT  = ROOT / "_clips_pool/senior_new"
CRED = ROOT / "secrets/gdrive.json"
VIDEO_EXT = (".mov", ".mp4", ".m4v", ".avi")

def token():
    c = json.loads(CRED.read_text())
    d = urllib.parse.urlencode({"client_id": c["client_id"], "client_secret": c["client_secret"],
                                "refresh_token": c["refresh_token"], "grant_type": "refresh_token"}).encode()
    r = urllib.request.urlopen(urllib.request.Request(
        "https://oauth2.googleapis.com/token", data=d, method="POST"), timeout=60)
    return json.loads(r.read())["access_token"]

def q(query, tok):
    out, pt = [], None
    while True:
        p = {"q": query, "fields": "nextPageToken,files(id,name,mimeType,size)",
             "pageSize": "1000", "supportsAllDrives": "true", "includeItemsFromAllDrives": "true"}
        if pt: p["pageToken"] = pt
        u = "https://www.googleapis.com/drive/v3/files?" + urllib.parse.urlencode(p)
        r = json.loads(urllib.request.urlopen(urllib.request.Request(
            u, headers={"Authorization": "Bearer " + tok}), timeout=120).read())
        out += r.get("files", []); pt = r.get("nextPageToken")
        if not pt: return out

def find_folder(name, tok, parent=None):
    cond = ("mimeType='application/vnd.google-apps.folder' and trashed=false and name contains '%s'"
            % name.replace("'", "\\'"))
    if parent: cond += " and '%s' in parents" % parent
    return q(cond, tok)

def download(fid, dest, tok, expect=0):
    if dest.exists() and expect and dest.stat().st_size == expect:
        print("건너뜀(이미 완전함): %s" % dest.name, flush=True); return True
    url = "https://www.googleapis.com/drive/v3/files/%s?alt=media&supportsAllDrives=true" % fid
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + tok})
    tmp = dest.with_suffix(dest.suffix + ".part")
    got = 0
    with urllib.request.urlopen(req, timeout=300) as r, open(tmp, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk: break
            f.write(chunk); got += len(chunk)
    tmp.rename(dest)
    ok = (not expect) or got == expect
    print("%s %s  %d bytes%s" % ("✅" if ok else "⛔", dest.name, got,
          "" if ok else " (기대 %d — 불일치)" % expect), flush=True)
    return ok

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tok = token()
    print("토큰 발급 OK", flush=True)
    parents = find_folder("앳나운", tok)
    print("상위 폴더 후보:", [(f["name"], f["id"]) for f in parents], flush=True)
    targets = []
    for p in parents:
        for sub in find_folder("사모님", tok, p["id"]):
            targets.append((p["name"], sub))
    if not targets:
        print("⛔ '사모님' 폴더를 못 찾음"); return 1
    total_ok = total_fail = 0
    for pname, sub in targets:
        files = [f for f in q("'%s' in parents and trashed=false" % sub["id"], tok)
                 if f["name"].lower().endswith(VIDEO_EXT)]
        print("\n[%s / %s] 영상 %d개" % (pname, sub["name"], len(files)), flush=True)
        for f in sorted(files, key=lambda x: int(x.get("size", 0))):
            try:
                ok = download(f["id"], OUT / f["name"], tok, int(f.get("size", 0)))
                total_ok += ok; total_fail += (not ok)
            except Exception as e:
                print("⛔ %s — %s: %s" % (f["name"], type(e).__name__, e), flush=True); total_fail += 1
    print("\n=== 완료: 성공 %d · 실패 %d ===" % (total_ok, total_fail), flush=True)
    for p in sorted(OUT.iterdir()):
        if p.is_file(): print("  %10d  %s" % (p.stat().st_size, p.name))
    return 0 if total_fail == 0 else 1

sys.exit(main())
