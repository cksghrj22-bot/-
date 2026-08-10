#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""브리지 가드 — 렌더 '전에' 잡을 검사한다.
렌더가 끝난 뒤 게이트에서 떨어지면 시간·크레딧이 날아간다.
실수는 대부분 부품 사이(브리지)에서 난다: 클립풀↔비트, 대본↔비트, 카드↔자막, 검정↔길이.
여기서 다 막고 통과한 잡만 큐에 넣는다.
"""
import json, os, sys, glob, re

MAC = "/Users/chanho/atnown-content-pipeline"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def real(p): return p.replace(MAC, HERE) if p else p

# 말은 되는데 뜻이 없는 문장 — "AI스럽다"의 정체
AI_SMELL = ["이롭", "유의미", "본질적으로", "극대화", "최적화", "퀄리티", "솔루션",
            "다양한", "여러가지", "중요합니다만", "라고 할 수 있습니다", "인 것 같습니다",
            "하는 데 있어", "에 대한 이해", "를 통해", "함으로써"]

def check(path):
    j = json.load(open(path, encoding="utf-8"))
    tag = os.path.basename(path).replace("JOB-", "").replace(".json", "")
    beats = j.get("beats", [])
    errs, warns, fixes = [], [], []

    # ── 브리지 1: 클립풀 ↔ 클립비트 ──
    used = [b.get("clip") for b in beats if b.get("clip")]
    d = real(j.get("clips_dir", ""))
    pool = sorted(os.path.basename(x) for x in glob.glob(d + "/*.mov")) if os.path.isdir(d) else []
    # 붙어 있는 비트가 같은 클립 = 한 장면 이어보기(허용). 떨어져 있으면 재활용(금지).
    runs = []
    for b in beats:
        c = b.get("clip") or ""
        if not c:
            runs.append(""); continue
        if not runs or runs[-1] != c: runs.append(c)
    seq = [c for c in runs if c]
    dup = sorted({c for c in seq if seq.count(c) > 1})
    if dup:
        errs.append("클립 재활용 %s — 떨어진 자리에서 같은 컷을 또 쓴다 (장면 %d개 / 풀 %d개)"
                    % (dup, len(seq), len(pool)))
    missing = [c for c in set(used) if c not in pool]
    if missing:
        errs.append("풀에 없는 클립 %s" % sorted(missing))

    # ── 브리지 2: 대본 ↔ 비트 ──
    for i, b in enumerate(beats):
        s = (b.get("say") or "").strip()
        if not s:
            errs.append("비트%d 대사 없음" % i); continue
        if s[-1] not in ".?!":
            errs.append("비트%d 끝부호 없음: …%s" % (i, s[-12:]))
        if len(s) > 60:
            warns.append("비트%d 60자 초과(%d자) — 한 호흡에 안 들어간다" % (i, len(s)))
        # 한 슬라이드 한 생각 (낙타 폼)
        if len(re.findall(r"[.?!]", s)) >= 2:
            warns.append("비트%d 문장 2개 — 한 컷 한 생각 위반: %s" % (i, s[:34]))
        for w in AI_SMELL:
            if w in s:
                warns.append("비트%d AI말투 '%s': %s" % (i, w, s[:34]))
                break

    # ── 브리지 2.5: 빈 화면 방지 ──
    # live_caption 을 끄면 자막은 cap 에서만 나온다. cap 도 card 도 없으면 글자 없는 검은 화면이 된다.
    # 2026-08-09 실측: 숱 편 36~40초가 통째로 빈 검정이었고, 하필 제일 중요한 문장이 거기 있었다.
    if j.get("live_caption") is False:
        for i, b in enumerate(beats):
            if not (b.get("cap") or b.get("card")):
                errs.append("비트%d 화면에 글자가 없다 — cap 도 card 도 없음 (빈 검정이 된다)" % i)

    # ── 브리지 3: 검정 배치 ──
    blk = [i for i, b in enumerate(beats) if b.get("black")]
    adj = [i for i in blk if i + 1 in blk]
    if adj:
        errs.append("검정 연속 %s — 죽은 구간이 된다" % [(i, i + 1) for i in adj])
    if beats and len(blk) / len(beats) > 0.40:
        errs.append("검정 비중 %.0f%% (기준 40%%)" % (100 * len(blk) / len(beats)))

    # ── 브리지 4: 카드 ↔ 자막 같은 말 반복 ──
    for i, b in enumerate(beats):
        _c = b.get("card") or ""
        card = (" ".join(_c) if isinstance(_c, list) else _c).replace("|", " ").strip()
        say = (b.get("say") or "").strip()
        if card and say:
            c = re.sub(r"[^가-힣0-9]", "", card)
            s = re.sub(r"[^가-힣0-9]", "", say)
            if c and (c in s or s in c):
                warns.append("비트%d 카드와 자막이 같은 말 — 카드가 죽는다" % i)

    # ── 브리지 5: 길이 예측 (본문 ÷ 7.4 + 4.2) ──
    body = sum(len((b.get("say") or "")) for b in beats)
    est = body / 7.4 + 4.2
    if not (30 <= est <= 50):
        warns.append("예상 길이 %.0f초 (권장 33~48초) — 본문 %d자" % (est, body))

    # ── 브리지 6: 마무리 형식 ──
    if not j.get("outro"):
        errs.append("아웃트로 없음")
    if not j.get("axis"):
        warns.append("축(재미·감동·정보) 미지정")
    if j.get("thumb") is not False:
        errs.append('thumb 이 false 가 아니다 — 이 방 규칙 위반')

    return tag, errs, warns, len(used), len(pool)

def main():
    pats = sys.argv[1:] or [HERE + "/_jobs/_processing/JOB-*OK.json"]
    rows = []
    for pat in pats:
        for p in sorted(glob.glob(pat)):
            rows.append((p,) + check(p))
    ok = []
    print("=" * 68)
    for p, tag, errs, warns, nu, npool in rows:
        mark = "통과" if not errs else "막힘"
        print("\n[%s] %-8s  장면%d/풀%d" % (mark, tag, nu, npool))
        for e in errs:  print("   ✗ " + e)
        for w in warns: print("   · " + w)
        if not errs: ok.append((p, tag))
    print("\n" + "=" * 68)
    print("통과 %d / 전체 %d" % (len(ok), len(rows)))
    for _, t in ok: print("  →", t)
    return ok

if __name__ == "__main__":
    main()
