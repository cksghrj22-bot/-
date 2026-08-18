#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""쇼츠 커스텀 썸네일 — 1080x1920 세로 (Shorts 선반 그대로 사용)

원칙
  · 프레임은 **최종본이 아니라 소스클립**에서 뽑는다 → 구운자막이 겹치지 않는다.
    소스는 하단에 구운자막이 있으므로 렌더와 같은 상단크롭을 건다.
  · 후보 프레임을 점수로 고른다(선명도·밝기·피부톤 비율) — 검은카드/흐린컷 자동 배제.
  · 훅 문구는 **어절별로 그린다**. 교보손글씨에 공백(U+0020) 글리프가 없다.
  · 문구는 상단(그리드에서 하단은 제목이 덮는다).

사용: python3 scripts/make_thumb.py            # 전편
      python3 scripts/make_thumb.py 07_커트의본질
"""
import json, subprocess, sys, tempfile, os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

ROOT  = Path(__file__).resolve().parent.parent
POOL  = ROOT / "_clips_pool"
FONT  = ROOT / "assets/fonts/KyoboHandwriting2019.ttf"
OUT   = ROOT / "_out/shorts/_thumbs"
GOLD  = (242, 194, 48)
WHITE = (255, 255, 255)
HEAD_Y = 640          # 인물 머리끝이 놓일 출력 y (문구 아래)
SUB_H  = 0.18         # 인물 덩어리가 차지할 세로 비율
MAX_SRC = 12          # 소스 몇 개까지 후보로 볼지
PER_SRC = 3           # 소스마다 몇 시점을 볼지         # 인물 덩어리가 차지할 세로 비율          # 인물 머리끝이 놓일 출력 y (문구 아래)
CROP  = "scale=-2:2100,crop=1080:1920:(iw-1080)/2:0"
SPEC  = ROOT / "content/썸네일_문구.json"
LEDGER = ROOT / "_out/shorts/_thumb_ledger.json"   # 편↔소스 장부 (중복 금지)


# ── 텍스트 (교보손글씨 공백 글리프 없음 → 어절별) ──────────────────
def wlen(d, text, font, gap):
    ws = [w for w in text.split(" ") if w]
    if not ws:
        return 0
    return sum(d.textlength(w, font=font) for w in ws) + gap * (len(ws) - 1)


def wdraw(d, xy, text, font, fill, sw, sfill, gap):
    x, y = xy
    for w in [w for w in text.split(" ") if w]:
        d.text((x, y), w, font=font, fill=fill, stroke_width=sw, stroke_fill=sfill)
        x += d.textlength(w, font=font) + gap


def fit(d, text, maxw, start=132, floor=68):
    """폭에 맞을 때까지 줄인 폰트를 돌려준다."""
    s = start
    while s > floor:
        f = ImageFont.truetype(str(FONT), s)
        if wlen(d, text, f, int(s * 0.32)) <= maxw:
            return f, s
        s -= 4
    return ImageFont.truetype(str(FONT), floor), floor


# ── 프레임 후보 뽑기 ───────────────────────────────────────────────
def grab(src, t, dst):
    r = subprocess.run(["ffmpeg", "-nostdin", "-y", "-ss", "%.2f" % t, "-i", str(src),
                        "-vf", CROP, "-frames:v", "1", "-q:v", "2", str(dst)],
                       capture_output=True)
    return r.returncode == 0 and Path(dst).exists() and Path(dst).stat().st_size > 5000


def subject(im):
    """피부톤 덩어리로 인물(얼굴·목·손) 자리를 잡는다.
    ⚠️ 살롱 바닥·목재·벽이 피부톤 범위에 들어온다 → 화면을 뒤덮는 덩어리는 인물이 아니다."""
    H, W = im.shape[:2]
    ycc = cv2.cvtColor(im, cv2.COLOR_BGR2YCrCb)
    cr, cb = ycc[:, :, 1].astype(int), ycc[:, :, 2].astype(int)
    m = (((cr > 133) & (cr < 180) & (cb > 77) & (cb < 127)) * 255).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((11, 11), np.uint8))
    n, lab, st, ce = cv2.connectedComponentsWithStats(m, 8)
    A = H * W
    ok = [j for j in range(1, n)
          if A * 0.003 < st[j, cv2.CC_STAT_AREA] < A * 0.20
          and st[j, cv2.CC_STAT_TOP] < H * 0.78]
    if not ok:
        return None
    j = max(ok, key=lambda k: st[k, cv2.CC_STAT_AREA])
    return tuple(int(v) for v in st[j, :5])          # x, y, w, h, area


def score(path):
    """썸네일감 점수 = 선명도 + 인물 구도. 흐린 컷·인물 없는 컷·검은카드를 떨군다."""
    im = cv2.imread(str(path))
    if im is None:
        return -1e9, {}
    H, W = im.shape[:2]
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    sharp = float(cv2.Laplacian(g, cv2.CV_64F).var())
    bright = float(g.mean())
    contrast = float(g.std())
    sub = subject(im)

    s = (min(sharp, 400) / 400) * 34
    if sharp < 28:
        s -= 130                                    # 초점 나간 컷
    if sub is None:
        s -= 110                                    # 인물이 안 잡히는 컷
        hf = cx = cy = ar = fill = 0.0
    else:
        x, y, w, h, area = sub
        hf = h / H                                  # 인물 덩어리 크기
        cx, cy = (x + w / 2) / W, (y + h / 2) / H
        ar = h / max(w, 1)                          # 얼굴은 세로가 조금 길다
        fill = area / max(w * h, 1)                 # 덩어리가 뭉쳐 있나(팔·어깨는 흩어진다)
        s += 50 * np.exp(-(((hf - 0.15) / 0.10) ** 2))
        s += 18 * np.exp(-(((cx - 0.50) / 0.26) ** 2))   # 가운데 있을수록
        s += 16 * np.exp(-(((cy - 0.42) / 0.26) ** 2))
        s += 18 * np.exp(-(((ar - 1.25) / 0.60) ** 2))
        s += 14 * min(fill / 0.55, 1.0)
        # ⚠️ 염색 호일·금속은 피부톤 범위에 들어온다. 얼굴이 아니다.
        roi = im[y:y + h, x:x + w]
        blown = float((cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) > 244).mean())
        sat = float(cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)[:, :, 1].mean())
        if blown > 0.05:
            s -= 70                                 # 번쩍이는 반사 = 호일
        if not (45 <= sat <= 165):
            s -= 45                                 # 무채색 금속 / 과채도
    s += 24 * (1 - min(abs(bright - 134) / 134, 1))
    s += 20 * (1 - min(abs(contrast - 58) / 58, 1))
    if bright < 42 or bright > 224:
        s -= 200
    return s, {"sh": round(sharp), "br": round(bright), "con": round(contrast),
               "인물": round(hf, 2), "xy": (round(cx, 2), round(cy, 2)),
               "종횡": round(ar, 2), "밀도": round(fill, 2)}


def _ledger():
    return json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else {"쓴것": {}, "거부": {}}


def _save(d):
    LEDGER.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def used_clips(key):
    """다른 편이 이미 쓴 소스 + 이 편에서 물린 소스는 안 쓴다.
    (B롤 장부제와 같은 원칙 — 채널에 같은 그림 두 장이 뜨면 안 된다.)"""
    d = _ledger()
    return {v for k, v in d["쓴것"].items() if k != key} | set(d["거부"].get(key, []))


def remember(key, clip):
    d = _ledger(); d["쓴것"][key] = clip; _save(d)


def reject(key):
    """지금 쓰고 있는 소스를 물린다 — 다음 뽑기에서 제외된다."""
    d = _ledger()
    cur = d["쓴것"].get(key)
    if cur:
        d["거부"].setdefault(key, [])
        if cur not in d["거부"][key]:
            d["거부"][key].append(cur)
        d["쓴것"].pop(key, None)
        _save(d)
        print("  ↺ 물림:", cur, flush=True)


def pick(cuts, tmp, key):
    """소스별 후보 프레임을 병렬로 뽑아 점수로 고른다.
    장면이 41개여도 소스는 몇 개뿐이다 → **소스 기준으로 접는다**(같은 그림 재채점 방지)."""
    bysrc = {}
    for c in cuts:
        if c.get("outro") or c.get("black"):
            continue
        clip = c.get("clip") or c.get("화면")
        if not clip or not (POOL / clip).exists():
            continue
        t = c.get("in", 0.3) + max(0.4, (c["end"] - c["start"]) / 2)
        bysrc.setdefault(clip, []).append(t)

    jobs = []
    for i, (clip, ts) in enumerate(list(bysrc.items())[:MAX_SRC]):
        ts = sorted(ts)
        for k, t in enumerate(ts[:: max(1, len(ts) // PER_SRC)][:PER_SRC]):
            jobs.append((clip, POOL / clip, t, tmp / ("%s_%02d_%02d.jpg" % (key, i, k))))

    def run(j):
        clip, src, t, dst = j
        return (clip, t, dst) if grab(src, t, dst) else None

    with ThreadPoolExecutor(max_workers=6) as ex:
        got = [r for r in ex.map(run, jobs) if r]

    ban = used_clips(key)
    ranked = []
    for clip, t, dst in got:
        s, info = score(dst)
        print("    %-30s t=%5.1f %7.1f %s%s" % (clip, t, s, info, "  ⟨다른편사용⟩" if clip in ban else ""), flush=True)
        ranked.append((s, clip, dst))
    ranked.sort(key=lambda r: -r[0])
    free = [r for r in ranked if r[1] not in ban]
    if not free:
        print("    ⚠️ 안 겹치는 소스가 없다 — 중복 허용", flush=True)
        free = ranked
    if not free:
        return None, None, None
    s, clip, dst = free[0]
    return dst, s, clip


# ── 인물 중심 줌 ───────────────────────────────────────────────────
def subject_crop(path):
    """인물 덩어리가 화면의 SUB_H 만큼 차지하도록 당기고,
    머리끝이 문구존 아래(HEAD_Y)로 오도록 세로를 앵커한다."""
    im = cv2.imread(str(path))
    H, W = im.shape[:2]
    src = Image.open(path).convert("RGB")
    sub = subject(im)
    if sub is None:
        return src.resize((1080, 1920), Image.LANCZOS)
    x, y, w, h, _ = sub
    z = max(1.0, min(1.40, (SUB_H * H) / max(h, 1)))   # 과한 줌 = 어깨·머리덩어리 클로즈업
    ch, cw = H / z, W / z
    x0 = int(max(0, min(W - cw, (x + w / 2) - cw / 2)))
    y0 = int(max(0, min(H - ch, y - HEAD_Y * ch / 1920)))
    return src.crop((x0, y0, x0 + int(cw), y0 + int(ch))).resize((1080, 1920), Image.LANCZOS)


# ── 합성 ───────────────────────────────────────────────────────────
def compose(frame, lines, dst):
    im = subject_crop(frame)

    # 상단 어둡게(문구 가독) — 아래로 갈수록 투명
    grad = Image.new("L", (1, 1920), 0)
    gp = grad.load()
    for y in range(1920):
        if y < 780:
            gp[0, y] = int(178 * (1 - (y / 780) ** 1.6))
        elif y > 1720:
            gp[0, y] = int(105 * ((y - 1720) / 200))
        else:
            gp[0, y] = 0
    mask = grad.resize((1080, 1920))
    im = Image.composite(Image.new("RGB", (1080, 1920), (0, 0, 0)), im, mask)

    d = ImageDraw.Draw(im)
    y = 172
    for i, ln in enumerate(lines):
        f, s = fit(d, ln, 928, start=136 if len(lines) > 1 else 150)
        gap = int(s * 0.32)
        w = wlen(d, ln, f, gap)
        x = (1080 - w) / 2
        wdraw(d, (x, y), ln, f, GOLD if i == len(lines) - 1 and len(lines) > 1 else WHITE,
              9, (0, 0, 0), gap)
        y += int(s * 1.22)

    # 브랜드 (작게, 문구 아래)
    bf = ImageFont.truetype(str(FONT), 46)
    bt = "앳나운 · 한남"
    bg = int(46 * 0.32)
    bw = wlen(d, bt, bf, bg)
    d.line([( (1080 - 300) / 2, y + 26), ((1080 + 300) / 2, y + 26)], fill=GOLD, width=3)
    wdraw(d, ((1080 - bw) / 2, y + 48), bt, bf, (245, 240, 232), 5, (0, 0, 0), bg)

    q = 92
    while q >= 62:
        im.save(dst, "JPEG", quality=q, optimize=True, progressive=True)
        if dst.stat().st_size <= 1_900_000:
            break
        q -= 6
    return dst


def main():
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    argv = sys.argv[1:]
    reroll = "--reroll" in argv
    want = [a for a in argv if not a.startswith("--")]
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="thumb_"))
    made = []
    for key, v in spec.items():
        if want and key not in want:
            continue
        print("■", key, flush=True)
        if reroll:
            reject(key)
        cuts = json.loads((ROOT / v["manifest"]).read_text(encoding="utf-8"))["cuts"]
        frame, s, clip = pick(cuts, tmp, key)
        if frame is None:
            print("  ⛔ 쓸 프레임 없음", flush=True)
            continue
        dst = OUT / ("%s.jpg" % key)
        compose(frame, v["훅"], dst)
        remember(key, clip)
        print("  ✅ %s  (%.0fKB, 점수 %.1f)  소스 %s" % (dst.name, dst.stat().st_size / 1024, s, clip), flush=True)
        made.append(key)

    # 확인용 9칸 시트
    if made:
        sheet = Image.new("RGB", (3 * 380, ((len(made) + 2) // 3) * 676 + 8), (18, 18, 18))
        for i, k in enumerate(made):
            t = Image.open(OUT / ("%s.jpg" % k)).resize((372, 662), Image.LANCZOS)
            sheet.paste(t, ((i % 3) * 380 + 4, (i // 3) * 676 + 4))
        sp = OUT / "_시트.jpg"
        sheet.save(sp, "JPEG", quality=88)
        print("🧾 시트:", sp, flush=True)


if __name__ == "__main__":
    main()
