#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""대본 txt → 쇼츠 매니페스트 뼈대 (정본 v11) + **B롤 전역 예약제**

차노 2026-08-18: "지금 b롤이 부족한지 계속 반복이거든?"
→ 원인은 분량 부족이 아니라 **편마다 같은 구간(in-point)을 다시 쓴 것**이었다.
   실측: 총 574초 / 8편 × 40초 = 320초 → 분량은 충분하다.
→ **장부**(`_out/shorts/_broll_ledger.json`)에 쓴 구간을 적고, 다음 편은 안 쓴 구간부터 가져간다.
   한 프레임도 겹치지 않는다.

사용: python3 scripts/gen_manifest.py <대본.txt> <출력매니페스트.json> [--card 8,9] [--only 파일명,파일명]
"""
import json, re, subprocess, sys
from pathlib import Path

ROOT   = Path(__file__).resolve().parent.parent
POOL   = ROOT / "_clips_pool/senior_new"
LEDGER = ROOT / "_out/shorts/_broll_ledger.json"
# ⛔ B롤로 쓰면 안 되는 파일 — **자막이 이미 구워진 완성본**이다.
#    2026-08-18 실사고: send_유행 을 소재로 쓴 2편이 S5(UI존 자막 침범)로 탈락했다.
EXCLUDE = {"send_유행.mp4"}
SEG    = 6.0      # 한 장면에 예약하는 길이(초) — 통컷 여유분
HEAD   = 0.3      # 클립 맨 앞 여백

def dur(p):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(p)],
                       capture_output=True, text=True)
    try: return float(r.stdout)
    except: return 0.0

def load_ledger():
    if LEDGER.exists():
        try: return json.loads(LEDGER.read_text())
        except Exception: pass
    return {}

def pool(only=None):
    """소스 목록 — 긴 것부터. 짧은 건 한 편에 한 번씩만 돈다."""
    out = []
    for f in sorted(POOL.iterdir()):
        if f.suffix.lower() not in (".mov", ".mp4"): continue
        if f.name in EXCLUDE: continue
        if only and f.name not in only: continue
        d = dur(f)
        if d >= 2.0: out.append((f.name, d))
    out.sort(key=lambda x: -x[1])
    return out

def take(led, name, total):
    """이 클립에서 아직 안 쓴 구간을 하나 예약한다. 없으면 None."""
    used = sorted(led.get(name, []))
    cur = HEAD
    for a, b in used:
        if a - cur >= SEG: break
        cur = max(cur, b + 0.2)
    if cur + SEG > total - 0.2:
        return None
    led.setdefault(name, []).append([round(cur,2), round(cur+SEG,2)])
    return round(cur, 2)

def lines_of(txt):
    out = []
    for ln in Path(txt).read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"): continue
        m = re.match(r"^\d{1,2}:\d{2}(?:\.\d+)?\s*[-~]\s*\d{1,2}:\d{2}(?:\.\d+)?\s+(.*)$", ln)
        out.append(m.group(1).strip() if m else ln)
    return [x for x in out if x]

def main():
    src, dst = sys.argv[1], sys.argv[2]
    cards = set()
    if "--card" in sys.argv:
        cards = {int(x) for x in sys.argv[sys.argv.index("--card")+1].split(",") if x.strip()}
    only = None
    if "--only" in sys.argv:
        only = [x.strip() for x in sys.argv[sys.argv.index("--only")+1].split(",") if x.strip()]

    says = lines_of(src)
    led  = load_ledger()
    srcs = pool(only)
    if not srcs:
        print("⛔ 소재 없음"); return 1

    cuts, scene, si = [], 0, 0
    used_here = []
    exhausted = []
    for i, say in enumerate(says, 1):
        new_scene = (i % 2 == 1) or (i in cards) or ((i-1) in cards)
        if new_scene:
            scene += 1
            if i in cards:
                clip, inn = "", None
            else:
                clip = inn = None
                # 한 편 안에서 같은 소스가 40% 를 넘지 않게 — **이 편에서 아직 안 쓴 것부터** 고른다
                for pref in (True, False):
                    for _ in range(len(srcs)):
                        name, total = srcs[si % len(srcs)]; si += 1
                        if pref and name in used_here: continue
                        got = take(led, name, total)
                        if got is not None: clip, inn = name, got; break
                        if name not in exhausted: exhausted.append(name)
                    if clip: break
                if clip: used_here.append(clip)
                if clip is None:
                    print("⛔ 남은 B롤 구간이 없다. 새 소재가 필요하다."); return 2
        cuts.append({"scene": scene, "start": 0.0, "end": 0.0, "말": say,
                     "clip": "" if i in cards else clip,
                     "화면": "검정 카드" if i in cards else clip,
                     "source": "카드" if i in cards else Path(clip).stem, "일치": "✅",
                     **({"in": inn} if (i not in cards and inn is not None) else {})})
    cuts.append({"scene": scene+1, "start": 0.0, "end": 0.0, "말": "앳나운  ·  한남", "clip": "",
                 "화면": "검정 카드", "source": "카드", "일치": "✅", "outro": True})
    Path(dst).write_text(json.dumps({"cuts": cuts}, ensure_ascii=False, indent=1))
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(led, ensure_ascii=False, indent=1))
    booked = sum(b-a for v in led.values() for a, b in v)
    print("대사 %d줄 · 장면 %d개 → %s" % (len(says), scene+1, Path(dst).name))
    for c in cuts:
        print("  [장면%2d] %-34s %s" % (c["scene"], (c["clip"] or "검정카드")[:32], c["말"][:30]))
    if exhausted: print("  (소진: %s)" % ", ".join(exhausted[:4]))
    print("  장부 누적 예약 %.0f초" % booked)
    return 0

sys.exit(main())
