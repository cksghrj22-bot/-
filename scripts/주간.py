#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
주간.py — 방별 주간 피드백 (2026-08-11 신설)
이찬호: "주간 피드백은 각 방마다 있어야지"
  python3 ~/atnown-trunk/scripts/주간.py B
자기 방 몫의 숫자와 지난주 기록을 뽑아 _reports/weekly_<날짜>_<방>.md 로 저장한다.
숫자는 자동, 세 줄(된 것·안 된 것·다음 주 하나)은 방이 직접 채운다.
"""
import os, sys, re, json, glob, datetime, statistics, subprocess

if len(sys.argv) < 2:
    raise SystemExit("쓰는 법: 주간.py <방코드>   예) 주간.py B")
ROOM = sys.argv[1].strip().upper()

P = os.path.expanduser("~/atnown-content-pipeline")
S = os.path.join(P, "secrets")
OUT = os.path.join(P, "_reports"); os.makedirs(OUT, exist_ok=True)
now = datetime.datetime.now()
wk1 = now - datetime.timedelta(days=7)
wk2 = now - datetime.timedelta(days=14)

NAME = {"B": "쇼츠 제작소", "기획": "차노기획실", "D": "블로그·잡업무",
        "E": "소재방", "교육": "교육디렉터실", "A": "확정본 보관", "C": "미등록"}
L = ["# 주간 피드백 — %s방 (%s)" % (ROOM, NAME.get(ROOM, "")),
     "", "> %s · 숫자는 자동, 아래 세 줄은 방이 직접 채운다" % now.strftime("%Y-%m-%d"), ""]

# ── 공통 · 이번 주 내가 남긴 기록
L += ["## 이번 주 내가 남긴 것", ""]
lg = os.path.join(P, "_ROOMS_LOG.md")
mine = []
if os.path.exists(lg):
    for ln in open(lg, encoding="utf-8"):
        if re.search(r"\*\*%s방\*\*" % re.escape(ROOM), ln): mine.append(ln.strip())
if mine:
    for m in mine[:15]: L.append(m)
else:
    L.append("남긴 게 없다. **남기지 않으면 다음 사람이 읽을 게 없다.**")
L.append("")

def get(u, h=None, t=30):
    import urllib.request
    return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=h or {}), timeout=t).read())

def ts(s):
    for f in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ"):
        try:
            t = datetime.datetime.strptime(s, f)
            return t.replace(tzinfo=None) - (t.utcoffset() or datetime.timedelta(0))
        except ValueError: continue
    return None

# ── 방별 숫자
if ROOM == "B":
    L += ["## 유튜브", ""]
    try:
        import urllib.parse, urllib.request
        c = json.load(open(os.path.join(S, "youtube.json")))
        b = urllib.parse.urlencode({"client_id": c["client_id"], "client_secret": c["client_secret"],
            "refresh_token": c["refresh_token"], "grant_type": "refresh_token"}).encode()
        tok = json.loads(urllib.request.urlopen(
            urllib.request.Request("https://oauth2.googleapis.com/token", data=b), timeout=25).read())["access_token"]
        H = {"Authorization": "Bearer " + tok}
        ch = get("https://www.googleapis.com/youtube/v3/channels?part=contentDetails,statistics&mine=true", H)
        up = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        st = ch["items"][0]["statistics"]
        pl = get("https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId=" + up, H)
        ids = [i["snippet"]["resourceId"]["videoId"] for i in pl.get("items", [])]
        vs = get("https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics,status&id=" + ",".join(ids), H)["items"]
        def bk(a, b_):
            return [v for v in vs if ts(v["snippet"]["publishedAt"]) and a <= ts(v["snippet"]["publishedAt"]) < b_]
        L += ["구독 %s명 · 총조회 %s회" % (f"{int(st.get('subscriberCount',0)):,}", f"{int(st.get('viewCount',0)):,}"), "",
              "| 구간 | 올린 편 | 조회 중앙값 |", "|---|---|---|"]
        for nm, w in (("이번 주", bk(wk1, now)), ("지난 주", bk(wk2, wk1))):
            if not w: L.append("| %s | 0 | — |" % nm); continue
            m = statistics.median([int(v["statistics"].get("viewCount", 0)) for v in w])
            L.append("| %s | %d | %.0f |" % (nm, len(w), m))
        L.append("")
        w1 = bk(wk1, now)
        if w1:
            L += ["이번 주 편별", "", "| 조회 | 제목 |", "|---|---|"]
            for v in sorted(w1, key=lambda x: -int(x["statistics"].get("viewCount", 0))):
                L.append("| %s | %s |" % (v["statistics"].get("viewCount", 0),
                                          v["snippet"]["title"].replace("\n", " ")[:44]))
            L.append("")
        priv = [v for v in vs if v["status"]["privacyStatus"] != "public"]
        L += ["비공개로 잠긴 편 %d개 — 예약이 안 걸렸는지 확인할 것" % len(priv), ""]
    except Exception as e:
        L += ["실측 실패 — %s" % str(e)[:140], ""]
    done = os.path.join(P, "_jobs", "_done")
    cut = wk1.timestamp()
    made = sorted([f for f in os.listdir(done) if f.endswith(".mp4") and os.path.getmtime(os.path.join(done, f)) > cut])
    L += ["## 이번 주 렌더한 것", "", "영상 %d편" % len(made), ""]
    for f in made[:20]: L.append("- %s" % f)
    L.append("")

elif ROOM in ("기획", "D"):
    L += ["## 인스타 · 스레드", ""]
    try:
        c = json.load(open(os.path.join(S, "meta.json")))
        tok, uid = c["long_token"], c["ig_user_id"]
        f = "id,caption,media_type,media_product_type,timestamp,like_count,comments_count"
        d = get("https://graph.facebook.com/v21.0/%s/media?fields=%s&limit=40&access_token=%s" % (uid, f, tok))
        ms = d.get("data", [])
        def bk(a, b_): return [m for m in ms if ts(m.get("timestamp","")) and a <= ts(m["timestamp"]) < b_]
        pr = get("https://graph.facebook.com/v21.0/%s?fields=username,followers_count&access_token=%s" % (uid, tok))
        L += ["@%s · 팔로워 %s명" % (pr.get("username"), f"{pr.get('followers_count',0):,}"), "",
              "| 구간 | 게시 | 좋아요 중앙값 | 댓글 중앙값 |", "|---|---|---|---|"]
        for nm, w in (("이번 주", bk(wk1, now)), ("지난 주", bk(wk2, wk1))):
            if not w: L.append("| %s | 0 | — | — |" % nm); continue
            L.append("| %s | %d | %.0f | %.0f |" % (nm, len(w),
                statistics.median([m.get("like_count") or 0 for m in w]),
                statistics.median([m.get("comments_count") or 0 for m in w])))
        L.append("")
        L += ["> 저장수·공유수는 게시물 인사이트에서 따로 봐야 한다. **저장이 도달을 만든다.**", ""]
    except Exception as e:
        L += ["실측 실패 — %s" % str(e)[:140], ""]

elif ROOM == "E":
    L += ["## 소재", ""]
    try:
        d = json.load(open(os.path.join(P, "_INTRAY_INDEX.json")))
        d = d if isinstance(d, list) else list(d.values())[0]
        n = len(d)
    except Exception: n = 0
    loc = len(os.listdir(os.path.join(P, "_intray"))) if os.path.isdir(os.path.join(P, "_intray")) else 0
    L += ["| 항목 | 개수 |", "|---|---|",
          "| 인트레이 파일 | %d |" % loc, "| 대장에 오른 것 | %d |" % n,
          "| **아직 안 본 것** | **%d** |" % max(0, loc - n), ""]
    cls = os.path.join(P, "_intray_분류")
    if os.path.isdir(cls):
        L += ["분류함", ""]
        for x in sorted(os.listdir(cls)):
            p2 = os.path.join(cls, x)
            if os.path.isdir(p2): L.append("- %s %d개" % (x, len(os.listdir(p2))))
        L.append("")

# ── 배선 상태 (모든 방 공통)
L += ["## 내 배선", ""]
stop = os.path.join(P, "_jobs", "_PAUSE_PULLS.stop")
L.append("- 멈춤 파일: **켜져 있다 — 자동 배선이 죽어 있다**" if os.path.exists(stop) else "- 멈춤 파일: 없음")
jb = glob.glob(os.path.join(P, "_jobs", "*.json"))
L.append("- 대기 중인 잡: %d개" % len(jb))
L.append("")

# ── 방이 채울 세 줄
L += ["---", "", "## 된 것", "", "(숫자로 적는다. 「좋아졌다」 말고 「1,363 → 2,840」)", "",
      "## 안 된 것", "", "(숨기지 않는다. 못 한 것도 적는다)", "",
      "## 다음 주 하나", "", "(하나만. 셋 적으면 하나도 안 된다)", ""]

p = os.path.join(OUT, "weekly_%s_%s.md" % (now.strftime("%Y-%m-%d"), ROOM))
open(p, "w", encoding="utf-8").write("\n".join(L))
print(p)
ob = os.path.join(P, "_obsidian_in")
if os.path.isdir(ob):
    import shutil; shutil.copy(p, ob); print("옵시디언 반영")
