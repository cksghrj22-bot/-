#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""드라이브 폴더/파일 목록 뽑기 — 유튜브쇼츠방 (코워크가 네트워크 못 붙어서 맥에서 실행)
사용법:
  python3 rooms/유튜브쇼츠방/drive_ls.py 사모님      # 이름에 '사모님' 들어간 폴더 찾기
  python3 rooms/유튜브쇼츠방/drive_ls.py --in <폴더ID>  # 그 폴더 안 파일 목록
"""
import json, sys, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
c = json.loads((ROOT / "secrets/gdrive.json").read_text())

def token():
    d = urllib.parse.urlencode({
        "client_id": c["client_id"], "client_secret": c["client_secret"],
        "refresh_token": c["refresh_token"], "grant_type": "refresh_token"}).encode()
    r = urllib.request.urlopen(urllib.request.Request(
        "https://oauth2.googleapis.com/token", data=d, method="POST"))
    return json.loads(r.read())["access_token"]

def q(query, tok):
    out, pt = [], None
    while True:
        p = {"q": query, "fields": "nextPageToken,files(id,name,mimeType,size,modifiedTime)",
             "pageSize": "1000", "orderBy": "name",
             "supportsAllDrives": "true", "includeItemsFromAllDrives": "true"}
        if pt: p["pageToken"] = pt
        u = "https://www.googleapis.com/drive/v3/files?" + urllib.parse.urlencode(p)
        r = json.loads(urllib.request.urlopen(urllib.request.Request(
            u, headers={"Authorization": "Bearer " + tok})).read())
        out += r.get("files", []); pt = r.get("nextPageToken")
        if not pt: break
    return out

def main():
    if len(sys.argv) < 2:
        print(__doc__); return 1
    tok = token()
    if sys.argv[1] == "--in":
        rows = q("'%s' in parents and trashed=false" % sys.argv[2], tok)
    elif sys.argv[1] == "--path":
        # 예: --path 앳나운영상/사모님   → 이름을 한 단계씩 타고 내려간다
        parent = None
        for i, name in enumerate(sys.argv[2].split("/")):
            cond = "mimeType='application/vnd.google-apps.folder' and name contains '%s' and trashed=false" % name.replace("'", "\\'")
            if parent: cond += " and '%s' in parents" % parent
            hits = q(cond, tok)
            if not hits:
                print("[없음] '%s' 를 못 찾음" % name); return 1
            if len(hits) > 1:
                print("[여러개] '%s' 후보 %d개 — 아래에서 골라 --in 으로 다시 실행" % (name, len(hits)))
                for h in hits: print("DIR \t%s\t%s" % (h["id"], h["name"]))
                return 1
            parent = hits[0]["id"]
            print("... %s = %s" % (hits[0]["name"], parent))
        rows = q("'%s' in parents and trashed=false" % parent, tok)
    else:
        rows = q("mimeType='application/vnd.google-apps.folder' and name contains '%s' and trashed=false"
                 % sys.argv[1].replace("'", "\\'"), tok)
    for f in rows:
        kind = "DIR " if f["mimeType"].endswith("folder") else "FILE"
        mb = (int(f.get("size", 0)) / 1048576) if f.get("size") else 0
        print("%s\t%s\t%8.1fMB\t%s" % (kind, f["id"], mb, f["name"]))
    print("\n(총 %d개)" % len(rows))
    return 0

sys.exit(main())
