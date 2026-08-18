#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""드라이브 '단발매니펌' 폴더 → _clips_pool/단발매니펌/ 수거 (낙타자막인스타스레드방)

맥(본진)에서 실행한다. 코워크 컨테이너는 네트워크가 없어 _terminal_inbox 발주로 돌린다.
드라이브 전체를 이름으로 뒤지므로 폴더가 앳나운_영상 밑이 아니어도 찾는다.
"""
import json, sys, urllib.request, urllib.parse, pathlib, subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
C = json.loads((ROOT / "secrets/gdrive.json").read_text())
NAME = "단발매니펌"
OUT = ROOT / "_clips_pool/단발매니펌"


def token():
    d = urllib.parse.urlencode({
        "client_id": C["client_id"], "client_secret": C["client_secret"],
        "refresh_token": C["refresh_token"], "grant_type": "refresh_token"}).encode()
    r = urllib.request.urlopen(urllib.request.Request(
        "https://oauth2.googleapis.com/token", data=d, method="POST"))
    return json.loads(r.read())["access_token"]


def q(query, tok):
    out, pt = [], None
    while True:
        p = {"q": query, "fields": "nextPageToken,files(id,name,mimeType,size)",
             "pageSize": "1000", "orderBy": "name",
             "supportsAllDrives": "true", "includeItemsFromAllDrives": "true"}
        if pt:
            p["pageToken"] = pt
        u = "https://www.googleapis.com/drive/v3/files?" + urllib.parse.urlencode(p)
        r = json.loads(urllib.request.urlopen(urllib.request.Request(
            u, headers={"Authorization": "Bearer " + tok})).read())
        out += r.get("files", [])
        pt = r.get("nextPageToken")
        if not pt:
            break
    return out


def probe(p):
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height:format=duration",
             "-of", "default=nw=1:nk=1", str(p)],
            capture_output=True, text=True, timeout=60)
        return " ".join(r.stdout.split())
    except Exception as e:
        return f"(ffprobe 실패 {e})"


def main():
    tok = token()
    hits = [f for f in q(
        "mimeType='application/vnd.google-apps.folder' and trashed=false and name contains '%s'" % NAME, tok)]
    if not hits:
        print("[없음] '%s' 이름의 폴더를 드라이브에서 못 찾음." % NAME)
        return 1
    print("=== 후보 폴더 %d개 ===" % len(hits))
    for h in hits:
        print("  DIR\t%s\t%s" % (h["id"], h["name"]))
    fid, fname = hits[0]["id"], hits[0]["name"]
    print("\n=== 대상: %s (%s) ===" % (fname, fid))

    files = [f for f in q("'%s' in parents and trashed=false" % fid, tok)
             if not f["mimeType"].endswith("folder")]
    OUT.mkdir(parents=True, exist_ok=True)
    print("파일 %d개" % len(files))
    ok = 0
    for f in files:
        dest = OUT / f["name"]
        try:
            u = ("https://www.googleapis.com/drive/v3/files/%s?alt=media&supportsAllDrives=true"
                 % f["id"])
            req = urllib.request.Request(u, headers={"Authorization": "Bearer " + tok})
            with urllib.request.urlopen(req) as r, open(dest, "wb") as w:
                while True:
                    chunk = r.read(1 << 20)
                    if not chunk:
                        break
                    w.write(chunk)
            mb = dest.stat().st_size / 1048576
            print("  OK  %8.2fMB  %-40s  %s" % (mb, f["name"], probe(dest)))
            ok += 1
        except Exception as e:
            print("  FAIL  %s  — %s" % (f["name"], e))
    print("\n받음 %d/%d → %s" % (ok, len(files), OUT))
    print("※ ffprobe 출력 = width height duration (영상) / width height (사진)")
    return 0 if ok else 1


sys.exit(main())
