"""shorts.bars_slides — 바자막 매니페스트 1개 → 캐러셀 '게시물' 슬라이드 PNG 여러 장.

배경(형 2026-08-01): "요건 mp4 말고 게시물로 만들 거라 사진으로 줘." 영상(make.py)과 같은 매니페스트를
써서, TTS·렌더 없이 각 세그를 1080x1920 정지 슬라이드로 뽑는다(인스타 캐러셀용). 바 색·기울기·폰트는
make.py의 _bar_png를 그대로 재사용 → 영상과 100% 동일한 룩. 사진 파일이 없으면 라벨 플레이스홀더로 대체.

쓰는 법:
    python3 -m shorts.bars_slides content/manifests/바자막_작은속삭임_요즘의생각.json --out /tmp/slides
"""
from __future__ import annotations

import json
from pathlib import Path

from . import make as M

W, H = 1080, 1920


def _photo_base(path: str):
    """사진 → 블러 커버 배경 + contain 전경(영상 _image_still과 동일 룩). 파일 없으면 None."""
    from PIL import Image, ImageFilter, ImageEnhance, ImageOps
    p = Path(str(path))
    if not p.is_file():
        return None
    im = Image.open(p).convert("RGB")
    bg = ImageOps.fit(im, (W, H), method=Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(42))
    bg = ImageEnhance.Brightness(bg).enhance(0.95)
    fg = im.copy()
    fg.thumbnail((W, H), Image.LANCZOS)
    slide = bg.copy()
    slide.paste(fg, ((W - fg.width) // 2, (H - fg.height) // 2))
    return slide.convert("RGBA")


def _placeholder(label: str):
    """사진 없을 때 라벨 플레이스홀더(무엇이 들어갈지)."""
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGBA", (W, H), (44, 44, 50, 255))
    d = ImageDraw.Draw(im)
    for y in range(H):
        c = 40 + int(46 * y / H)
        d.line([(0, y), (W, y)], fill=(c, c, c + 6, 255))
    f = ImageFont.truetype(M.NSQR, 30)
    d.text((44, H - 70), "· 사진 자리: " + label, font=f, fill=(190, 188, 182, 255))
    return im


def _apply_bars_still(slide, bars, k, handmade):
    """정지 슬라이드에 바들을 얹는다(make._apply_bars와 같은 규칙: 자동스택·handmade 기울기)."""
    from PIL import Image
    import tempfile, os
    run_y = None
    start_y = 748
    for bi, bar in enumerate(bars):
        y = bar.get("y")
        if y is None:
            y = start_y if run_y is None else run_y
        rot = bar.get("rot")
        if rot is None:
            rot = M._HANDMADE_TILT[(k * 3 + bi) % len(M._HANDMADE_TILT)] if handmade else 0.0
        tf = Path(tempfile.gettempdir()) / f"_slidebar_{k}_{bi}.png"
        bh = M._bar_png(bar["text"], bar.get("color", "white"), bar.get("x", 76), int(y), tf,
                        fontsize=int(bar.get("fs", 56)), rot=float(rot))
        barimg = Image.open(tf).convert("RGBA")
        slide.alpha_composite(barimg)
        os.unlink(tf)
        run_y = int(y) + bh + 20
    return slide


def make_slides(manifest_path: str, outdir: str) -> list:
    m = json.loads(Path(manifest_path).read_text())
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    handmade = bool(m.get("handmade"))
    paths = []
    idx = 0
    for k, seg in enumerate(m.get("segments", [])):
        bars = seg.get("bars")
        if not bars:
            continue                      # 아웃트로 tail 등 바 없는 세그는 건너뜀
        if seg.get("img"):
            base = _photo_base(seg["img"]) or _placeholder(Path(str(seg["img"])).stem)
        else:                             # black 등
            from PIL import Image
            base = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        base = _apply_bars_still(base, bars, k, handmade)
        idx += 1
        fp = out / f"slide_{idx:02d}.png"
        base.convert("RGB").save(fp, quality=95)
        paths.append(fp)
    # 아웃트로 슬라이드(있으면): 검은 배경 중앙 텍스트
    if m.get("outro"):
        from PIL import Image, ImageDraw, ImageFont
        im = Image.new("RGB", (W, H), (0, 0, 0))
        d = ImageDraw.Draw(im)
        f = ImageFont.truetype(M.NSQR, 46)
        tw = d.textlength(m["outro"], font=f)
        d.text(((W - tw) // 2, H // 2 - 30), m["outro"], font=f, fill=(238, 238, 238))
        idx += 1
        fp = out / f"slide_{idx:02d}.png"
        im.save(fp, quality=95)
        paths.append(fp)
    return paths


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="바자막 매니페스트 → 캐러셀 슬라이드 PNG")
    ap.add_argument("manifest")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    ps = make_slides(a.manifest, a.out)
    for p in ps:
        print(p)
    print(f"✅ 슬라이드 {len(ps)}장: {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
