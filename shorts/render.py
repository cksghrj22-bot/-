"""ffmpeg 렌더링: 자막 굽기 + BGM 믹싱. (Mac에서 실행: brew install ffmpeg)"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .subtitles import Script, assign_timings, to_ass


import re
import shutil as _shutil


# BGM을 고르게(들리게) 깔기 위한 컴프레서 체인. 피아노 루프의 조용한 구간이
# 아웃트로에 걸려도 '안 들리는' 일이 없게 다이내믹을 눌러 소리를 끌어올린다.
# (volume 스케일은 이 뒤에 곱해진다.)
BGM_EVEN = "dynaudnorm=f=100:g=15:p=0.9,acompressor=threshold=-28dB:ratio=4:makeup=5"


def _ffmpeg_info(video: str | Path) -> str:
    """ffprobe가 없는 환경 폴백: `ffmpeg -i` stderr에서 메타데이터를 읽는다."""
    result = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(video)], capture_output=True, text=True)
    return result.stderr


def probe_duration(video: str | Path) -> float:
    """영상 길이(초). ffprobe 우선, 없으면 ffmpeg stderr 파싱."""
    if _shutil.which("ffprobe"):
        # check=False + 실패 시 ffmpeg 파싱 폴백 — ffprobe가 간헐 실패해도 예외로 죽지 않는다.
        # (이게 없으면 _valid_bgm이 유효 BGM을 조용히 버려 음악이 사라지는 버그가 났다.)
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(video)],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            try:
                return float(json.loads(result.stdout)["format"]["duration"])
            except Exception:
                pass
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
    # 끝 여운: 마지막에 탁 끊기지 않게 영상·소리를 스륵 페이드아웃한다 (2026-07-17 이찬호).
    v_fade, a_fade = 1.3, 1.6
    v_st = max(0.0, duration - v_fade)
    filters = [f"{base}ass={ass_path},fade=t=out:st={v_st:.3f}:d={v_fade}[vout]"]
    maps = ["-map", "[vout]"]

    if narration:
        cmd += ["-i", str(narration)]
        nar_idx = 1
        if bgm:
            cmd += ["-stream_loop", "-1", "-i", str(bgm)]
            # 나레이션을 영상 전체 길이(배경=나레이션+tail)만큼 무음 패딩 → amix duration=first가
            # 영상 끝까지 이어지고, 루프 BGM이 나레이션 뒤 아웃트로 구간까지 계속 깔린다.
            # BGM은 컴프레서(acompressor)로 다이내믹을 눌러 조용한 루프 구간도 '들리게' 고르게 깐다.
            # (2026-07-17: 06편이 피아노 루프의 조용한 구간에 걸려 아웃트로 -52dB로 안 들리던 것 방지.)
            filters.append(
                f"[{nar_idx}:a]apad=whole_dur={duration:.3f}[narp];"
                f"[{nar_idx + 1}:a]{BGM_EVEN},volume={bgm_volume}[bg];"
                f"[narp][bg]amix=inputs=2:normalize=0:duration=first:dropout_transition=0[aout]"
            )
        else:
            # BGM 없으면 나레이션도 영상 길이만큼 패딩(뒤는 무음) → 아웃트로 구간까지 영상 유지.
            filters.append(f"[{nar_idx}:a]apad=whole_dur={duration:.3f}[aout]")
        # -shortest 금지: 나레이션 길이로 자르면 아웃트로(배경 tail 구간)가 잘린다. 아래 -t가 배경 길이로 고정.
        maps += ["-map", "[aout]"]
    elif bgm:
        cmd += ["-stream_loop", "-1", "-i", str(bgm)]
        if has_audio(video):
            filters.append(
                f"[1:a]{BGM_EVEN},volume={bgm_volume}[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=0[aout]"
            )
        else:
            filters.append(f"[1:a]{BGM_EVEN},volume={bgm_volume}[aout]")
        maps += ["-map", "[aout]", "-shortest"]
    elif has_audio(video):
        maps += ["-map", "0:a"]

    # 끝 여운: 오디오 페이드아웃. 나레이션이 끝난 뒤 순수 BGM 꼬리(아웃트로 구간)에서
    # 루프 BGM이 다시 시작되며 '쓸데없는 반복/드론음'이 들리던 문제(2026-07-20 이찬호 A-1 지적)를
    # 막기 위해, 나레이션이 끝나는 지점부터 BGM을 스륵 내린다 — 꼬리에 또렷한 반복음이 남지 않게.
    if "[aout]" in maps:
        nar_end = max((l.end for l in lines if l.end is not None), default=duration)
        # 나레이션 끝 직후부터 페이드 시작(단, 최소 a_fade는 확보). 시작 뒤 duration까지 서서히.
        a_st = max(0.0, min(duration - a_fade, nar_end - 0.15))
        a_dur = max(a_fade, duration - a_st)
        filters.append(f"[aout]afade=t=out:st={a_st:.3f}:d={a_dur:.3f}[aoutf]")
        maps = ["[aoutf]" if m == "[aout]" else m for m in maps]

    cmd += [
        "-filter_complex", ";".join(filters),
        *maps,
        "-t", f"{duration:.3f}",   # 출력 길이를 배경(=나레이션+tail) 길이로 고정 → 아웃트로 온전히 보임
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        str(output),
    ]
    subprocess.run(cmd, check=True)
    return output
