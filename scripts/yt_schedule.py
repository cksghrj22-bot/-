#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""쇼츠 예약 업로드 — private + publishAt (예약공개)

⚠️ 샌드박스 밖(remote_cmd_watch)에서 실행. 발행은 **차노 승인 후에만**.
사용: {"cmd":"python_script","args":["yt_schedule.py","<계획.json>"]}
계획 형식: [{"file":"...mp4","script":"...txt","publish_at":"2026-08-19T02:00:00Z"}, ...]
"""
import json, os, re, sys, urllib.request, urllib.parse
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
CRED = json.loads((ROOT/"secrets/youtube.json").read_text())
LOG  = ROOT/"_out/shorts/_예약결과.json"

def token():
    d = urllib.parse.urlencode({"client_id":CRED["client_id"],"client_secret":CRED["client_secret"],
        "refresh_token":CRED["refresh_token"],"grant_type":"refresh_token"}).encode()
    return json.loads(urllib.request.urlopen(urllib.request.Request(
        "https://oauth2.googleapis.com/token",data=d,method="POST"),timeout=60).read())["access_token"]

def meta(script_path):
    t = d = ""; tags = []
    for ln in Path(script_path).read_text(encoding="utf-8").splitlines():
        if ln.startswith("# 제목:"): t = ln.split(":",1)[1].strip()
        elif ln.startswith("# 설명:"): d = ln.split(":",1)[1].strip()
        elif ln.startswith("# 태그:"): tags = [x.strip() for x in ln.split(":",1)[1].split(",") if x.strip()]
    return t, d, tags

def upload(path, title, desc, tags, publish_at, tok):
    body = {"snippet": {"title": title[:100], "description": desc[:4900],
                        "tags": tags[:15], "categoryId": "26"},
            "status": {"privacyStatus": "private", "publishAt": publish_at,
                       "selfDeclaredMadeForKids": False}}
    size = os.path.getsize(path)
    req = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        data=json.dumps(body).encode(),
        headers={"Authorization":"Bearer "+tok, "Content-Type":"application/json; charset=UTF-8",
                 "X-Upload-Content-Length": str(size), "X-Upload-Content-Type": "video/mp4"})
    loc = urllib.request.urlopen(req, timeout=120).headers["Location"]
    with open(path,"rb") as f:
        put = urllib.request.Request(loc, data=f.read(), method="PUT",
                                     headers={"Content-Type":"video/mp4","Content-Length":str(size)})
        res = json.loads(urllib.request.urlopen(put, timeout=900).read())
    return res.get("id")

def main():
    plan = json.loads(Path(sys.argv[1]).read_text())
    tok = token(); out = []
    for it in plan:
        f = ROOT/it["file"]
        if not f.exists(): print("⛔ 없음:", it["file"], flush=True); continue
        t, d, tags = meta(ROOT/it["script"])
        try:
            vid = upload(str(f), t, d, tags, it["publish_at"], tok)
            out.append({**it, "videoId": vid, "title": t})
            print("✅ %-22s %s  %s  https://youtu.be/%s" % (f.name, t[:26], it["publish_at"], vid), flush=True)
        except Exception as e:
            body = e.read().decode()[:300] if hasattr(e, "read") else str(e)
            print("⛔ %s — %s" % (f.name, body), flush=True)
    LOG.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print("\n예약 %d편 완료 → %s" % (len(out), LOG.name), flush=True)
    return 0
sys.exit(main())
