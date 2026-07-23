"""롱폼 조립기 — 4K 원본 프록시(720p) + 일레븐랩스 Scribe 전사로 유튜브 롱폼을 편집한다.

이찬호 2026-07-21: 「앳나운 두피케어 System」 두피 스케일링 홍보 롱폼(8~13분).
- 원본 총 52분(뒷얘기·NG 섞임) → EDL로 알짜 구간만 골라 세그먼트로 조립.
- 각 세그먼트: 프록시 클립 트림 + Scribe 단어 타임스탬프로 한글 자막 구움.
- 오프닝/세그먼트 타이틀카드(앳나운 노란 제목) + BGM 언더.

EDL item = {"clip": "8957", "start": 15, "end": 150, "seg": "① 두피 진단",
            "title": "두피는 pH가 무너지면 방어력을 잃습니다"}
"""
from __future__ import annotations
import json, subprocess, re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720
FONT_HAND = "/root/.fonts/KyoboHandwriting2019.ttf"
FONT_B = "/usr/share/fonts/truetype/nanum/NanumSquareB.ttf"
FONT_R = "/usr/share/fonts/truetype/nanum/NanumSquareR.ttf"
YELLOW = (245, 215, 66)


def _wrap(draw, text, font, maxw):
    lines, cur = [], ""
    for ch in text:
        if draw.textlength(cur + ch, font=font) <= maxw or not cur:
            cur += ch
        else:
            lines.append(cur); cur = ch
    if cur:
        lines.append(cur)
    return lines


def title_card(main: str, sub: str, dur: float, out: Path, opening=False):
    """다크 배경 + 노랑 제목 타이틀카드(정지영상 → dur초 클립, 무음)."""
    img = Image.new("RGB", (W, H), (16, 16, 18))
    d = ImageDraw.Draw(img)
    if opening:
        # 교보 손글씨는 공백을 □로 깨뜨림 → 실제 렌더로 검증해 안전 폰트 선택
        from shorts import textsafe
        hand = textsafe.pick_font(main, [FONT_HAND, FONT_B])
        f = ImageFont.truetype(hand, 92)
        lines = _wrap(d, main, f, W - 160)
        y = H // 2 - len(lines) * 60 - 30
        for ln in lines:
            w = d.textlength(ln, font=f); d.text(((W - w) / 2, y), ln, font=f, fill=YELLOW); y += 108
        if sub:
            fs = ImageFont.truetype(FONT_R, 40); w = d.textlength(sub, font=fs)
            d.text(((W - w) / 2, y + 10), sub, font=fs, fill=(210, 210, 210))
    else:
        fk = ImageFont.truetype(FONT_B, 40)
        d.text((90, 250), sub, font=fk, fill=YELLOW)          # 세그먼트 번호/라벨
        d.line([90, 310, 230, 310], fill=YELLOW, width=5)
        f = ImageFont.truetype(FONT_B, 58)
        lines = _wrap(d, main, f, W - 180)
        y = 340
        for ln in lines:
            d.text((90, y), ln, font=f, fill=(245, 245, 245)); y += 78
    png = out.with_suffix(".png"); img.save(png)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-t", f"{dur}",
                    "-i", str(png), "-f", "lavfi", "-t", f"{dur}", "-i", "anullsrc=r=44100:cl=stereo",
                    "-vf", f"scale={W}:{H},fps=30", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-shortest", str(out)], check=True)


def _ass_escape(s):
    return s.replace("\\", "").replace("{", "(").replace("}", ")").strip()


def build_ass(words, t0, t1, out: Path):
    """Scribe words 중 [t0,t1] 구간을 잡아 (구간시작=0 기준) ASS 자막 생성. ~2.2초/줄 그룹."""
    ev = []
    cur, cs, ce = [], None, None
    def flush():
        nonlocal cur, cs, ce
        if cur:
            txt = _ass_escape("".join(cur))
            if txt:
                ev.append((max(0, cs - t0), ce - t0, txt))
        cur, cs, ce = [], None, None
    for w in words:
        if w.get("type") != "word":
            continue
        s, e = w.get("start", 0), w.get("end", 0)
        if e < t0 or s > t1:
            continue
        if cs is None:
            cs = s
        cur.append(w["text"] + (" " if not w["text"].endswith(("다", "요", "죠", "까", ".", "?", "!")) else ""))
        ce = e
        if (ce - cs) >= 2.2 or w["text"].endswith((".", "?", "!", "다", "요", "죠")):
            flush()
    flush()

    def ts(t):
        h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
        return f"{h}:{m:02d}:{s:05.2f}"
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: sub,NanumSquareB,44,&H00FFFFFF,&H00000000,&H96000000,1,3,0,3,2,60,60,54,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    body = "".join(f"Dialogue: 0,{ts(s)},{ts(e)},sub,,0,0,0,,{t}\n" for s, e, t in ev)
    out.write_text(head + body, encoding="utf-8")
    return len(ev)


def _title_band_png(seg_label: str, main: str, out: Path):
    """세그먼트 상단 반투명 타이틀 밴드 PNG (하단 자막과 안 겹치게 위쪽)."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 40, W, 214], fill=(14, 14, 16, 210))
    d.rectangle([0, 210, W, 214], fill=(*YELLOW, 255))
    fs = ImageFont.truetype(FONT_B, 32)
    d.text((88, 60), seg_label, font=fs, fill=YELLOW)
    fm = ImageFont.truetype(FONT_B, 46)
    for j, ln in enumerate(_wrap(d, main, fm, W - 180)[:2]):
        d.text((88, 104 + j * 54), ln, font=fm, fill=(245, 245, 245))
    img.save(out)


def segment(clip_mp4: Path, stt_json: Path, start: float, end: float, out: Path, work: Path,
            seg_label: str = "", title: str = ""):
    """프록시 [start,end] 트림 → 자막 구움 + (title 주면) 상단 타이틀 밴드 처음 4.5초 페이드 오버레이."""
    words = json.loads(stt_json.read_text())["words"] if stt_json.exists() else []
    ass = work / (out.stem + ".ass")
    build_ass(words, start, end, ass)
    base = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=30,subtitles='{ass}'"
    if title:
        band = work / (out.stem + "_band.png")
        _title_band_png(seg_label, title, band)
        fc = (f"[0:v]{base}[bg];"
              f"[1:v]format=rgba,fade=t=in:st=0:d=0.4:alpha=1,fade=t=out:st=4.1:d=0.4:alpha=1[tb];"
              f"[bg][tb]overlay=0:0:enable='between(t,0,4.5)'[v]")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start}", "-to", f"{end}",
                        "-i", str(clip_mp4), "-loop", "1", "-framerate", "30", "-i", str(band),
                        "-filter_complex", fc, "-map", "[v]", "-map", "0:a", "-shortest",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "44100", str(out)], check=True)
    else:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start}", "-to", f"{end}",
                        "-i", str(clip_mp4), "-vf", base, "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-ar", "44100", str(out)], check=True)


def segment_av(video_clip: Path, vstart: float, audio_clip: Path, astart: float, aend: float,
               stt_json: Path, out: Path, work: Path, seg_label: str = "", title: str = ""):
    """영상은 video_clip[vstart~](DJI 시술컷), 소리·자막은 audio_clip[astart~aend](MVI 인터뷰 설명).
    DJI 다이나믹 화면 위에 인터뷰 설명이 나레이션·자막으로 흐른다. 영상은 소리 길이에 맞춰 루프."""
    words = json.loads(stt_json.read_text())["words"] if stt_json.exists() else []
    alen = aend - astart
    ass = work / (out.stem + ".ass")
    build_ass(words, astart, aend, ass)
    base = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=30,subtitles='{ass}'"
    band = work / (out.stem + "_band.png")
    _title_band_png(seg_label, title, band)
    fc = (f"[0:v]{base}[bg];"
          f"[2:v]format=rgba,fade=t=in:st=0:d=0.4:alpha=1,fade=t=out:st=4.1:d=0.4:alpha=1[tb];"
          f"[bg][tb]overlay=0:0:enable='between(t,0,4.5)'[v]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error",
                    "-stream_loop", "-1", "-ss", f"{vstart}", "-t", f"{alen}", "-an", "-i", str(video_clip),
                    "-ss", f"{astart}", "-to", f"{aend}", "-i", str(audio_clip),
                    "-loop", "1", "-framerate", "30", "-i", str(band),
                    "-filter_complex", fc, "-map", "[v]", "-map", "1:a", "-shortest",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "44100", str(out)], check=True)


def _dur(p: Path) -> float:
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", str(p)], check=True, capture_output=True, text=True).stdout.strip())


def crossfade_concat(clips: list[Path], out: Path, d: float = 0.6) -> Path:
    """클립들을 xfade(영상)+acrossfade(오디오)로 매끄럽게 이어붙임 (하드컷·무음브레이크 없음)."""
    durs = [_dur(c) for c in clips]
    inputs = []
    for c in clips:
        inputs += ["-i", str(c)]
    vparts, aparts = [], []
    vlab, alab, offset = "[0:v]", "[0:a]", 0.0
    for i in range(1, len(clips)):
        offset += durs[i - 1] - d
        vout, aout = f"[v{i}]", f"[a{i}]"
        vparts.append(f"{vlab}[{i}:v]xfade=transition=fade:duration={d}:offset={offset:.3f}{vout}")
        aparts.append(f"{alab}[{i}:a]acrossfade=d={d}{aout}")
        vlab, alab = vout, aout
    fc = ";".join(vparts + aparts)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", fc,
                    "-map", vlab, "-map", alab, "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", str(out)], check=True)
    return out


def assemble(edl, proxy_dir: Path, out: Path, bgm: Path, work: Path, open_title: str):
    """오프닝 타이틀 + 세그먼트(상단 타이틀 오버레이) 크로스페이드 조립 + BGM 언더.
    무음 타이틀카드를 없애 말소리가 끊기지 않고, 세그먼트 사이는 크로스페이드로 이어진다."""
    work.mkdir(parents=True, exist_ok=True)
    clips = []
    op = work / "open.mp4"
    title_card(open_title, "AT NOWN · 두피 스케일링", 4.0, op, opening=True)
    clips.append(op)
    for i, item in enumerate(edl):
        seg = work / f"seg{i}.mp4"
        segment(proxy_dir / f"mvi_{item['clip']}_720.mp4",
                proxy_dir / f"mvi_{item['clip']}_720.stt.json",
                item["start"], item["end"], seg, work,
                seg_label=item.get("seg", ""), title=item.get("title", ""))
        clips.append(seg)
    body = work / "body.mp4"
    crossfade_concat(clips, body, d=0.6)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(body),
                    "-stream_loop", "-1", "-i", str(bgm),
                    "-filter_complex", "[1:a]volume=0.06[b];[0:a][b]amix=inputs=2:duration=first:dropout_transition=0[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-shortest", str(out)], check=True)
    return out
