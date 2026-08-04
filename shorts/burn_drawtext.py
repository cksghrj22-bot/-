"""macOS libass 폰트 폴백을 피하는 자막 버너.

ASS의 타이밍·위치를 읽되 글자는 drawtext ``fontfile=``로 직접 그려 교보손글씨를
확실히 사용한다. ``ffmpeg-full``이 설치된 Mac 렌더 노드용이다.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import textwrap
from pathlib import Path

from .render import BGM_EVEN, probe_duration

ROOT = Path(__file__).resolve().parent.parent
FFMPEG = "/usr/local/opt/ffmpeg-full/bin/ffmpeg"
KYOBO = ROOT / "assets/fonts/KyoboHandwriting2019.ttf"
GOTHIC = ROOT / "assets/fonts/nsqr_eb.ttf"


def _sec(value: str) -> float:
    h, m, s = value.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def parse_events(path: str | Path) -> list[dict]:
    events = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.startswith("Dialogue:"):
            continue
        layer, start, end, style, text = line.removeprefix("Dialogue:").strip().split(",", 4)
        marker = re.search(r"\{\\fs60[^}]*\}", text)
        ko_raw = text[:marker.start()] if marker else text
        en_raw = text[marker.end():] if marker else ""
        clean = lambda s: re.sub(r"\{[^}]*\}", "", s).replace(r"\N", "\n").strip()
        pos = re.search(r"\\pos\(540,(\d+)\)", text)
        events.append({
            "start": _sec(start), "end": _sec(end), "style": style,
            "ko": clean(ko_raw), "en": clean(en_raw),
            "big": r"\an5" in text or r"\fs104" in text,
            "pos_y": int(pos.group(1)) if pos else None,
        })
    return events


def _esc(value: str | Path) -> str:
    return str(value).replace("\\", "\\\\").replace(":", r"\:").replace("'", r"\'")


def _wrap_ko(text: str, width: int = 11) -> str:
    """한글 훅을 단어 경계에서 1080px 안전폭으로 나눈다."""
    lines: list[str] = []
    for paragraph in text.splitlines():
        current = ""
        for word in paragraph.split():
            candidate = f"{current} {word}".strip()
            if current and len(candidate) > width:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
    return "\n".join(lines)


def burn(base: str | Path, ass: str | Path, narration: str | Path, bgm: str | Path,
         out: str | Path) -> Path:
    base, ass, narration, bgm, out = map(Path, (base, ass, narration, bgm, out))
    duration = probe_duration(base)
    work = ass.parent / "drawtext"
    work.mkdir(parents=True, exist_ok=True)
    filters, cur = [], "[0:v]"
    for idx, ev in enumerate(parse_events(ass)):
        if ev["style"] == "Outro":
            ko_size, ko_y, box = 64, "(h-text_h)/2", True
        elif ev["big"]:
            # 실사 훅도 1080px 안전폭 안에 두고 한글 QC 규격(70~82px)을 지킨다.
            ko_size, ko_y, box = 82, "720", False
        else:
            ko_size = 78
            ko_y = str(max(820, (ev["pos_y"] or 1280) - 180))
            box = True
        ko_file = work / f"{idx:02d}_ko.txt"
        # 이 교보손글씨 파일은 ASCII space 글리프가 비어 있어 drawtext가
        # 띄어쓰기를 tofu(□)로 표시한다. 한글 폰트에 포함된 전각 공백을 쓴다.
        ko_text = _wrap_ko(ev["ko"]) if ev["big"] else ev["ko"]
        ko_file.write_text(ko_text.replace(" ", "\u3000"), encoding="utf-8")
        nxt = f"[v{idx}k]"
        box_opts = ":box=1:boxcolor=black@0.88:boxborderw=24" if box else ""
        filters.append(
            f"{cur}drawtext=fontfile='{_esc(KYOBO)}':textfile='{_esc(ko_file)}':"
            f"fontsize={ko_size}:fontcolor=white:line_spacing=12:x=(w-text_w)/2:y={ko_y}"
            f"{box_opts}:enable='between(t,{ev['start']:.3f},{ev['end']:.3f})'{nxt}"
        )
        cur = nxt
        if ev["en"]:
            en_file = work / f"{idx:02d}_en.txt"
            # 1080px 세로 화면에서 58px 영문이 좌우로 잘리지 않도록 줄 폭을 제한한다.
            en_file.write_text("\n".join(textwrap.wrap(ev["en"], width=28)), encoding="utf-8")
            en_y = "1080" if ev["big"] else str(int(ko_y) + 205)
            nxt = f"[v{idx}e]"
            filters.append(
                f"{cur}drawtext=fontfile='{_esc(GOTHIC)}':textfile='{_esc(en_file)}':"
                f"fontsize=58:fontcolor=0xF0F0F0:line_spacing=8:x=(w-text_w)/2:y={en_y}:"
                f"box=1:boxcolor=black@0.72:boxborderw=16:enable='between(t,{ev['start']:.3f},{ev['end']:.3f})'{nxt}"
            )
            cur = nxt
    v_st, a_st = max(0.0, duration - 1.3), max(0.0, duration - 1.6)
    filters.append(f"{cur}fade=t=out:st={v_st:.3f}:d=1.3[vout]")
    filters.append(
        f"[1:a]apad=whole_dur={duration:.3f}[narp];"
        f"[2:a]{BGM_EVEN},volume=1.0[bg];"
        f"[narp][bg]amix=inputs=2:normalize=0:duration=first:dropout_transition=0[aout];"
        f"[aout]afade=t=out:st={a_st:.3f}:d=1.6,loudnorm=I=-18:TP=-2:LRA=11[aoutf]"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        FFMPEG, "-v", "error", "-y", "-i", str(base), "-i", str(narration),
        "-stream_loop", "-1", "-i", str(bgm), "-filter_complex", ";".join(filters),
        "-map", "[vout]", "-map", "[aoutf]", "-t", f"{duration:.3f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k", str(out),
    ], check=True)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("base"); ap.add_argument("ass"); ap.add_argument("narration")
    ap.add_argument("bgm"); ap.add_argument("out")
    a = ap.parse_args()
    print(burn(a.base, a.ass, a.narration, a.bgm, a.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
