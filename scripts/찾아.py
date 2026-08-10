#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""찾아 — 일 시작 전에 무조건 먼저 도는 것. "이거 전에 한 적 있나?"

왜(2026-08-10 형 지시):
"이미 다 기록은 있는데 찾는 트리거가 없는 거잖아."
실제로 그날, 트렁크에 `knowledge/B롤_촬영요청.md` 가 있는데도
같은 컷을 새로 찍어달라고 요청했다. 문서가 없어서가 아니라 안 찾아서였다.

기억은 방마다 사라진다. 기록은 트렁크에 남는다.
그 둘을 잇는 건 '시작 전에 찾는 습관'뿐인데, 습관은 잊힌다. 그래서 명령으로 만든다.

    python3 scripts/찾아.py 숱치기
    python3 scripts/찾아.py "B롤" 촬영
    python3 scripts/찾아.py --결정 썸네일      # 이미 정해진 것만
"""
import os, sys, re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOME = os.path.expanduser("~")
# 뒤질 곳 — 트렁크가 원줄기, 파이프라인은 작업장
ROOTS = [
    (os.path.join(HERE, "knowledge"),  "지식"),
    (os.path.join(HERE, "prompts"),    "규약"),
    (os.path.join(HERE, "pipeline"),   "폼"),
    (os.path.join(HERE, "docs"),       "문서"),
    (os.path.join(HERE, "briefings"),  "브리핑"),
    (HERE,                              "트렁크"),
    (os.path.join(HOME, "atnown-content-pipeline", "_codex_inbox"),   "지시서"),
    (os.path.join(HOME, "atnown-content-pipeline", "_cowork_sync"),   "결과보고"),
]
EXT = (".md", ".txt", ".json")
SKIP = ("/.git/", "/node_modules/", "/_tmp", "/__pycache__/")
# 이미 정해진 것 = 다시 논의하지 않는 것
DECIDED = ("확정", "정본", "금지", "규칙", "박제", "결정", "합의")

def files():
    seen=set()
    for root, label in ROOTS:
        if not os.path.isdir(root): continue
        depth = 1 if root == HERE else 4
        base = root.rstrip("/").count("/")
        for dp, dn, fn in os.walk(root):
            if any(s in dp+"/" for s in SKIP): continue
            if dp.count("/") - base >= depth: dn[:] = []
            for f in fn:
                if not f.endswith(EXT): continue
                p = os.path.join(dp, f)
                if p in seen: continue
                seen.add(p); yield p, label

def find(words, only_decided=False):
    hits=[]
    for p, label in files():
        try: txt = open(p, encoding="utf-8", errors="ignore").read()
        except Exception: continue
        name = os.path.basename(p)
        score = 0; lines=[]
        for w in words:
            if w in name: score += 12
            c = txt.count(w)
            if c: score += min(c, 10)
        if not score: continue
        for i, ln in enumerate(txt.split("\n")):
            if any(w in ln for w in words) and ln.strip():
                if only_decided and not any(d in ln for d in DECIDED): continue
                lines.append(ln.strip()[:130])
            if len(lines) >= 6: break
        if only_decided and not lines: continue
        mt = os.path.getmtime(p)
        hits.append((score, mt, p, label, lines))
    hits.sort(key=lambda x: (-x[0], -x[1]))
    return hits

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    only = "--결정" in sys.argv
    if not args:
        print("쓰는 법:  python3 scripts/찾아.py <단어> [단어...]   ·   --결정 을 붙이면 이미 정해진 것만")
        sys.exit(0)
    hits = find(args, only)
    print("\n" + "═"*62)
    print("찾아 · %s%s" % (" ".join(args), "  (이미 정해진 것만)" if only else ""))
    print("═"*62)
    if not hits:
        print("\n없다. 전에 한 적 없는 일이다. 새로 시작해도 된다.\n")
        sys.exit(0)
    import time
    for score, mt, p, label, lines in hits[:8]:
        rel = p.replace(HOME + "/", "")
        print("\n[%s] %s   (%s · 점수%d)" % (label, rel, time.strftime("%m-%d", time.localtime(mt)), score))
        for ln in lines:
            print("     " + ln)
    print("\n" + "─"*62)
    print("%d곳에서 나왔다. **새로 만들기 전에 위를 먼저 읽어라.**" % len(hits))
    print("이미 정해진 게 있으면 그대로 쓴다. 다시 정하지 않는다.\n")
