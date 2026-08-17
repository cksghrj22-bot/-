#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""에이엠톤 카드 자동 게이트 — 방3 `N` / 줄기 ③ 전용.

낙타(①)·쇼츠(②) 게이트와 섞지 않는다. 규격 정본:
  knowledge/규격_에이엠톤식_좌하단두줄_v1.md

  [A1] 1080 x 1350
  [A2] 글자가 좌하단에 있다 — 하단 35% · 좌측 55% 안에 잉크가 몰려 있어야 함
  [A3] 두 줄 — 잉크 행 프로파일에서 덩어리 2개
  [A4] 노랑 포인트: 카드당 노랑 픽셀 0.02~1.2% (0 = 포인트 없음, 과다 = 강조 죽음)
  [A5] 글자 대비 — 자막영역 글자 밝기 vs 배경 밝기 차 >= 60
  [A6] 그레이딩 걸렸나 — 블랙포인트 >= 15 (E 기준 23, 원본 4)
  [A7] 발행 전 컨택트시트 — 전 장 한 화면 + 판정 표시

  python3 scripts/cards/amton_gate.py _out/<폴더>
탈락(FAIL)이 하나라도 있으면 exit 1 = 산출물 아님.
"""
import sys, glob, pathlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
FONT = HERE / "fonts" / "NanumSquareRoundB.ttf"
W, H = 1080, 1350
YELLOW = (242, 194, 48)

def ink_mask(a):
    """글자 픽셀만. 흰 글자는 **거의 순백**(>=215 전채널), 포인트는 노랑.
    임계를 낮추면 밝은 피부(예: 196,168,150)를 글자로 오인한다 — 2026-08-15 자체검수에서 잡힌 버그."""
    white  = a.min(2) >= 215
    yellow = (a[..., 0] > 190) & (a[..., 1] > 140) & (a[..., 1] < 225) & (a[..., 2] < 110)
    return white | yellow

def yellow_ratio(a, ink):
    """노랑을 **글자 픽셀 대비** 비율로 잰다. 화면 전체 대비로 재면 한 줄 전체가 노래도
    0.3%밖에 안 나와서 못 잡는다 — 2026-08-15 역검증에서 잡힌 버그."""
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    m = (r > 190) & (g > 140) & (g < 225) & (b < 110)
    n = ink.sum()
    return (m & ink).sum() / n * 100 if n else 0.0

def row_blocks(mask, thr=3):
    rows = mask.sum(1)
    on = rows > thr
    blocks, run = [], 0
    for v in on:
        if v: run += 1
        elif run:
            if run >= 8: blocks.append(run)
            run = 0
    if run >= 8: blocks.append(run)
    return blocks

def check(p):
    im = Image.open(p).convert("RGB")
    a = np.asarray(im).astype(float)
    fails, warns, info = [], [], {}
    w, h = im.size
    if (w, h) != (W, H):
        fails.append(f"[A1] 해상도 {w}x{h} (1080x1350 이어야 함)")
        return fails, warns, info

    m = ink_mask(a)
    ys, xs = np.nonzero(m)
    if len(ys) < 200:
        fails.append("[A2] 글자를 못 찾음 (밝은 글자 픽셀 200 미만)")
        return fails, warns, info

    # A2 좌하단
    cy, cx = ys.mean() / H, xs.mean() / W
    info["글자중심"] = f"y {cy:.2f} / x {cx:.2f}"
    if cy < 0.65: fails.append(f"[A2] 글자가 하단에 없음 (중심 y={cy:.2f}, 0.65 이상이어야 함)")
    if cx > 0.55: fails.append(f"[A2] 글자가 좌측에 없음 (중심 x={cx:.2f}, 0.55 이하여야 함)")

    # A3 두 줄
    band = m[int(H * 0.60):, :]
    blocks = row_blocks(band)
    info["줄수"] = len(blocks)
    if len(blocks) != 2:
        (fails if len(blocks) > 2 else warns).append(f"[A3] 하단 글자 덩어리 {len(blocks)}개 (두 줄이어야 함)")

    # A4 노랑
    yr = yellow_ratio(a, m)
    info["노랑%"] = round(yr, 1)
    if yr < 3: fails.append(f"[A4] 노랑 포인트 없음 (글자 중 {yr:.1f}%)")
    elif yr > 25: fails.append(f"[A4] 노랑 과다 — 글자의 {yr:.0f}%. 한 단어만 (25% 이하). 한 줄 통째 노랑은 30%+ 로 잡힌다")

    # A5 대비
    sub = a[int(H * 0.60):, :]
    sm = m[int(H * 0.60):, :]
    lum = 0.299 * sub[..., 0] + 0.587 * sub[..., 1] + 0.114 * sub[..., 2]
    d = lum[sm].mean() - lum[~sm].mean()
    info["대비차"] = round(d, 1)
    if d < 60: fails.append(f"[A5] 글자-배경 밝기차 {d:.0f} (60 이상. 스크림을 더 내려라)")

    # A6 그레이딩
    L = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    bp = np.percentile(L, 5)
    info["블랙"] = round(bp, 1)
    if bp < 15: fails.append(f"[A6] 블랙포인트 {bp:.1f} — 그레이딩(E) 안 걸린 원본으로 보인다")
    return fails, warns, info

def sheet(items, out):
    TW = 430; TH = int(TW * H / W)
    F = ImageFont.truetype(str(FONT), 26); S = ImageFont.truetype(str(FONT), 20)
    n = len(items); cols = min(n, 4); rows = (n + cols - 1) // cols
    sh = Image.new("RGB", (cols * (TW + 16) + 16, rows * (TH + 96) + 16), (16, 16, 18))
    d = ImageDraw.Draw(sh)
    for i, (p, f, w_, info) in enumerate(items):
        r, c = divmod(i, cols)
        x = 16 + c * (TW + 16); y = 16 + r * (TH + 96)
        sh.paste(Image.open(p).resize((TW, TH), Image.LANCZOS), (x, y))
        ok = not f
        d.rectangle([x, y, x + TW, y + TH], outline=(60, 220, 130) if ok else (240, 70, 70), width=4)
        d.text((x, y + TH + 6), f"{pathlib.Path(p).name}  {'PASS' if ok else 'FAIL'}",
               font=F, fill=(60, 220, 130) if ok else (240, 90, 90))
        d.text((x, y + TH + 38), f"줄 {info.get('줄수','?')} · 노랑 {info.get('노랑%','?')}% · 대비 {info.get('대비차','?')}",
               font=S, fill=(170, 200, 230))
        d.text((x, y + TH + 62), (f[0][:34] if f else f"중심 {info.get('글자중심','')} · 블랙 {info.get('블랙','')}"),
               font=S, fill=(240, 120, 120) if f else (140, 150, 160))
    sh.save(out, quality=92)
    return sh.size

def main():
    tgt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    files = sorted(glob.glob(str(tgt / "*.jpg"))) if tgt.is_dir() else [str(tgt)]
    files = [f for f in files if not pathlib.Path(f).name.startswith("_")]
    if not files:
        print("검사할 카드 없음:", tgt); return 1
    items, allf = [], []
    for p in files:
        f, w_, info = check(p)
        items.append((p, f, w_, info)); allf += f
        tag = "PASS" if not f else "FAIL"
        print(f"{tag}  {pathlib.Path(p).name}  " +
              " · ".join(f"{k} {v}" for k, v in info.items()))
        for x in f: print("      ", x)
        for x in w_: print("   ⚠", x)
    out = (tgt if tgt.is_dir() else tgt.parent) / "_검수시트_에이엠톤.jpg"
    print("\n[A7] 검수 시트:", out, sheet(items, out))
    if allf:
        print(f"\n⛔ FAIL {len(allf)}건 — 산출물 아님. 고치고 다시 돌린다."); return 1
    print("\n[통과] A1~A6. 시트를 차노에게 띄운 다음 발행한다 (_ROOMS.md §3-1).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
