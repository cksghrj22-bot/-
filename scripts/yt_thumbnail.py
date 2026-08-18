#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""커스텀 썸네일 장착 — youtube.thumbnails.set

⚠️ 샌드박스 밖(remote_cmd_watch)에서 실행. **차노 승인 후에만.**
사용: {"cmd":"python_script","args":["yt_thumbnail.py"]}
      {"cmd":"python_script","args":["yt_thumbnail.py","07_커트의본질"]}
문구·videoId 정본: content/썸네일_문구.json / 이미지: _out/shorts/_thumbs/<키>.jpg
"""
import json, sys, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CRED = json.loads((ROOT / "secrets/youtube.json").read_text())
SPEC = ROOT / "content/썸네일_문구.json"
THUMB = ROOT / "_out/shorts/_thumbs"
LOG  = ROOT / "_out/shorts/_썸네일결과.json"
LIMIT = 2 * 1024 * 1024


def token():
    d = urllib.parse.urlencode({
        "client_id": CRED["client_id"], "client_secret": CRED["client_secret"],
        "refresh_token": CRED["refresh_token"], "grant_type": "refresh_token"}).encode()
    return json.loads(urllib.request.urlopen(urllib.request.Request(
        "https://oauth2.googleapis.com/token", data=d, method="POST"), timeout=60).read())["access_token"]


def put(video_id, img, tok):
    body = img.read_bytes()
    req = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/thumbnails/set?uploadType=media&videoId=" + video_id,
        data=body, method="POST",
        headers={"Authorization": "Bearer " + tok, "Content-Type": "image/jpeg",
                 "Content-Length": str(len(body))})
    return json.loads(urllib.request.urlopen(req, timeout=180).read())


def main():
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    want = sys.argv[1:]
    tok = token()
    out = []
    for key, v in spec.items():
        if want and key not in want:
            continue
        img = THUMB / ("%s.jpg" % key)
        if not img.exists():
            print("⛔ 이미지 없음:", img.name, flush=True); continue
        if img.stat().st_size > LIMIT:
            print("⛔ 2MB 초과: %s (%.1fMB)" % (img.name, img.stat().st_size / 1048576), flush=True); continue
        try:
            r = put(v["videoId"], img, tok)
            url = (r.get("items") or [{}])[0].get("default", {}).get("url", "")
            out.append({"key": key, "videoId": v["videoId"], "ok": True, "url": url})
            print("✅ %-18s %s  https://youtu.be/%s" % (key, img.name, v["videoId"]), flush=True)
        except Exception as e:
            msg = e.read().decode()[:400] if hasattr(e, "read") else str(e)
            out.append({"key": key, "videoId": v["videoId"], "ok": False, "error": msg})
            print("⛔ %-18s %s" % (key, msg), flush=True)
    LOG.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n===== 요약 =====  성공 %d / %d" % (sum(1 for x in out if x["ok"]), len(out)), flush=True)


if __name__ == "__main__":
    main()
