"""ffmpeg 렌더링: 자막 굽기 + BGM 믹싱. (Mac에서 실행: brew install ffmpeg)"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .subtitles import Script, assign_timings, to_ass


def probe_duration(video: str | Path) -> float:
    """ffprobe로 영상 길이(초)를 얻는다."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "json", str(video),
        ],
        capture_output=True, text=True, check=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def has_audio(video: str | Path) -> bool:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
         "stream=index", "-of", "json", str(video)],
        capture_output=True, text=True, check=True,
    )
    return bool(json.loads(result.stdout).get("streams"))


def render(
    video: str | Path,
    script: Script,
    output: str | Path,
    bgm: str | Path | None = None,
    bgm_volume: float = 0.15,
    style: dict | None = None,
    workdir: str | Path = ".",
) -> Path:
    """자막을 굽고 (있다면) BGM을 원본 음성 위에 깔아 output으로 렌더링한다."""
    video = Path(video)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    duration = probe_duration(video)
    lines = assign_timings(list(script.lines), duration)
    ass_path = Path(workdir) / f"{video.stem}.ass"
    ass_path.write_text(to_ass(lines, style=style), encoding="utf-8")

    cmd: list[str] = ["ffmpeg", "-y", "-i", str(video)]
    filters = [f"[0:v]ass={ass_path}[vout]"]
    maps = ["-map", "[vout]"]

    if bgm:
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
