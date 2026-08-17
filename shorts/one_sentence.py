"""오늘의 한 문장 → 9:16 타이포 모션 숏폼 (앳나운 톤: 검정 배경·화이트/골드 미니멀).

리추얼 「하루 한 문장이 한 권의 책이 된다」 전용 빌더.
- 캔버스 1080x1920, 검정(#000). 문장만 남긴다. 장식 최소.
- 줄 단위 스태거 페이드인 → 마지막에 골드 헤어라인 + AT NOWN 워드마크.
- BGM: shorts/assets/bgm_piano_long.mp3 (은은하게, 끝에서 페이드아웃).
- B롤(~/Desktop/아무영상)이 있으면 --broll 로 뒤에 깔 수 있음. 없으면 타이포만.

사용:
    python3 shorts/one_sentence.py "문장" [--out 경로.mp4] [--broll 클립.mp4] [--no-bgm]
"""
import argparse, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
BG = (0, 0, 0)
WHITE = (243, 241, 236)
GOLD = (198, 162, 92)
FONT_BODY = os.path.expanduser("~/Library/Fonts/NanumSquareOTF_acL.otf")
FONT_MARK = os.path.expanduser("~/Library/Fonts/NanumSquareOTF_acR.otf")
BGM = os.path.expanduser("~/atnown-content-pipeline/shorts/assets/bgm_piano_long.mp3")
MARGIN = 130          # 좌우 여백 — 문장이 화면에 갇히지 않게 넉넉히
LINE_GAP = 1.62       # 행간 배수


def wrap(text, font, max_w):
    """어절 단위 줄바꿈. 감독이 직접 넣은 줄바꿈(\n)은 그대로 존중."""
    out = []
    for para in text.split("\n"):
        words, cur = para.split(), ""
        for w in words:
            trial = (cur + " " + w).strip()
            if font.getbbox(trial)[2] <= max_w or not cur:
                cur = trial
            else:
                out.append(cur); cur = w
        out.append(cur)
    return [l for l in out if l != ""]


def line_png(text, font, color, y, path):
    """한 줄을 전체 캔버스 투명 PNG로 — ffmpeg overlay 로 페이드인 시키려고."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bbox = font.getbbox(text)
    d.text(((W - (bbox[2] - bbox[0])) / 2 - bbox[0], y), text, font=font, fill=color + (255,))
    img.save(path)


def mark_png(path):
    """골드 헤어라인 + AT NOWN 워드마크 (하단, 아주 작게)."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.line([(W / 2 - 60, H - 300), (W / 2 + 60, H - 300)], fill=GOLD + (255,), width=2)
    f = ImageFont.truetype(FONT_MARK, 26)
    t = "AT NOWN"
    bb = f.getbbox(t)
    d.text(((W - (bb[2] - bb[0])) / 2 - bb[0], H - 258), t, font=f, fill=GOLD + (200,))
    img.save(path)


def build(sentence, out, broll=None, bgm=True, size=None):
    tmp = tempfile.mkdtemp(prefix="onesentence_")
    # 문장 길이에 따라 글자 크기 자동 — 짧은 문장은 크게, 긴 문장은 읽히게
    n = len(sentence.replace("\n", ""))
    size = size or (96 if n <= 22 else 80 if n <= 40 else 68 if n <= 70 else 58)
    font = ImageFont.truetype(FONT_BODY, size)
    lines = wrap(sentence, font, W - MARGIN * 2)

    lh = size * LINE_GAP
    block_h = lh * len(lines)
    y0 = (H - block_h) / 2 - size * 0.25      # 시각 중심은 기하 중심보다 살짝 위

    layers = []
    for i, ln in enumerate(lines):
        p = f"{tmp}/l{i}.png"
        line_png(ln, font, WHITE, y0 + i * lh, p)
        layers.append((p, 0.9 + i * 0.85))     # 스태거 등장
    mp = f"{tmp}/mark.png"
    mark_png(mp)
    mark_t = layers[-1][1] + 1.5
    layers.append((mp, mark_t))

    dur = round(mark_t + 3.4, 2)               # 마지막 여운

    cmd = ["ffmpeg", "-y"]
    if broll:
        cmd += ["-i", broll]
    else:
        cmd += ["-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:r=30"]
    for p, _ in layers:
        cmd += ["-loop", "1", "-i", p]
    if bgm and os.path.exists(BGM):
        cmd += ["-i", BGM]

    fc = []
    if broll:
        # B롤은 9:16 크롭 + 크게 어둡게 — 문장이 주인공
        fc.append(f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
                  f"crop={W}:{H},eq=brightness=-0.28:saturation=0.55,"
                  f"gblur=sigma=14,fps=30,trim=0:{dur},setpts=PTS-STARTPTS[base]")
    else:
        fc.append(f"[0:v]trim=0:{dur},setpts=PTS-STARTPTS[base]")

    cur = "base"
    for i, (_, t) in enumerate(layers):
        idx = i + 1
        fc.append(f"[{idx}:v]format=rgba,fade=t=in:st={t}:d=1.1:alpha=1[o{i}]")
        nxt = f"v{i}"
        fc.append(f"[{cur}][o{i}]overlay=0:0:shortest=0[{nxt}]")
        cur = nxt
    fc.append(f"[{cur}]fade=t=in:st=0:d=0.6,fade=t=out:st={dur-1.2}:d=1.2,format=yuv420p[vout]")

    maps = ["-map", "[vout]"]
    if bgm and os.path.exists(BGM):
        ai = len(layers) + 1
        fc.append(f"[{ai}:a]volume=0.16,afade=t=in:st=0:d=2,"
                  f"afade=t=out:st={dur-2.5}:d=2.5,atrim=0:{dur}[aout]")
        maps += ["-map", "[aout]", "-c:a", "aac", "-b:a", "192k"]

    cmd += ["-filter_complex", ";".join(fc)] + maps + [
        "-t", str(dur), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
        "-crf", "18", "-preset", "medium", out]
    subprocess.run(cmd, check=True, capture_output=True)
    return out, dur, lines


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("sentence")
    ap.add_argument("--out", default=os.path.expanduser("~/Desktop/한문장.mp4"))
    ap.add_argument("--broll", default=None)
    ap.add_argument("--no-bgm", action="store_true")
    a = ap.parse_args()
    p, d, ls = build(a.sentence, a.out, a.broll, not a.no_bgm)
    print(f"OK {p}  {d}s  lines={ls}")
