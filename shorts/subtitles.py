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
_EN_SEP = re.compile(r"\s*\|\|\s*")  # '한글 || English' 구분자 (외국인 유치용 영어 자막)


def _split_ko_en(text: str) -> tuple[str, str | None]:
    """'한글 || English' → ('한글', 'English'). 구분자 없으면 (한글, None)."""
    parts = _EN_SEP.split(text, maxsplit=1)
    if len(parts) == 2 and parts[1].strip():
        return parts[0].strip(), parts[1].strip()
    return text.strip(), None


@dataclass
class Line:
    text: str
    start: float | None = None  # 초 단위, None이면 자동 배분
    end: float | None = None
    en: str | None = None       # 영어 자막(외국인 유치용) — 한글 아래 줄에 표시. 없으면 미표시.


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
        if line.startswith("#"):
            continue  # 알 수 없는 주석(# 라인: 등)은 대사가 아니다 — 건너뛴다 (나레이션 오염 방지)
        timed = _TIMED_RE.match(line)
        if timed:
            ko, en = _split_ko_en(timed.group(3))
            script.lines.append(
                Line(text=ko, start=_parse_time(timed.group(1)), end=_parse_time(timed.group(2)), en=en)
            )
        else:
            ko, en = _split_ko_en(line)
            script.lines.append(Line(text=ko, en=en))
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

# 영어 자막 (외국인 유치용 · 2026-07-21 이찬호) — 한글 자막 바로 아래, 한글보다 작게·흰 글씨+반투명 박스.
# 한글(margin_v 260)보다 낮은 margin_v로 화면 더 아래에 깔린다(겹침 없음). 읽기 우선 → 또렷한 외곽+옅은 박스.
DEFAULT_EN_STYLE = {
    "font": "AppleSDGothicNeo-Bold",  # 라틴 글리프 포함 — 영어도 안전
    "size": 52,                       # 한글(64)보다 작게 = 보조 자막 (2026-07-21 이찬호: 영어 좀 더 크게 42→52)
    "primary_color": "&H00F0F0F0",    # 살짝 낮춘 흰색(주자막과 위계)
    "outline_color": "&H00000000",
    "box_color": "000000",
    "box_opacity": 0,                 # 박스 없음 — 글씨만(2026-07-21 이찬호: 박스까지면 화면 복잡)
    "border_style": 1,               # 1 = 외곽선+그림자만(박스 X)
    "outline": 2.4,                   # 박스 없으니 외곽 두껍게 = 어떤 배경에서도 읽힘
    "shadow": 1,                      # 옅은 그림자로 가독성 보강
    "alignment": 2,                   # 하단 중앙
    "margin_v": 170,                  # 한글(260)보다 아래 = 한글 밑에 위치
}

# 하단 아웃트로 (브랜딩 줄: "SNS에 일기를 쓰고 있어요" — 얇게·작게·반투명, 마지막 몇 초만)
# 2026-07-15 이찬호 지시: "사람 차노" 브랜딩. 저장 CTA가 아니라 조용한 상태 표시. 박스 없이 얇게.
DEFAULT_OUTRO_STYLE = {
    "font": "Kyobo Handwriting 2019",
    "size": 46,
    "primary_color": "&H00FFFFFF",   # 흰 글자
    "outline_color": "&H00000000",
    "box_color": "000000",
    "box_opacity": 0,                # 박스 없음 (얇게 스며들듯)
    "border_style": 1,               # 외곽선만
    "outline": 1,
    "alignment": 2,                  # 하단 중앙
    "margin_v": 90,
    "alpha": "80",                   # 반투명 (00=불투명, FF=투명) — "얇게"
    "fade": [600, 400],              # 페이드 인/아웃(ms)
    "dur": 2.8,                      # 마지막 몇 초 노출
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
        f"{_back_color(st)},1,{st['border_style']},{st['outline']},{st.get('shadow', 0)},"
        f"{st['alignment']},60,60,{st['margin_v']}"
    )


def _line_units(s: str) -> float:
    """줄의 대략적 폭(폰트크기 1당). 전각(한글)≈1.0·공백≈0.4·그 외≈0.55."""
    u = 0.0
    for ch in s:
        if ch == " ":
            u += 0.4
        elif ord(ch) > 0x2E00:
            u += 1.0
        else:
            u += 0.55
    return u


def fit_title(text: str, base_size: int, width: int, margin: int = 70, floor: int = 100) -> tuple[int, str]:
    """제목이 화면을 넘지 않게 (크기, 표시텍스트) 반환.

    규칙(이찬호): **제목은 항상 자막보다 크게. 길면 2줄로(크기 유지), 절대 자막보다 작아지지 않는다.**
    ① 한 줄에 들어가면 그대로. ② 안 들어가면 무조건 2줄로 나눠 크기 확보(대개 base 유지).
    floor = 자막 크기(+여유) — 최소한 이보다는 크게 유지하려 한다. 폭은 절대 안 넘김.
    """
    usable = width - 2 * margin
    u = _line_units(text)
    if u <= 0 or base_size * u <= usable:
        return base_size, text
    spaces = [i for i, ch in enumerate(text) if ch == " "]
    if spaces:
        mid = len(text) / 2
        bi = min(spaces, key=lambda i: abs(i - mid))
        l1, l2 = text[:bi], text[bi + 1:]
        longest = max(_line_units(l1), _line_units(l2))
        size2 = min(base_size, int(usable / longest)) if longest > 0 else base_size
        return size2, l1 + "\\N" + l2  # 2줄 — 짧은 제목이면 base 유지, 자막보다 큼
    return max(floor, int(usable / u)), text


def wrap_en(text: str, size: int, width: int, margin: int = 60, max_lines: int = 2) -> str:
    """영어 자막이 화면 폭을 넘으면 단어 경계로 최대 max_lines줄까지 접는다(\\N)."""
    usable = width - 2 * margin
    if _line_units(text) * size <= usable:
        return text
    words = text.split(" ")
    lines_out: list[str] = []
    cur = ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if _line_units(trial) * size > usable and cur:
            lines_out.append(cur)
            cur = w
            if len(lines_out) == max_lines - 1:
                # 마지막 줄: 남은 단어 다 붙인다(넘쳐도 한 줄로 — 크기 축소는 호출부에서)
                rest = " ".join(words[words.index(w):])
                lines_out.append(rest)
                cur = ""
                break
        else:
            cur = trial
    if cur:
        lines_out.append(cur)
    return "\\N".join(lines_out[:max_lines])


def to_ass(
    lines: list[Line],
    style: dict | None = None,
    width: int = 1080,
    height: int = 1920,
    title: str | None = None,
    title_style: dict | None = None,
    outro: str | None = None,
    outro_style: dict | None = None,
    total_duration: float | None = None,
    en_style: dict | None = None,
) -> str:
    """타이밍이 배정된 라인들을 ASS 자막 문서로 변환한다.

    title을 주면 상단 노란 박스 제목이 영상 전체에 표시된다 (채널 스타일).
    outro를 주면 마지막 몇 초 하단에 얇은 브랜딩 줄이 페이드로 뜬다 (사람 차노).
    total_duration = 영상 전체 길이(초). 주면 아웃트로를 영상 끝에 정확히 붙인다.
    """
    st = dict(DEFAULT_STYLE)
    if style:
        st.update(style)
    tst = dict(DEFAULT_TITLE_STYLE)
    if title_style:
        tst.update(title_style)
    if style and "font" in style and not (title_style and "font" in title_style):
        tst["font"] = style["font"]  # 본문 폰트를 지정하면 제목도 따라간다
    ost = dict(DEFAULT_OUTRO_STYLE)
    if outro_style:
        ost.update(outro_style)
    if style and "font" in style and not (outro_style and "font" in outro_style):
        ost["font"] = style["font"]  # 아웃트로도 본문 폰트를 따라간다
    est = dict(DEFAULT_EN_STYLE)
    if en_style:
        est.update(en_style)
    has_en = any(getattr(l, "en", None) for l in lines)
    title_text = title
    if title:
        # 제목은 항상 자막보다 크게(길면 2줄), 화면 폭은 안 넘김. floor = 자막 크기 + 여유.
        tst["size"], title_text = fit_title(
            title, int(tst.get("size", 96)), width, floor=int(st.get("size", 98)) + 2,
        )

    style_lines = [_style_line('Default', st), _style_line('Title', tst)]
    if outro:
        style_lines.append(_style_line('Outro', ost))
    if has_en:
        style_lines.append(_style_line('English', est))
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV
{chr(10).join(style_lines)}

[Events]
Format: Layer, Start, End, Style, Text
"""
    events = []
    for line in lines:
        if line.start is None or line.end is None:
            raise ValueError(f"타이밍이 배정되지 않은 라인: {line.text!r} (assign_timings 먼저 호출)")
        text = line.text.replace("\n", "\\N")
        events.append(f"Dialogue: 0,{_ass_time(line.start)},{_ass_time(line.end)},Default,{text}")
        en = getattr(line, "en", None)
        if en:
            en_text = wrap_en(en.replace("\n", " "), int(est.get("size", 44)), width)
            events.append(f"Dialogue: 0,{_ass_time(line.start)},{_ass_time(line.end)},English,{en_text}")
    last_end = max((l.end or 0) for l in lines) if lines else 60.0
    if title:
        tt = title_text.replace(chr(10), "\\N")
        if "\\N" in tt:
            # 2줄 제목: libass 기본 행간이 넓어서, 각 줄을 \pos로 찍어 간격을 직접 좁힌다.
            # line_gap = 폰트 크기 대비 줄 간격 비율(작을수록 촘촘). \an8=상단중앙 기준.
            gap = int(int(tst["size"]) * float(tst.get("line_gap", 0.85)))
            top = int(tst.get("margin_v", 110))
            cx = width // 2
            parts = tt.split("\\N")
            for i, part in enumerate(parts[:2]):
                y = top + i * gap
                events.insert(0 + i,
                    f"Dialogue: 1,{_ass_time(0)},{_ass_time(last_end)},Title,"
                    f"{{\\an8\\pos({cx},{y})}}{part}")
        else:
            events.insert(0, f"Dialogue: 1,{_ass_time(0)},{_ass_time(last_end)},Title,{tt}")
    if outro:
        vid_end = total_duration if total_duration is not None else last_end
        dur = float(ost.get("dur", 2.8))
        o_start = max(0.0, vid_end - dur)
        # 프레임 양자화 가드: 출력 mp4는 total_duration보다 최대 몇 프레임(~0.1s) 짧게 끝난다
        # (마지막 프레임 경계로 반올림). 아웃트로 끝을 total_duration에 딱 맞추면 verify가 '잘림'으로
        # 오탐 → 끝을 0.15s 당긴다(페이드아웃 중이라 눈에 안 보임). 2026-07-23 박제(렌더버그 #10).
        o_end = max(o_start + 0.5, vid_end - 0.15)
        fin, fout = (ost.get("fade") or [0, 0])[:2]
        # 글자(1a)·외곽선(3a)만 alpha 적용. 박스(BackColour=4a)는 style의 box_opacity가 제어하게
        # 남겨둔다 → 어두운 박스는 또렷하게 깔리고 글자만 원하는 투명도. (blanket \alpha는 박스까지 투명화)
        a = ost.get("alpha", "80")
        tag = f"{{\\fad({int(fin)},{int(fout)})\\1a&H{a}&\\3a&H{a}&}}"
        otext = outro.replace("\n", "\\N")
        events.append(f"Dialogue: 2,{_ass_time(o_start)},{_ass_time(o_end)},Outro,{tag}{otext}")
    return header + "\n".join(events) + "\n"
