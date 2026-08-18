#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""대본 txt → 쇼츠 매니페스트 뼈대 (정본 v11)

대본 형식:  `00:03-00:07 대사...`  (앞의 # 줄은 제목/설명/태그)
소재는 `_clips_pool/senior_new` 에서 인물이 겹치지 않게 돌려 배정하고,
**두 줄을 한 장면(통컷)** 으로 묶는다. 검정 카드는 `--card N,M` 으로 지정.

사용: python3 scripts/gen_manifest.py <대본.txt> <출력매니페스트.json> [--card 8,9]
"""
import json, re, sys, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POOL = ROOT / "_clips_pool/senior_new"
# 인물 배정 — 같은 인물이 연달아 오지 않게 순서를 짠다
CLIPS = [("IMG_2471.MOV","F 숏컷",4.0), ("video-1961_singular_display.mov","H 커트",26.0),
         ("IMG_9610.MOV","사모님",1.0),  ("video-1949_singular_display.mov","E 커트",50.0),
         ("바비.mov","G 모피",0.3),      ("IMG_7224.MOV","B 롯드",1.0),
         ("IMG_9608.MOV","사모님",0.5),  ("쇼트으.mov","I 숏컷",0.3),
         ("IMG_0848.MOV","D 외출",0.8),  ("IMG_9604.MOV","사모님",4.0),
         ("video-1961_singular_display.mov","H 커트",100.0),
         ("video-1949_singular_display.mov","E 커트",128.0),
         ("IMG_2471.MOV","F 숏컷",58.0), ("IMG_9609.MOV","사모님",2.0)]

def lines_of(txt):
    out=[]
    for ln in Path(txt).read_text(encoding="utf-8").splitlines():
        ln=ln.strip()
        if not ln or ln.startswith("#"): continue
        m=re.match(r"^\d{1,2}:\d{2}(?:\.\d+)?\s*[-~]\s*\d{1,2}:\d{2}(?:\.\d+)?\s+(.*)$", ln)
        out.append(m.group(1).strip() if m else ln)
    return [x for x in out if x]

def main():
    src, dst = sys.argv[1], sys.argv[2]
    cards=set()
    if "--card" in sys.argv:
        cards={int(x) for x in sys.argv[sys.argv.index("--card")+1].split(",") if x.strip()}
    says = lines_of(src)
    cuts=[]; scene=0; ci=0
    for i, say in enumerate(says, 1):
        new_scene = (i % 2 == 1) or (i in cards) or ((i-1) in cards)
        if new_scene:
            scene += 1
            if i in cards:
                clip, who, inn = "", "카드", None
            else:
                clip, who, inn = CLIPS[ci % len(CLIPS)]; ci += 1
        cuts.append({"scene":scene,"start":0.0,"end":0.0,"말":say,
                     "clip":"" if i in cards else clip,
                     "화면":"검정 카드" if i in cards else clip,
                     "source":"카드" if i in cards else who,"일치":"✅",
                     **({"in":inn} if (i not in cards and inn is not None) else {})})
    cuts.append({"scene":scene+1,"start":0.0,"end":0.0,"말":"앳나운  ·  한남","clip":"",
                 "화면":"검정 카드","source":"카드","일치":"✅","outro":True})
    Path(dst).write_text(json.dumps({"cuts":cuts}, ensure_ascii=False, indent=1))
    print("대사 %d줄 · 장면 %d개 → %s"%(len(says), scene+1, Path(dst).name))
    for c in cuts: print("  [장면%2d] %-14s %s"%(c["scene"], c["clip"] or "검정카드", c["말"][:34]))
    return 0

sys.exit(main())
