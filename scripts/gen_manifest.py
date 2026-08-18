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
POOL2  = ROOT / "_clips_pool/문방구"          # 영상문방구 — 차노 승인분만
OKLIST = ROOT / "_out/shorts/_문방구_승인.json"
TONE   = ROOT / "_out/shorts/_broll_tone.json"
TONE_TARGET = 11.0   # 채널 기준 톤(R-B). 전 편을 이 근처로 모은다
TONE_GLOBAL = 9.0    # 기준에서 이만큼까지만 허용 (+2 ~ +20)
TONE_BAND = 5.0   # 한 편 안에서 허용하는 톤(R-B) 폭 — 8 로는 +12 와 +20 이 한 편에 섞였다
LEDGER = ROOT / "_out/shorts/_broll_ledger.json"
# ⛔ B롤로 쓰면 안 되는 파일 — **자막이 이미 구워진 완성본**이다.
#    2026-08-18 실사고: send_유행 을 소재로 쓴 2편이 S5(UI존 자막 침범)로 탈락했다.
# ⛔ B롤로 쓰면 안 되는 것 — **완성본**(자막이 구워짐)과 **다른 방 산출물**이다.
#    2026-08-18: 자동 수거가 낙타 영상·오늘의한문장·SEED 완성본까지 끌어왔다.
#    이름 규칙으로 거른다. 새 완성본이 들어와도 자동으로 빠진다.
EXCLUDE = {"send_유행.mp4"}
EXCLUDE_PAT = ("낙타", "오늘의한문장", "SEED", "연습_최종", "_최종본", "_final",
               "시니어_통합편", "_v5", "_v6", "_v7", "_v8", "_v9", "_v1", "시안")
SEG    = 3.6      # 한 장면 예약 길이 — 문방구 클립 상당수가 짧아 6초로는 못 쓴다(2026-08-18)
HEAD   = 0.3      # 클립 맨 앞 여백

def size(p):
    r = subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries",
                        "stream=width,height","-of","csv=p=0",str(p)], capture_output=True, text=True)
    try:
        w,h = r.stdout.strip().split(",")[:2]; return int(w), int(h)
    except Exception: return 0, 0

def is_finished(p):
    """완성 쇼츠인가 — **정확히 1080x1920** 이면 우리가 뽑은 결과물이다.
    원본 B롤은 4K(3840x2160) 나 세로4K(2160x3840) 나 폰 원본이라 이 치수가 안 나온다.
    2026-08-18: 이름 목록으로 거르니 S7_번역기 같은 게 계속 새어 나왔다 → 치수로 잠근다."""
    w, h = size(p)
    return (w, h) == (1080, 1920)

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
    """소스 목록. senior_new + 문방구(승인분).
    ⚠️ 문방구 소스는 톤이 어긋날 수 있어 **차노 승인 목록**(_문방구_승인.json)에 든 것만 쓴다."""
    cands = [f for f in sorted(POOL.iterdir())]
    if OKLIST.exists():
        ok = set(json.loads(OKLIST.read_text()))
        cands += [f for f in sorted(POOL2.iterdir()) if f.name in ok]
    out = []
    for f in cands:
        if f.suffix.lower() not in (".mov", ".mp4"): continue
        if f.name in EXCLUDE: continue
        if any(x in f.name for x in EXCLUDE_PAT): continue
        if is_finished(f): continue
        if only and f.name not in only: continue
        d = dur(f)
        if d >= 4.0: out.append((str(f.relative_to(ROOT/"_clips_pool")), d))
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

    import hashlib
    # 편마다 소스 순서를 다르게 — 안 그러면 전 편이 같은 그림으로 시작한다(차노 2026-08-18)
    si0 = int(hashlib.md5(Path(dst).stem.encode()).hexdigest()[:6], 16)
    cuts, scene, si = [], 0, si0
    used_here = []
    tone = json.loads(TONE.read_text()) if TONE.exists() else {}
    band = [None]   # 이 편의 기준 톤
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
                # 톤 밴드 — 차노 2026-08-18 "중간부터 끝까지 너무 빨간톤".
                # 편 안에서 톤이 튀면 눈이 불편하다. **첫 클립 톤 ±TONE_BAND 안에서만** 고른다.
                for stage in (0, 1, 2):
                    pref = (stage == 0)
                    for _ in range(len(srcs)):
                        name, total = srcs[si % len(srcs)]; si += 1
                        if pref and name in used_here: continue
                        t = tone.get(name)
                        # 채널 기준 톤 — 편끼리도 톤이 갈리면 몰아 볼 때 눈이 불편하다
                        # (차노 2026-08-18 "중간부터 끝까지 너무 빨간톤")
                        if stage < 2 and t is not None and abs(t - TONE_TARGET) > TONE_GLOBAL:
                            continue
                        lim = TONE_BAND if stage == 0 else (TONE_BAND * 1.6 if stage == 1 else 1e9)
                        if band[0] is not None and t is not None and abs(t - band[0]) > lim:
                            continue
                        got = take(led, name, total)
                        if got is not None:
                            clip, inn = name, got
                            if band[0] is None and t is not None: band[0] = t
                            break
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
