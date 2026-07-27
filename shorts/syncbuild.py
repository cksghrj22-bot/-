"""자막 싱크 빌더 — 영구 박제(2026-07-27 이찬호 "이거 박제 중요해").

원칙(형 확정):
- 자막은 **나레이션 그대로**(요약/설명체 금지). "대사가 넘어가야 잘 보이고 오래 본다."
- 타이밍은 **일레븐랩스 타임스탬프**로 목소리에 정확히 맞춘다(분수 배분 금지 = 싱크 버그).

쓰는 법:
    from shorts import syncbuild, shortstyle as SS
    phrases = [(raw, disp, en, emph), ...]   # raw=나레이션 그대로 substring, disp=줄바꿈만, en, 강조여부
    lines, narr_path = syncbuild.build(full_narration_text, phrases, creds, out_mp3)
    render(video, Script(lines=lines), out, narration=narr_path, style=SS.SUB, ...)

raw는 반드시 full_narration_text의 **연속 부분문자열**(순서대로)이어야 정렬된다.
"""
from __future__ import annotations
import base64
from pathlib import Path

from .subtitles import Line
from . import tts
from . import shortstyle as SS


def build(narr_text: str, phrases: list, creds: dict, out_mp3: str | Path,
          timeout: int = 300) -> tuple[list[Line], Path]:
    """나레이션을 타임스탬프와 함께 합성하고, phrases를 목소리에 정렬한 Line 목록을 만든다.

    phrases: (raw, disp, en, emph)
      raw  = narr_text의 그대로 substring(정렬 기준)
      disp = 화면 표시용(줄바꿈 \n만 추가, 단어는 raw와 동일 — verbatim 유지)
      en   = 영어 자막(한글 아래 붙음) or None
      emph = 강조(글자확대) 여부
    반환: (timed Lines, 합성된 mp3 경로)
    """
    resp = tts.synthesize_full_with_timestamps(tts.apply_synth_fixes(narr_text), creds, timeout=timeout)
    out = Path(out_mp3)
    out.write_bytes(base64.b64decode(resp["audio_base64"]))
    al = resp["alignment"]
    spans = tts.align_line_spans(
        [p[0] for p in phrases], al["characters"],
        al["character_start_times_seconds"], al["character_end_times_seconds"], speed=1.0,
    )
    lines: list[Line] = []
    for (raw, disp, en, emph), (st, et) in zip(phrases, spans):
        txt = (SS.EMPHASIS_INLINE if emph else "") + SS.ko_en(disp, en)
        lines.append(Line(text=txt, start=round(st, 2), end=round(et, 2)))
    return lines, out
