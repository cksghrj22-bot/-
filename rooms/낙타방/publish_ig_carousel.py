#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""인스타 캐러셀 발행 — 영상 자녀 (낙타방 `N` 전용)

**네트워크가 있는 곳에서 실행한다.** (코워크 클라우드 컨테이너 / 본진. 디바이스 VM은 망 없음)

  python3 publish_ig_carousel.py <슬라이드폴더> <캡션.txt> <instagram.json> [--go]

--go 없으면 점검만 한다(계정·파일·규격 확인). 실제 발행은 --go 를 붙였을 때만.
발행 성공 시 폴더에 .PUBLISHED 를 남겨 이중 발행을 막는다.
"""
import json, sys, time, pathlib, subprocess, urllib.request, urllib.parse

GRAPH = "https://graph.facebook.com/v19.0"
RUPLOAD = "https://rupload.facebook.com/ig-api-upload/v19.0"

def die(m): raise SystemExit("⛔ " + m)

def api(method, path, params):
    url = f"{GRAPH}/{path}"
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data if method == "POST" else None,
                                 method=method)
    if method == "GET":
        req = urllib.request.Request(url + "?" + urllib.parse.urlencode(params))
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)

def probe(p):
    out = subprocess.run(["ffprobe","-v","error","-select_streams","v",
        "-show_entries","stream=width,height,r_frame_rate","-show_entries","format=duration",
        "-of","default=nw=1:nk=1", str(p)], capture_output=True, text=True).stdout.split()
    return out

def main():
    if len(sys.argv) < 4: die(__doc__)
    folder = pathlib.Path(sys.argv[1]); cap = pathlib.Path(sys.argv[2]); cred = pathlib.Path(sys.argv[3])
    go = "--go" in sys.argv
    if (folder / ".PUBLISHED").exists(): die("이미 발행됨 (.PUBLISHED 존재)")

    slides = sorted(folder.glob("slide_*.mp4"), key=lambda p: int(p.stem.split("_")[1]))
    if not slides: die(f"슬라이드 없음: {folder}")
    if not (2 <= len(slides) <= 10): die(f"캐러셀은 2~10장. 지금 {len(slides)}장")
    caption = cap.read_text(encoding="utf-8").rstrip("\n")
    c = json.loads(cred.read_text(encoding="utf-8"))
    tok, uid = c["access_token"], c["ig_user_id"]

    me = api("GET", uid, {"fields": "username", "access_token": tok})
    print(f"계정: @{me.get('username')}  ({uid})")
    for p in slides:
        w, h, fr, dur = (probe(p) + ["?"]*4)[:4]
        print(f"  {p.name}  {w}x{h}  {fr}  {float(dur):.2f}s")
        if (w, h) != ("1080", "1350"): die(f"{p.name} 규격 위반 {w}x{h}")
    print(f"캡션 {len(caption)}자 / 첫 줄: {caption.splitlines()[0]}")
    if not go:
        print("\n[점검만 함] 실제 발행하려면 --go"); return 0

    kids = []
    for p in slides:
        r = api("POST", f"{uid}/media", {"media_type":"VIDEO","is_carousel_item":"true",
                                         "upload_type":"resumable","access_token":tok})
        cid = str(r["id"]); b = p.read_bytes()
        req = urllib.request.Request(f"{RUPLOAD}/{cid}", data=b, method="POST",
            headers={"Authorization": f"OAuth {tok}", "offset": "0",
                     "file_size": str(len(b)), "Content-Type": "application/octet-stream"})
        with urllib.request.urlopen(req, timeout=600) as rr:
            json.load(rr)
        kids.append(cid); print(f"  업로드 {p.name} -> {cid}")

    for cid in kids:
        for _ in range(60):
            s = api("GET", cid, {"fields":"status_code","access_token":tok}).get("status_code")
            if s == "FINISHED": break
            if s == "ERROR": die(f"자녀 처리 실패 {cid}")
            time.sleep(5)
        else: die(f"자녀 처리 시간초과 {cid}")
    print("자녀 처리 완료")

    par = api("POST", f"{uid}/media", {"media_type":"CAROUSEL",
              "children": ",".join(kids), "caption": caption, "access_token": tok})
    pub = api("POST", f"{uid}/media_publish", {"creation_id": str(par["id"]), "access_token": tok})
    mid = str(pub["id"])
    info = api("GET", mid, {"fields":"permalink,media_type,children{media_type}","access_token":tok})
    print("\n발행 완료")
    print("  media_id :", mid)
    print("  permalink:", info.get("permalink"))
    print("  type     :", info.get("media_type"),
          "/ 자녀", len(info.get("children",{}).get("data",[])), "장")
    (folder / ".PUBLISHED").write_text(json.dumps(
        {"media_id": mid, "permalink": info.get("permalink")}, ensure_ascii=False), encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
