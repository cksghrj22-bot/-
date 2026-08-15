#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""① 낙타형 자막바 — 매니페스트 구동 렌더러 (이 방 전용)

규격 정본: knowledge/규격_낙타형자막바_컨텐츠_정본.md
그리기 정본: scripts/cards/nakta_post.py (공유자원 — 수치는 그쪽이 정본, 여기서 바꾸지 않는다)

에이엠톤(③) 매니페스트와 **전혀 다른 형식**이다. 구분은 manifest_kinds.py 가 강제한다.
  python3 rooms/낙타방/nakta_from_manifest.py content/nakta/<매니페스트>.json
"""
import pathlib, subprocess, sys, tempfile
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "scripts" / "cards"))
import manifest_kinds
import nakta_post as N            # 그리기 정본 (공유)

ROLES = ("설정", "결론", "시안")


def frame(src, t, crop_y):
    """영상이면 t초 프레임, 사진이면 그대로 → 1080x1350 커버크롭."""
    src = ROOT / src if not pathlib.Path(src).is_absolute() else pathlib.Path(src)
    if src.suffix.lower() in {".mp4", ".mov", ".m4v"}:
        tmp = pathlib.Path(tempfile.mkdtemp()) / "f.jpg"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", str(src),
                        "-frames:v", "1", "-q:v", "2", str(tmp)], check=True)
        im = Image.open(tmp)
    else:
        im = Image.open(src)
    W, H = N.W, N.H
    w, h = im.size
    s = max(W / w, H / h)
    im = im.resize((round(w * s), round(h * s)), Image.LANCZOS)
    w, h = im.size
    y = int((h - H) * crop_y)
    return im.crop(((w - W) // 2, y, (w - W) // 2 + W, y + H))


def main():
    m = manifest_kinds.load(sys.argv[1], expect="nakta_subtitle_bar_v1")   # 스탬 구분기 필수
    d = m.get("defaults", {})
    outdir = ROOT / m["out"]; outdir.mkdir(parents=True, exist_ok=True)
    made = []
    for s in m["slides"]:
        lines = [(l["role"], l["text"]) for l in s["lines"]]
        bad = [r for r, _ in lines if r not in ROLES]
        if bad:
            raise SystemExit(f"⛔ 모르는 역할 {bad} — 낙타 역할은 {ROLES} 뿐이다 (규격 §3)")
        sizes = {**d.get("sizes", {"설정": 44, "결론": 34, "시안": 36}), **s.get("sizes", {})}
        base = frame(s["src"], s.get("start", 0.0), s.get("crop_y", d.get("crop_y", 0.46)))
        out = outdir / f"slide_{s['n']}.jpg"
        N.render(base, lines, str(out), size=sizes,
                 top=s["top"], left=s["left"])
        made.append(out)
        print(f"slide_{s['n']}.jpg  <- {s['src']} @{s.get('start',0)}s  「{lines[0][1]}」")
    print(f"\n{len(made)}장 → {outdir}")
    print("검수: python3 scripts/cards/nakta_gate.py", outdir)
    return made


if __name__ == "__main__":
    main()
