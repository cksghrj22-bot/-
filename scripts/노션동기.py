#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
노션동기.py — 옵시디언·트렁크의 글을 노션 「앳나운 지식 대장」으로 올린다 (2026-08-11 신설)
이찬호: "무조건 노션이랑 옵시디언 연동해라. 1년 지나서 자료를 찾아도 바로바로 나와야 된다."
  python3 ~/atnown-trunk/scripts/노션동기.py          매일 launchd
  python3 ~/atnown-trunk/scripts/노션동기.py --all     처음부터 다시
쌓기만 한다. 노션에서 지운 건 다시 안 올린다(상태파일 기준).
"""
import os, sys, json, re, hashlib, urllib.request, datetime

HOME = os.path.expanduser("~")
PIPE = os.path.join(HOME, "atnown-content-pipeline")
TRUNK = os.path.join(HOME, "atnown-trunk")
DB = "fb58939c66d640a390477d7d6ecbf88b"              # 앳나운 지식 대장
STATE = os.path.join(PIPE, "_노션동기.state.json")
TOKEN = json.load(open(os.path.join(PIPE, "secrets", "notion.json")))["token"]
H = {"Authorization": "Bearer " + TOKEN, "Notion-Version": "2022-06-28",
     "Content-Type": "application/json"}

# 어디를 훑나
SRC = [
    (os.path.join(PIPE, "_obsidian_in"), "옵시디언"),
    (os.path.join(TRUNK, "knowledge"), "규약정본"),
    (os.path.join(TRUNK, "prompts"), "규약정본"),
]

# 낱말 → 키워드 축
AXIS = {
    "진단":   ["납작", "부스스", "얇아", "가라앉", "손상", "곱슬", "원인", "증상"],
    "조합":   ["조합", "커트와 펌", "동시에", "같이 하", "믹스"],
    "볼륨":   ["볼륨", "정수리", "뿌리", "세우", "살아 보"],
    "커트":   ["커트", "자르", "층", "숱", "끝선", "기장"],
    "펌":     ["펌", "로드", "컬", "웨이브", "매직"],
    "염색":   ["염색", "새치", "탈색", "톤"],
    "상담":   ["상담", "손님", "고객", "물어", "되묻", "사진", "분위기"],
    "시간":   ["삼 주", "3주", "유지", "오래", "손질", "다음날"],
    "디자이너": ["디자이너", "미용사", "태도", "기준", "실력"],
    "경영":   ["살롱", "매출", "교육", "규약", "실측", "조회", "알고리즘", "채널"],
}

def axes(text):
    t = text[:6000]
    got = [k for k, ws in AXIS.items() if any(w in t for w in ws)]
    return got or ["경영"]

def load_state():
    try: return json.load(open(STATE, encoding="utf-8"))
    except Exception: return {}

def api(url, body):
    r = urllib.request.Request(url, data=json.dumps(body, ensure_ascii=False).encode(), headers=H)
    with urllib.request.urlopen(r, timeout=40) as x:
        return json.loads(x.read().decode())

def blocks(md, limit=90):
    """마크다운을 노션 블록으로. 표·코드는 통째로 코드블록에 넣어 원문을 지키지 않고 잃지 않는다."""
    out, buf = [], []
    for ln in md.split("\n"):
        if len(out) >= limit: break
        s = ln.rstrip()
        if s.startswith("#"):
            lvl = min(3, len(s) - len(s.lstrip("#")))
            txt = s.lstrip("# ").strip()
            if txt:
                out.append({"object": "block", "type": "heading_%d" % lvl,
                            "heading_%d" % lvl: {"rich_text": [{"type": "text", "text": {"content": txt[:1900]}}]}})
        elif s.startswith(("- ", "* ")):
            out.append({"object": "block", "type": "bulleted_list_item",
                        "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": s[2:][:1900]}}]}})
        elif s.startswith(">"):
            out.append({"object": "block", "type": "quote",
                        "quote": {"rich_text": [{"type": "text", "text": {"content": s.lstrip("> ")[:1900]}}]}})
        elif s.strip():
            out.append({"object": "block", "type": "paragraph",
                        "paragraph": {"rich_text": [{"type": "text", "text": {"content": s[:1900]}}]}})
    return out

def main():
    allmode = "--all" in sys.argv
    st = {} if allmode else load_state()
    new = 0
    for root, src in SRC:
        if not os.path.isdir(root): continue
        for fn in sorted(os.listdir(root)):
            if not fn.endswith(".md"): continue
            p = os.path.join(root, fn)
            try: md = open(p, encoding="utf-8").read()
            except Exception: continue
            h = hashlib.md5(md.encode()).hexdigest()[:12]
            key = os.path.relpath(p, HOME)
            if st.get(key) == h: continue           # 안 바뀌었다
            title = fn[:-3]
            m = re.search(r"^#\s+(.+)$", md, re.M)
            if m: title = m.group(1).strip()[:90]
            oneline = ""
            for ln in md.split("\n"):
                s = ln.strip()
                if s and not s.startswith(("#", ">", "|", "-", "*", "`")):
                    oneline = s[:180]; break
            props = {
                "제목": {"title": [{"text": {"content": title}}]},
                "키워드": {"multi_select": [{"name": a} for a in axes(md)]},
                "한 줄": {"rich_text": [{"text": {"content": oneline}}]},
                "출처": {"select": {"name": src}},
                "형 원문": {"checkbox": bool(re.search(r'이찬호[:：]\s*["「]', md))},   # 따옴표 안 원문이 있을 때만
                "날짜": {"date": {"start": datetime.date.fromtimestamp(os.path.getmtime(p)).isoformat()}},
                "원본 위치": {"rich_text": [{"text": {"content": key}}]},
            }
            try:
                api("https://api.notion.com/v1/pages",
                    {"parent": {"database_id": DB},
                     "properties": props, "children": blocks(md)})
                st[key] = h; new += 1
                print("올림 %s" % title[:44])
            except Exception as e:
                print("실패 %s — %s" % (fn[:34], str(e)[:90]))
    json.dump(st, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("새로 올린 것 %d개 · 대장 총 %d개" % (new, len(st)))

if __name__ == "__main__":
    main()
