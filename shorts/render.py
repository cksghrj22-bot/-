"""ffmpeg 렌더링: 자막 굽기 + BGM 믹싱. (Mac에서 실행: brew install ffmpeg)"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .subtitles import Script, assign_timings, to_ass


import re
import shutil as _shutil


def _ffmpeg_info(video: str | Path) -> str:
    """ffprobe가 없는 환경 폴백: `ffmpeg -i` stderr에서 메타데이터를 읽는다."""
    result = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(video)], capture_output=True, text=True)
    return result.stderr


def probe_duration(video: str | Path) -> float:
    """영상 길이(초). ffprobe 우선, 없으면 ffmpeg stderr 파싱."""
    if _shutil.which("ffprobe"):
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(video)],
            capture_output=True, text=True, check=True,
        )
        return float(json.loads(result.stdout)["format"]["duration"])
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", _ffmpeg_info(video))
    if not m:
        raise RuntimeError(f"영상 길이를 읽을 수 없음: {video}")
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def has_audio(video: str | Path) -> bool:
    if _shutil.which("ffprobe"):
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
             "stream=index", "-of", "json", str(video)],
            capture_output=True, text=True, check=True,
        )
        return bool(json.loads(result.stdout).get("streams"))
    return "Audio:" in _ffmpeg_info(video)


def render(
    video: str | Path,
    script: Script,
    output: str | Path,
    bgm: str | Path | None = None,
    bgm_volume: float = 0.15,
    style: dict | None = None,
    title_style: dict | None = None,
    layout: str = "full",
    workdir: str | Path = ".",
    narration: str | Path | None = None,
    outro: str | None = None,
    outro_style: dict | None = None,
) -> Path:
    """자막을 굽고 (있다면) BGM을 원본 음성 위에 깔아 output으로 렌더링한다.

    narration이 있으면(TTS 보이스클론 트랙) 원본 음성을 대체하고 BGM은 그 아래에 깐다.
    outro를 주면 마지막 몇 초 하단에 얇은 브랜딩 줄이 페이드로 뜬다.
    """
    video = Path(video)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    duration = probe_duration(video)
    lines = assign_timings(list(script.lines), duration)
    ass_path = Path(workdir) / f"{video.stem}.ass"
    ass_path.write_text(
        to_ass(lines, style=style, title=script.title or None, title_style=title_style,
               outro=outro, outro_style=outro_style, total_duration=duration),
        encoding="utf-8",
    )

    cmd: list[str] = ["ffmpeg", "-y", "-i", str(video)]
    if layout == "letterbox":
        # 채널 v9 구성: 원본을 가로 맞춤 → 위아래 검은 여백 → 제목은 상단 여백, 자막은 영상 위
        base = f"[0:v]scale=1080:-2,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black[vbase];[vbase]"
    else:
        base = "[0:v]"
    filters = [f"{base}ass={ass_path}[vout]"]
    maps = ["-map", "[vout]"]

    if narration:
        cmd += ["-i", str(narration)]
        nar_idx = 1
        if bgm:
            cmd += ["-stream_loop", "-1", "-i", str(bgm)]
            filters.append(
                f"[{nar_idx + 1}:a]volume={bgm_volume}[bg];"
                f"[{nar_idx}:a][bg]amix=inputs=2:normalize=0:duration=first:dropout_transition=0[aout]"
            )
        else:
            filters.append(f"[{nar_idx}:a]anull[aout]")
        maps += ["-map", "[aout]", "-shortest"]
    elif bgm:
        cmd += ["-stream_loop", "-1", "-i", str(bgm)]
        if has_audio(video):
            filters.append(
                f"[1:a]volume={bgm_volume}[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=0[aout]"
            )
        else:
            filters.append(f"[1:a]volume={bgm_volume}[aout]")
        maps += ["-map", "[aout]", "-shortest"]
    elif has_audio(video):
        maps += ["-map", "0:a"]

    cmd += [
        "-filter_complex", ";".join(filters),
        *maps,
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        str(output),
    ]
    subprocess.run(cmd, check=True)
    return output
