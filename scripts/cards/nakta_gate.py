#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""낙타 자막바 카드 — 게이트 (규격 검사 + 눈검수 시트 + 자동 로그).

정본: knowledge/규격_낙타형자막바_컨텐츠_정본.md
      knowledge/체크리스트_낙타형자막바_렌더게이트_정본.md

쓰는 법:
    python3 scripts/cards/nakta_gate.py <폴더> [--원문 <파일>]
    → 통과 exit 0 / 탈락 exit 1

검사 축 (2026-08-18 구현 — 그 전엔 이미지 존재만 봤다):
    N1 해상도      1080×1350 전 장
    N2 장수        2~10 (인스타 캐러셀 상한)
    N3 전폭바 금지  박스 폭 ≥ 92% 캔버스 = 탈락  (「전체폭 바자막 금지」)
    N4 위치 변주    전 장 자막 위치가 같으면 탈락 (「6장 다 똑같음 = 신문」)
    N5 시안 분산    연속 배치 탈락 / 0장·4장↑ 경고 (「2~3장 분산」)
    N6 크기 위계    한 장 안 박스 높이가 전부 같으면 경고 (「다 같은 크기 금지」)
    N7 영상 길이    슬라이드 mp4 는 3~5초 (ffprobe 있을 때)
    N8 문안 원문    --원문 주면 공백 제거 대조 (「창작·윤문 금지」)

자동으로 못 잡는 것 = **피사체(얼굴) 가림.**
  핸드헬드 POV 자동 얼굴검출은 2026-07-31 에 불가로 박제됐다.
  그래서 이 게이트는 `_게이트_눈검수.jpg` 를 만든다 — 만든 쪽이 먼저 보고 판단한다.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent.parent

CANVAS = (1080, 1350)
MAX_SLIDES = 10
FULLWIDTH_RATIO = 0.92      # 이 이상이면 전폭바
MIN_RUN_W = 60              # 박스로 볼 최소 가로 길이(px)
MIN_BAND_H = 24             # 박스로 볼 최소 세로 높이(px)
ROW_FILL = 0.45             # 박스 행: 좌우 끝 사이가 이 비율 이상 박스색
BOX_FILL = 0.30             # 박스 전체: 글자 구멍 빼고 이 비율 이상
ROW_GAP  = 4                # 행 끊김 허용(글자 사이)
EDGE_STD_L = 7.0            # 좌측정렬이므로 왼쪽 끝은 거의 안 흔들린다
EDGE_STD_R = 22.0           # 오른쪽 끝(글자폭)은 조금 흔들린다
LONG_TEXT  = 22             # 이보다 길면 「부연」 — 최대 크기로 두면 안 된다
MAX_BOX_H  = 0.22           # 박스 높이 상한(캔버스 대비) — 머리카락 덩어리 차단
# 영상 슬라이드 길이 — 2026-08-18 차노 지시 2회로 개정.
#   ① 「아니야 2초 괜찮아」        → 하한 3.0 → 2.0
#   ② 「그냥 쭈욱 길게 / 5초제한 빼」 → **상한 폐기(None)**
# 남은 건 하한뿐이다. 원칙 = 08-15 쇼츠 길이규격 폐기와 같다:
# **길이를 맞추려고 자르거나 늘리거나 늦추지 않는다. 길이는 내용이 정한다.**
VIDEO_SEC = (2.0, None)


# ── 박스 검출 ────────────────────────────────────────────────
def _masks(a: np.ndarray) -> dict:
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    return {
        "설정": (r > 225) & (g > 225) & (b > 225),
        "결론": (r < 72) & (g < 72) & (b < 72),
        "시안": (g > 175) & (b > 185) & (r < 195) & (b > r + 30),
    }


def _bands(mask: np.ndarray, gray: np.ndarray) -> list[tuple[int, int, int, int]]:
    """행 투영으로 박스 bbox 를 뽑는다.

    박스 안에는 글자가 들어가 구멍이 뚫린다(흰 박스 위 검은 글자).
    그래서 균일도(std)로 거르면 박스를 통째로 놓친다 — 2026-08-18 실측으로 확인.
    대신 **채움 비율**로 거른다: 박스 행은 좌우 끝 사이가 대부분 박스색이다.
    """
    h, w = mask.shape
    rows: list = []
    for y in range(h):
        xs = np.flatnonzero(mask[y])
        if xs.size < MIN_RUN_W:
            rows.append(None)
            continue
        x0, x1 = int(np.percentile(xs, 2)), int(np.percentile(xs, 98))
        span = x1 - x0 + 1
        if span < MIN_RUN_W:
            rows.append(None)
            continue
        inside = int(((xs >= x0) & (xs <= x1)).sum())
        rows.append((x0, x1) if inside / span >= ROW_FILL else None)

    boxes, cur, y0, gap, seq = [], None, 0, 0, []
    for y in range(h + 1):
        row = rows[y] if y < h else None
        if row is not None:
            if cur is None:
                cur, y0, seq = [row[0], row[1]], y, [row]
            else:
                cur = [min(cur[0], row[0]), max(cur[1], row[1])]
                seq.append(row)
            gap = 0
        elif cur is not None:
            gap += 1
            if gap <= ROW_GAP and y < h:
                continue
            y_end = y - gap
            if y_end - y0 + 1 >= MIN_BAND_H:
                x0, x1 = cur
                sub = mask[y0:y_end + 1, x0:x1 + 1]
                ls = np.array([r[0] for r in seq], dtype=float)
                rs = np.array([r[1] for r in seq], dtype=float)
                # 진짜 낙타 박스 = 좌측정렬 직각 사각형.
                # 머리카락·그림자 덩어리는 행마다 좌우 끝이 크게 흔들린다 (2026-08-18 오검출 실측).
                straight = ls.std() <= EDGE_STD_L and rs.std() <= EDGE_STD_R
                not_tall = (y_end - y0 + 1) <= MAX_BOX_H * h
                # 낙타 박스는 x=7% 에서 시작하는 글자폭 박스다. 화면 가장자리에 붙지 않는다.
                # 옷·그릇 같은 어두운 영역은 프레임에 잘려 x0=0 / y1=끝 이 되며 가장자리에 붙는다.
                inset = x0 >= 0.02 * w and x1 <= w - 3 and y_end <= h - 4
                if sub.size and sub.mean() >= BOX_FILL and straight and not_tall and inset:
                    boxes.append((x0, y0, x1, y_end))
            cur, gap, seq = None, 0, []
    return boxes


def analyze(path: Path) -> dict:
    """렌더 메타(정확) 우선. 없으면 픽셀 추정(부정확 — 표시한다)."""
    im = Image.open(path).convert("RGB")
    meta_p = path.with_suffix(".meta.json")
    if meta_p.exists():
        try:
            m = json.loads(meta_p.read_text(encoding="utf-8"))
            roles: dict = {"설정": [], "결론": [], "시안": []}
            boxes, sizes, texts = [], [], []
            for b in m.get("boxes", []):
                x0, y0, x1, y1 = b["rect"]
                roles.setdefault(b.get("role", "설정"), []).append((x0, y0, x1, y1))
                boxes.append((x0, y0, x1, y1))
                sizes.append(b.get("font_size"))
                texts.append(b.get("text", ""))
            return {"size": im.size, "boxes": boxes, "roles": roles,
                    "sizes": sizes, "texts": texts, "src": "실측"}
        except Exception:
            pass
    a = np.asarray(im)
    gray = a.mean(axis=2)
    out = {"size": im.size, "boxes": [], "roles": {}, "sizes": [], "texts": [], "src": "추정"}
    for role, m in _masks(a).items():
        bs = _bands(m, gray)
        out["roles"][role] = bs
        out["boxes"] += bs
    return out


# ── 눈검수 시트 ──────────────────────────────────────────────
def make_sheet(folder: Path, slides: list[Path], info: dict) -> Path:
    thumb_w, pad = 320, 10
    ims = []
    for p in slides:
        im = Image.open(p).convert("RGB")
        d = ImageDraw.Draw(im)
        for (x0, y0, x1, y1) in info[p.name]["boxes"]:
            d.rectangle([x0, y0, x1, y1], outline=(255, 40, 40), width=6)
        sc = thumb_w / im.width
        im = im.resize((thumb_w, int(im.height * sc)))
        # 라벨은 이미지 **위에 덮지 않는다.** 덮으면 상단 자막이 잘린 것처럼 보여
        # 시트가 거짓 신호를 준다(2026-08-18 실측). 위에 띠를 따로 붙인다.
        lab = Image.new("RGB", (thumb_w, im.height + 26), (24, 24, 24))
        ld = ImageDraw.Draw(lab)
        ld.text((6, 6), p.stem, fill=(255, 220, 0))
        lab.paste(im, (0, 26))
        ims.append(lab)

    H = max(i.height for i in ims)
    sheet = Image.new("RGB", (len(ims) * (thumb_w + pad) + pad, H + 2 * pad), (24, 24, 24))
    for i, im in enumerate(ims):
        sheet.paste(im, (pad + i * (thumb_w + pad), pad))
    out = folder / "_게이트_눈검수.jpg"
    sheet.save(out, quality=88)
    return out


# ── 로그 ─────────────────────────────────────────────────────
def log_to_rooms(msg: str):
    ts = datetime.now().strftime("%m-%d %H:%M")
    line = f"- `{ts}` **낙타자막인스타** — {msg}\n"
    with open(ROOT / "_ROOMS_LOG.md", "a", encoding="utf-8") as f:
        f.write(line)
    print(f"[로그 자동기록] {line.strip()}")


def video_seconds(p: Path):
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(p)],
            capture_output=True, text=True, timeout=30)
        return float(r.stdout.strip()) if r.returncode == 0 else None
    except Exception:
        return None


def main() -> int:
    args = [a for a in sys.argv[1:]]
    src_file = None
    if "--원문" in args:
        i = args.index("--원문")
        src_file = Path(args[i + 1])
        del args[i:i + 2]
    if not args:
        print("사용법: nakta_gate.py <폴더> [--원문 <파일>]")
        return 2

    tgt = Path(args[0])
    if not tgt.is_dir():
        print(f"[탈락] {tgt} 폴더 아님")
        log_to_rooms(f"게이트 탈락. {tgt}. 폴더 아님.")
        return 1

    slides = sorted([p for p in list(tgt.glob("*.png")) + list(tgt.glob("*.jpg"))
                     if not p.name.startswith("_")],
                    key=lambda p: (len(p.stem), p.stem))
    if not slides:
        print(f"[탈락] {tgt} 에 슬라이드 이미지 없음")
        log_to_rooms(f"게이트 탈락. {tgt}. 이미지 없음.")
        return 1

    print(f"== 낙타 게이트: {tgt.name} ==")
    print(f"  슬라이드 {len(slides)}장\n")

    fails, warns, info = [], [], {}

    # N2 장수
    if len(slides) > MAX_SLIDES:
        fails.append(f"[N2] {len(slides)}장 — 인스타 캐러셀 상한 {MAX_SLIDES}장 초과")
    if len(slides) < 2:
        warns.append(f"[N2] {len(slides)}장 — 캐러셀이 아니다")

    centers, cyan_idx = [], []
    for n, p in enumerate(slides, 1):
        d = analyze(p)
        info[p.name] = d
        w, h = d["size"]
        tag = f"  {n}. {p.name:<22}"

        # N1 해상도
        if (w, h) != CANVAS:
            fails.append(f"[N1] {p.name} {w}×{h} — 정본 {CANVAS[0]}×{CANVAS[1]} 아님")

        boxes = d["boxes"]
        if not boxes:
            warns.append(f"[N3~N6] {p.name} 자막 박스 미검출 — 눈검수 필요")
            print(tag + f"{w}×{h}  박스 0")
            continue

        # N3 전폭바
        widest = max((x1 - x0 + 1) for x0, _, x1, _ in boxes)
        if widest / w >= FULLWIDTH_RATIO:
            fails.append(f"[N3] {p.name} 박스 폭 {widest/w:.0%} — 전체폭 바자막 금지")

        # 위치(무게중심)
        cx = sum((x0 + x1) / 2 for x0, _, x1, _ in boxes) / len(boxes) / w
        cy = sum((y0 + y1) / 2 for _, y0, _, y1 in boxes) / len(boxes) / h
        centers.append((cx, cy))

        # N6 크기 위계
        if d["src"] == "실측" and d["sizes"]:
            # 정본: 「핵심 단언은 크게, **긴 부연만** 작게」 — 짧은 두 줄이 같은 크기인 건 위반이 아니다.
            mx = max(d["sizes"])
            big_long = [t for t, z in zip(d["texts"], d["sizes"])
                        if z == mx and len(t) > LONG_TEXT]
            if big_long:
                fails.append(f"[N6] {p.name} 긴 부연({len(big_long[0])}자)이 최대 크기 {mx} — "
                             f"길면 줄여야 함: 「{big_long[0][:20]}…」")
            elif len(boxes) >= 3 and len(set(d["sizes"])) == 1:
                warns.append(f"[N6] {p.name} 3줄 이상이 전부 {mx} — 위계 약함")
        else:
            hs = {(y1 - y0 + 1) // 8 for _, y0, _, y1 in boxes}
            if len(boxes) >= 2 and len(hs) == 1:
                warns.append(f"[N6] {p.name} 박스 높이가 전부 같음 — 글자 크기 위계 없음(추정)")

        if d["roles"].get("시안"):
            cyan_idx.append(n)

        print(tag + f"{w}×{h}  박스 {len(boxes)}({d['src']})  폭 {widest/w:.0%}  "
                    f"위치 x{cx:.2f} y{cy:.2f}"
                    + (f"  크기 {'/'.join(str(z) for z in d['sizes'])}" if d["sizes"] else "")
                    + ("  [시안]" if d["roles"].get("시안") else ""))

    # N4 위치 변주
    if len(centers) >= 3:
        uniq = {(round(cx, 1), round(cy, 1)) for cx, cy in centers}
        if len(uniq) == 1:
            fails.append(f"[N4] {len(centers)}장 자막 위치가 전부 같음 — 신문. 위치 변주 필수")
        elif len(uniq) < max(2, len(centers) // 3):
            warns.append(f"[N4] 위치 변주 약함 — {len(centers)}장 중 자리 {len(uniq)}종")

    # N5 시안 분산
    if cyan_idx:
        runs = [b - a for a, b in zip(cyan_idx, cyan_idx[1:])]
        if any(r == 1 for r in runs):
            fails.append(f"[N5] 시안 연속 배치 {cyan_idx} — 중간중간 분산해야 함")
        if len(cyan_idx) > 3:
            warns.append(f"[N5] 시안 {len(cyan_idx)}장 — 정본 권장 2~3장")
    elif len(slides) >= 4:
        warns.append("[N5] 시안 0장 — 흰/검정만 반복하면 밋밋 (정본: 2~3장 시안)")

    # N7 영상 길이
    # `_` 로 시작하는 건 슬라이드가 아니라 부속물(이어보기·시트) — 이미지와 같은 규칙
    for v in sorted(v for v in tgt.glob("*.mp4") if not v.name.startswith("_")):
        sec = video_seconds(v)
        if sec is None:
            warns.append(f"[N7] {v.name} 길이 미측정 (ffprobe 없음)")
        elif sec < VIDEO_SEC[0]:
            fails.append(f"[N7] {v.name} {sec:.2f}초 — 하한 {VIDEO_SEC[0]:.0f}초 미만")
        elif VIDEO_SEC[1] is not None and sec > VIDEO_SEC[1]:
            fails.append(f"[N7] {v.name} {sec:.2f}초 — 상한 {VIDEO_SEC[1]:.0f}초 초과")

    # N8 문안 원문 대조
    if src_file:
        if not src_file.exists():
            warns.append(f"[N8] 원문 {src_file} 없음 — 대조 못 함")
        else:
            src = "".join(src_file.read_text(encoding="utf-8").split())
            card_texts = [t for p2 in slides for t in info[p2.name].get("texts", [])]
            if not card_texts:
                warns.append("[N8] 렌더 메타 없음 — 문안 대조 불가. 매핑표로 눈대조할 것")
            else:
                missing = [t for t in card_texts if "".join(t.split()) not in src]
                print(f"\n  원문 대조: {src_file} — 카드 문안 {len(card_texts)}줄")
                if missing:
                    fails.append(f"[N8] 원문에 없는 문안 {len(missing)}줄 — 창작·윤문 금지: "
                                 + " / ".join(m[:22] for m in missing[:3]))
                else:
                    print(f"    ✅ {len(card_texts)}줄 전부 원문과 일치 (공백 제거 대조)")

    # 눈검수 시트
    try:
        sheet = make_sheet(tgt, slides, info)
        print(f"\n  👁 눈검수 시트: {sheet}")
        print("     빨간 테두리 = 검출된 자막 박스. **피사체 가림은 이걸 보고 내가 판단한다.**")
    except Exception as e:
        warns.append(f"[시트] 눈검수 시트 생성 실패: {e}")

    if warns:
        print("\n[경고]")
        for x in warns:
            print("   " + x)

    if fails:
        print("\n[게이트 탈락]")
        for x in fails:
            print("   " + x)
        log_to_rooms(f"게이트 탈락. {tgt.name}. {len(slides)}장. 사유: {fails[0][:70]}")
        return 1

    print(f"\n[통과] 규격 {len(slides)}장 — N1~N7 이상 없음"
          + (f" (경고 {len(warns)})" if warns else ""))
    log_to_rooms(f"게이트 통과. {tgt.name}. {len(slides)}장"
                 + (f", 경고 {len(warns)}" if warns else "")
                 + ". 눈검수 시트 확인 후 **형 확인 대기.**")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
