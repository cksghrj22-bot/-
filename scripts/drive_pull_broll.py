#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""드라이브 '앳나운영상' **아래 모든 하위폴더**의 영상을 _clips_pool/senior_new/ 로 수거.
형이 계속 새 B롤을 올리므로 폴더를 가리지 않고 새 파일만 받아온다(이미 완전한 건 건너뜀).
⚠️ 샌드박스 밖(remote_cmd_watch)에서 실행. codex_dispatch 로는 DNS 가 죽는다.
"""
import json, sys, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT  = ROOT / "_clips_pool/senior_new"
CRED = ROOT / "secrets/gdrive.json"
EXT  = (".mov", ".mp4", ".m4v")

def token():
    c = json.loads(CRED.read_text())
    d = urllib.parse.urlencode({"client_id": c["client_id"], "client_secret": c["client_secret"],
                                "refresh_token": c["refresh_token"], "grant_type": "refresh_token"}).encode()
    return json.loads(urllib.request.urlopen(urllib.request.Request(
        "https://oauth2.googleapis.com/token", data=d, method="POST"), timeout=60).read())["access_token"]

def q(query, tok):
    out, pt = [], None
    while True:
        p = {"q": query, "fields": "nextPageToken,files(id,name,mimeType,size)", "pageSize": "1000",
             "supportsAllDrives": "true", "includeItemsFromAllDrives": "true"}
        if pt: p["pageToken"] = pt
        r = json.loads(urllib.request.urlopen(urllib.request.Request(
            "https://www.googleapis.com/drive/v3/files?" + urllib.parse.urlencode(p),
            headers={"Authorization": "Bearer " + tok}), timeout=120).read())
        out += r.get("files", []); pt = r.get("nextPageToken")
        if not pt: return out

def walk(fid, tok, depth=0):
    """폴더를 재귀로 훑어 (경로, 파일) 목록을 만든다"""
    files = []
    for f in q("'%s' in parents and trashed=false" % fid, tok):
        if f["mimeType"].endswith("folder"):
            if depth < 3: files += walk(f["id"], tok, depth + 1)
        elif f["name"].lower().endswith(EXT):
            files.append(f)
    return files

def download(f, tok):
    dest = OUT / f["name"]
    want = int(f.get("size", 0))
    if dest.exists() and want and dest.stat().st_size == want:
        return "skip"
    url = "https://www.googleapis.com/drive/v3/files/%s?alt=media&supportsAllDrives=true" % f["id"]
    tmp = dest.with_suffix(dest.suffix + ".part"); got = 0
    with urllib.request.urlopen(urllib.request.Request(
            url, headers={"Authorization": "Bearer " + tok}), timeout=600) as r, open(tmp, "wb") as fh:
        while True:
            b = r.read(1 << 20)
            if not b: break
            fh.write(b); got += len(b)
    tmp.rename(dest)
    return "ok" if (not want or got == want) else "size-mismatch(%d/%d)" % (got, want)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tok = token()
    roots = [f for f in q("mimeType='application/vnd.google-apps.folder' and trashed=false "
                          "and name contains '앳나운'", tok)]
    print("상위 폴더:", [f["name"] for f in roots], flush=True)
    seen, new, skipped = set(), 0, 0
    for root in roots:
        for f in walk(root["id"], tok):
            if f["id"] in seen: continue
            seen.add(f["id"])
            try:
                st = download(f, tok)
            except Exception as e:
                print("⛔ %s — %s" % (f["name"], e), flush=True); continue
            if st == "skip": skipped += 1
            else:
                new += 1
                print("✅ %-42s %10s bytes  %s" % (f["name"], f.get("size","?"), st), flush=True)
    print("\n새로 받음 %d개 · 이미 있음 %d개 · 총 %d개 후보" % (new, skipped, len(seen)), flush=True)
    tot = sum(p.stat().st_size for p in OUT.iterdir() if p.is_file())
    print("풀 현황: 파일 %d개 · %.1fGB" % (len(list(OUT.iterdir())), tot/1073741824), flush=True)
    return 0

sys.exit(main())
