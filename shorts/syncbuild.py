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
          timeout: int = 300, trim_pauses: bool = True, max_gap: float = 0.30) -> tuple[list[Line], Path]:
    """나레이션을 타임스탬프와 함께 합성하고, phrases를 목소리에 정렬한 Line 목록을 만든다.

    phrases: (raw, disp, en, emph)
      raw  = narr_text의 그대로 substring(정렬 기준)
      disp = 화면 표시용(줄바꿈 \n만 추가, 단어는 raw와 동일 — verbatim 유지)
      en   = 영어 자막(한글 아래 붙음) or None
      emph = 강조(글자확대) 여부
    trim_pauses: 일레븐랩스가 제멋대로 벌리는 과한 쉼을 자동 트리밍(부호=PUNCT_TARGET, 무부호=max_gap 상한).
      2026-07-28 이찬호 지적("능력은 뒤 너무 쉰다")의 코드 수정 — collect_pause_edits를 파이프라인에 물림.
      자막 타이밍도 트리밍 반영해 재계산(싱크 유지). 출력은 .m4a(aac).
    반환: (timed Lines, 합성된 오디오 경로)
    """
    resp = tts.synthesize_full_with_timestamps(tts.apply_synth_fixes(narr_text), creds, timeout=timeout)
    out = Path(out_mp3)
    al = resp["alignment"]
    chars = al["characters"]
    cs = al["character_start_times_seconds"]
    ce = al["character_end_times_seconds"]
    # 정렬 기준 = 합성한 텍스트(=apply_synth_fixes 적용본). raw도 같은 fix를 거쳐야 substring 매칭됨.
    spans = tts.align_line_spans(
        [tts.apply_synth_fixes(p[0]) for p in phrases], chars, cs, ce, speed=1.0,
    )
    if trim_pauses:
        edits = tts.collect_pause_edits(chars, cs, ce, tts.PUNCT_TARGET, max_gap=max_gap)
        out = out.with_suffix(".m4a")
        raw_tmp = out.with_name("_raw_" + out.stem + ".mp3")
        raw_tmp.write_bytes(base64.b64decode(resp["audio_base64"]))
        tts._apply_pause_edits(raw_tmp, out, edits, speed=1.0)  # speed=1.0: 템포 유지, 쉼만 트리밍
        raw_tmp.unlink(missing_ok=True)
        spans = [(tts._remap_pause(st, edits), tts._remap_pause(et, edits)) for st, et in spans]
    else:
        out.write_bytes(base64.b64decode(resp["audio_base64"]))
    lines: list[Line] = []
    for (raw, disp, en, emph), (st, et) in zip(phrases, spans):
        txt = (SS.EMPHASIS_INLINE if emph else "") + SS.ko_en(disp, en)
        lines.append(Line(text=txt, start=round(st, 2), end=round(et, 2)))
    return lines, out
