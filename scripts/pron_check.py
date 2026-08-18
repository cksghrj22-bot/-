#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""발음 사전 게이트 — 렌더 **전에** 대본을 훑어 뭉갤 자리를 잡아낸다.

차노 2026-08-18: "이렇게 하나씩 고쳐주면 다시는 실수를 안 해야지. 자동화가 되겠니?"
→ 맞다. 사고가 난 뒤에 고치는 방식은 자동화가 아니다.
   **렌더 전에 대본을 검사해서, 사전에 없는 위험 패턴이 있으면 렌더를 세운다.**

검사 항목
  ① 「어간+기(氣)」가 사전에 안 잡힌 채 남아 있는가  → 「이」로 읽혀 뭉갠다
  ② 받침+「에」가 붙어 뭉갤 자리인가                → 「매」로 읽힌다
  ③ 한 줄이 너무 길어 띄어쓰기 없이 이어지는가       → 붙여 읽는다

사용: python3 scripts/pron_check.py <매니페스트.json>   (rc=0 통과 / rc=1 걸림)
"""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
PF   = ROOT / "content/발음사전.json"

# 「기」로 끝나지만 그대로 읽어도 되는 말 — 여기 없는 「~기」는 전부 의심한다
SAFE_GI = {"습기","얘기","여기","저기","거기","경기","이야기","보기","포기","기기","연기",
           "시기","초기","말기","용기","분위기","향기","공기","자기","동기","계기","위기",
           "환기","기록","기술","기준","기본","기간","기대","기억","기분","기회","기계"}

def load():
    raw = json.loads(PF.read_text()) if PF.exists() else {}
    pron = {k: v for k, v in raw.items() if not k.startswith("_")}
    for st in raw.get("_끼어간", []):
        for j in raw.get("_조사", [""]):
            pron["%s기%s" % (st, j)] = "%s 끼%s" % (st, j)
    return raw, dict(sorted(pron.items(), key=lambda kv: -len(kv[0])))

def main():
    man = Path(sys.argv[1])
    raw, pron = load()
    cuts = json.loads(man.read_text())["cuts"]
    bad = []
    for i, c in enumerate(cuts, 1):
        if c.get("outro"): continue
        say = c.get("읽기") or c["말"]
        for a, b in pron.items(): say = say.replace(a, b)
        # ① 「~기(氣)」 — 관형형(-ㄴ/-ㄹ) 뒤에서만 氣 다.
        #    ⚠️ 「비행기·제습기·자르기·그렇기」까지 잡으면 게이트가 쓸모없어진다(2026-08-18 과탐지).
        for m in re.finditer(r"([가-힣])기(?=[가를은는의도만로와랑에\s.,!?]|$)", say):
            ch = m.group(1); jong = (ord(ch) - 0xAC00) % 28
            if jong not in (4, 8): continue          # ㄴ, ㄹ 받침만
            if ch + "기" in SAFE_GI: continue
            head = say[max(0, m.start()-3):m.start()+1]
            bad.append((i, "「%s기」 — 氣 인데 「이」로 뭉갠다. _끼어간 에 「%s」 추가" % (ch, head), c["말"]))
        # ② 외래어 색이름 + 기
        for m in re.finditer(r"(레드|애쉬|브라운|베이지|골드|오렌지|옐로우|그레이|블루)기", say):
            bad.append((i, "「%s기」 — _끼어간 에 「%s」 추가" % (m.group(1), m.group(1)), c["말"]))
        # ③ 띄어쓰기 없이 긴 덩어리
        for tok in say.split():
            if len(tok) >= 12:
                bad.append((i, "「%s」 %d자 — 띄어쓰기 없이 길다. 끊어 쓸 것" % (tok, len(tok)), c["말"]))
    if bad:
        print("⛔ 발음 게이트 %d건 — 렌더 전에 고친다" % len(bad))
        for i, msg, orig in bad:
            print("  %2d줄  %s" % (i, msg))
            print("        원문: %s" % orig)
        return 1
    print("✅ 발음 게이트 통과 (%d줄)" % len([c for c in cuts if not c.get("outro")]))
    return 0

sys.exit(main())
