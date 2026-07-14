"""대사 스크립트 파싱과 ASS 자막 생성.

스크립트 파일 형식 (영상과 같은 이름의 .txt):

    # 제목: 정착 미용실 찾는 법
    # 설명: 설명 문구
    # 태그: 미용실,헤어,쇼츠
    00:00-00:03 첫 대사
    00:03-00:07 둘째 대사

타이밍(MM:SS 또는 MM:SS.s)은 생략 가능 — 생략하면 영상 길이에 맞춰 균등 배분한다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_TIMED_RE = re.compile(r"^(\d{1,2}:\d{2}(?:\.\d)?)\s*-\s*(\d{1,2}:\d{2}(?:\.\d)?)\s+(.+)$")
_META_RE = re.compile(r"^#\s*(제목|설명|태그)\s*:\s*(.*)$")


@dataclass
class Line:
    text: str
    start: float | None = None  # 초 단위, None이면 자동 배분
    end: float | None = None


@dataclass
class Script:
    title: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    lines: list[Line] = field(default_factory=list)


def _parse_time(value: str) -> float:
    minutes, seconds = value.split(":")
    return int(minutes) * 60 + float(seconds)


def parse_script(text: str) -> Script:
    script = Script()
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        meta = _META_RE.match(line)
        if meta:
            key, value = meta.group(1), meta.group(2).strip()
            if key == "제목":
                script.title = value
            elif key == "설명":
                script.description = value
            else:
                script.tags = [t.strip() for t in value.split(",") if t.strip()]
            continue
        timed = _TIMED_RE.match(line)
        if timed:
            script.lines.append(
                Line(text=timed.group(3).strip(), start=_parse_time(timed.group(1)), end=_parse_time(timed.group(2)))
            )
        else:
            script.lines.append(Line(text=line))
    return script


def assign_timings(lines: list[Line], duration: float) -> list[Line]:
    """타이밍이 없는 라인들에 영상 길이를 균등 배분한다 (이미 있으면 유지)."""
    untimed = [l for l in lines if l.start is None or l.end is None]
    if not untimed:
        return lines
    slot = duration / len(lines)
    cursor = 0.0
    for line in lines:
        if line.start is None or line.end is None:
            line.start = cursor
            line.end = min(cursor + slot, duration)
        cursor = line.end
    return lines


DEFAULT_STYLE = {
    "font": "AppleSDGothicNeo-Bold",
    "size": 64,
    "primary_color": "&H00FFFFFF",   # 흰 글자 (ASS는 BGR 순서)
    "outline_color": "&H00000000",   # 검정 외곽
    "back_color": "&H80000000",      # 반투명 검정 박스
    "border_style": 4,               # 4 = 배경 박스
    "outline": 2,
    "alignment": 2,                  # 하단 중앙
    "margin_v": 260,                 # 쇼츠 UI 피해서 아래에서 띄우기
}


def _ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int(seconds % 3600 // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def to_ass(lines: list[Line], style: dict | None = None, width: int = 1080, height: int = 1920) -> str:
    """타이밍이 배정된 라인들을 ASS 자막 문서로 변환한다."""
    st = dict(DEFAULT_STYLE)
    if style:
        st.update(style)
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV
Style: Default,{st['font']},{st['size']},{st['primary_color']},{st['outline_color']},{st['back_color']},1,{st['border_style']},{st['outline']},0,{st['alignment']},60,60,{st['margin_v']}

[Events]
Format: Layer, Start, End, Style, Text
"""
    events = []
    for line in lines:
        if line.start is None or line.end is None:
            raise ValueError(f"타이밍이 배정되지 않은 라인: {line.text!r} (assign_timings 먼저 호출)")
        text = line.text.replace("\n", "\\N")
        events.append(f"Dialogue: 0,{_ass_time(line.start)},{_ass_time(line.end)},Default,{text}")
    return header + "\n".join(events) + "\n"
