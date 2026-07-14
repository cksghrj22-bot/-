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
    "box_color": "000000",           # 자막 박스 색 (RGB hex)
    "box_opacity": 65,               # 박스 불투명도 % (0=투명, 100=완전 불투명)
    "border_style": 4,               # 4 = 배경 박스
    "outline": 2,
    "alignment": 2,                  # 하단 중앙
    "margin_v": 260,                 # 쇼츠 UI 피해서 아래에서 띄우기
}

# 상단 제목 (채널 스타일: 노란 박스 + 검정 글자)
DEFAULT_TITLE_STYLE = {
    "font": "AppleSDGothicNeo-Bold",
    "size": 72,
    "primary_color": "&H00000000",   # 검정 글자
    "outline_color": "&H0000D7FF",
    "box_color": "FFD700",           # 노란 박스 (RGB)
    "box_opacity": 100,
    "border_style": 4,
    "outline": 3,
    "alignment": 8,                  # 상단 중앙
    "margin_v": 200,
}


def _back_color(style: dict) -> str:
    """box_color(RGB)+box_opacity(%) → ASS BackColour(&HAABBGGRR)."""
    rgb = style.get("box_color", "000000")
    r, g, b = rgb[0:2], rgb[2:4], rgb[4:6]
    alpha = 255 - round(255 * style.get("box_opacity", 65) / 100)  # ASS는 00=불투명
    return f"&H{alpha:02X}{b}{g}{r}".upper()


def _ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int(seconds % 3600 // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _style_line(name: str, st: dict) -> str:
    return (
        f"Style: {name},{st['font']},{st['size']},{st['primary_color']},{st['outline_color']},"
        f"{_back_color(st)},1,{st['border_style']},{st['outline']},0,{st['alignment']},60,60,{st['margin_v']}"
    )


def to_ass(
    lines: list[Line],
    style: dict | None = None,
    width: int = 1080,
    height: int = 1920,
    title: str | None = None,
    title_style: dict | None = None,
) -> str:
    """타이밍이 배정된 라인들을 ASS 자막 문서로 변환한다.

    title을 주면 상단 노란 박스 제목이 영상 전체에 표시된다 (채널 스타일).
    """
    st = dict(DEFAULT_STYLE)
    if style:
        st.update(style)
    tst = dict(DEFAULT_TITLE_STYLE)
    if title_style:
        tst.update(title_style)
    if style and "font" in style and not (title_style and "font" in title_style):
        tst["font"] = style["font"]  # 본문 폰트를 지정하면 제목도 따라간다

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV
{_style_line('Default', st)}
{_style_line('Title', tst)}

[Events]
Format: Layer, Start, End, Style, Text
"""
    events = []
    for line in lines:
        if line.start is None or line.end is None:
            raise ValueError(f"타이밍이 배정되지 않은 라인: {line.text!r} (assign_timings 먼저 호출)")
        text = line.text.replace("\n", "\\N")
        events.append(f"Dialogue: 0,{_ass_time(line.start)},{_ass_time(line.end)},Default,{text}")
    if title:
        end = max((l.end or 0) for l in lines) if lines else 60.0
        events.insert(0, f"Dialogue: 1,{_ass_time(0)},{_ass_time(end)},Title,{title.replace(chr(10), ' ')}")
    return header + "\n".join(events) + "\n"
