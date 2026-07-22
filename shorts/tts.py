"""일레븐랩스 보이스클론 TTS — 대본 줄별 나레이션 합성 + 자막 타임라인 배치.

정본 렌더(클론보이스 1.1배속·켄번스·페이드팝)는 본진 Creator OS build_reel.py.
이 모듈은 코드방/백업 경로: secrets/elevenlabs.json만 있으면
`python -m shorts run`이 자막 타이밍에 맞춘 나레이션 트랙을 만들어 믹싱한다.

secrets/elevenlabs.json 형식 (gitignore — 절대 커밋 금지):
    {
      "api_key": "sk_...",            # 일레븐랩스 프로필 → API Keys
      "voice_id": "...",              # 차노 목소리 클론의 voice ID (Voices → 해당 보이스 → ID)
      "model_id": "eleven_multilingual_v2",   # 생략 가능 (한국어 지원 기본값)
      "speed": 1.1                    # 생략 가능 (본진 규약 1.1배속)
    }
"""

from __future__ import annotations

import json
import subprocess
import urllib.request
from pathlib import Path

API_BASE = "https://api.elevenlabs.io/v1"
DEFAULT_MODEL = "eleven_multilingual_v2"
# 코드방 마인드 쇼츠 정본 = 1.05 (2026-07-17 이찬호 승인 목소리. 1.1=경박·1.0=느림 사이).
# 본진 CreatorOS는 1.1이 별도 정본 — 방마다 섞지 말 것. secrets에 speed 없어도 이 기본이 나온다.
DEFAULT_SPEED = 1.05

# 차노 클론 나레이션 기본값 (2026-07-18 이찬호 'B' 선택 — A/B 비교 후).
# stability 0.42·style 0.15 = 억양 살아있고 자연스러움. 쉼표 유지(라임 06). speed 1.05.
# 두 방 공통값. secrets의 "voice_settings"로 덮어쓸 수 있다.
DEFAULT_VOICE_SETTINGS = {
    "stability": 0.42,
    "similarity_boost": 0.85,
    "style": 0.15,
    "use_speaker_boost": True,
}


def load_credentials(path: str | Path) -> dict:
    """secrets/elevenlabs.json을 읽고 필수 필드를 검증한다."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"일레븐랩스 자격증명 없음: {p} — API 키와 voice_id 발급 필요")
    creds = json.loads(p.read_text(encoding="utf-8"))
    missing = {"api_key", "voice_id"} - creds.keys()
    if missing:
        raise ValueError(f"secrets/elevenlabs.json 누락 필드: {sorted(missing)}")
    creds.setdefault("model_id", DEFAULT_MODEL)
    creds.setdefault("speed", DEFAULT_SPEED)
    creds["voice_settings"] = {**DEFAULT_VOICE_SETTINGS, **creds.get("voice_settings", {})}
    return creds


def build_request(
    text: str,
    api_key: str,
    voice_id: str,
    model_id: str = DEFAULT_MODEL,
    previous_text: str | None = None,
    next_text: str | None = None,
    voice_settings: dict | None = None,
) -> urllib.request.Request:
    """TTS 합성 HTTP 요청을 만든다 (전송은 synthesize가 한다 — 테스트 분리용).

    previous_text/next_text를 주면 일레븐랩스가 앞뒤 문맥을 알고 합성해서
    줄별 합성이어도 억양이 한 호흡으로 이어진다 (줄마다 '새 문장 시작' 톤 방지).
    """
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": voice_settings or dict(DEFAULT_VOICE_SETTINGS),
    }
    if previous_text:
        payload["previous_text"] = previous_text
    if next_text:
        payload["next_text"] = next_text
    body = json.dumps(payload).encode("utf-8")
    return urllib.request.Request(
        f"{API_BASE}/text-to-speech/{voice_id}?output_format=mp3_44100_128",
        data=body,
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        method="POST",
    )


def synthesize(
    text: str,
    creds: dict,
    out_path: str | Path,
    timeout: int = 60,
    previous_text: str | None = None,
    next_text: str | None = None,
) -> Path:
    """한 줄을 mp3로 합성해 out_path에 저장한다."""
    req = build_request(
        text, creds["api_key"], creds["voice_id"], creds["model_id"],
        previous_text=previous_text, next_text=next_text,
        voice_settings=creds.get("voice_settings"),
    )
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        out.write_bytes(r.read())
    return out


def narration_filter(clips: list[tuple[str, float]], speed: float = DEFAULT_SPEED) -> str:
    """줄별 mp3를 배속·지연 배치해 하나로 섞는 ffmpeg filter_complex 문자열.

    clips: [(파일경로, 시작초), ...] — 입력 인덱스는 리스트 순서와 동일하다고 가정.
    클립 양끝 20ms 페이드로 경계의 '뚝' 소리(클릭 노이즈)를 없앤다.
    """
    declick = "afade=t=in:st=0:d=0.02,areverse,afade=t=in:st=0:d=0.02,areverse"
    parts = []
    labels = []
    for i, (_path, start) in enumerate(clips):
        delay = int(round(start * 1000))
        parts.append(f"[{i}:a]atempo={speed},{declick},adelay={delay}|{delay}[n{i}]")
        labels.append(f"[n{i}]")
    parts.append(f"{''.join(labels)}amix=inputs={len(clips)}:normalize=0:duration=longest[nar]")
    return ";".join(parts)


def probe_duration(path: str | Path) -> float:
    """mp3 클립 길이(초)를 ffprobe로 읽는다."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    return float(out)


def schedule_starts(
    starts: list[float],
    durations: list[float],
    speed: float = DEFAULT_SPEED,
    min_gap: float = 0.12,
) -> list[float]:
    """자막 시작 시각을 존중하되, 앞 줄 나레이션이 끝나기 전에 다음 줄이 겹치지 않게 민다.

    durations는 배속 전 원본 클립 길이 — 실제 점유 시간은 duration/speed.
    겹치면 목소리가 이중으로 들리고, 그게 '뚝뚝 끊기는' 느낌의 주범 중 하나다.
    """
    scheduled: list[float] = []
    prev_end = 0.0
    for start, dur in zip(starts, durations):
        s = start if not scheduled else max(start, prev_end + min_gap)
        scheduled.append(s)
        prev_end = s + dur / speed
    return scheduled


def synthesize_full_with_timestamps(text: str, creds: dict, timeout: int = 300) -> dict:
    """대본 전체를 한 번에 합성하고 글자 단위 타임스탬프를 받는다.

    한 요청 = 한 호흡 — 줄별 합성의 경계 끊김이 원천적으로 없다.
    응답: {"audio_base64": ..., "alignment": {"characters": [...],
           "character_start_times_seconds": [...], "character_end_times_seconds": [...]}}
    """
    body = json.dumps({
        "text": text,
        "model_id": creds["model_id"],
        "voice_settings": creds.get("voice_settings") or dict(DEFAULT_VOICE_SETTINGS),
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}/text-to-speech/{creds['voice_id']}/with-timestamps?output_format=mp3_44100_128",
        data=body,
        headers={"xi-api-key": creds["api_key"], "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def align_line_spans(
    texts: list[str],
    characters: list[str],
    char_starts: list[float],
    char_ends: list[float],
    speed: float = DEFAULT_SPEED,
) -> list[tuple[float, float]]:
    """글자 타임스탬프에서 줄별 (시작, 끝) 초를 뽑는다 (배속 반영).

    자막이 목소리와 정확히 같이 넘어가게 하는 심장부 — 늘어지는 간격이 없어진다.
    """
    joined = "".join(characters)
    spans: list[tuple[float, float]] = []
    pos = 0
    for t in texts:
        b = joined.index(t, pos)
        e = b + len(t)
        pos = e
        spans.append((char_starts[b] / speed, char_ends[e - 1] / speed))
    return spans


# 무음을 품는 글자 — 공백/문장부호. 일레븐랩스는 쉼을 '이 글자의 긴 지속시간'으로 인코딩한다
# (글자 사이 gap이 아님 — 실측 확인). 말소리 음절은 절대 자르지 않는다.
PAUSE_CHARS = set(" \t\n,.…·!?　")


def plan_gap_cuts(
    characters: list[str],
    char_starts: list[float],
    char_ends: list[float],
    keep: float = 0.14,
    threshold: float = 0.30,
) -> list[tuple[float, float]]:
    """늘어진 무음을 keep초만 남기고 잘라낼 (시작,끝) 구간 목록 (배속 전 raw 초).

    ①공백/문장부호 글자의 긴 지속시간(진짜 원인) ②글자 사이 gap — 둘 다 대상.
    말소리 음절(공백·부호가 아닌 글자)은 건드리지 않아 목소리가 깎이지 않는다.
    """
    cuts: list[tuple[float, float]] = []
    for i, c in enumerate(characters):
        # ① 무음 글자의 긴 지속시간
        if c in PAUSE_CHARS:
            dur = char_ends[i] - char_starts[i]
            if dur > threshold:
                cs = char_starts[i] + keep
                ce = char_ends[i]
                if ce > cs + 0.02:
                    cuts.append((cs, ce))
        # ② 글자 사이 빈 공백(gap)
        if i + 1 < len(characters):
            gap = char_starts[i + 1] - char_ends[i]
            if gap > threshold:
                cs = char_ends[i] + keep
                ce = char_starts[i + 1]
                if ce > cs + 0.02:
                    cuts.append((cs, ce))
    cuts.sort()
    return cuts


def _remap_time(t: float, cuts: list[tuple[float, float]]) -> float:
    """잘라낸 구간을 반영해 raw 시각 t를 압축 후 시각으로 옮긴다."""
    removed = 0.0
    for cs, ce in cuts:
        if t >= ce:
            removed += ce - cs
        elif t > cs:
            removed += t - cs
            break
        else:
            break
    return t - removed


def _compress_and_tempo(raw: Path, out: Path, cuts: list[tuple[float, float]], speed: float) -> None:
    """raw mp3에서 cuts 구간을 제거하고 atempo 적용 → out(m4a). cuts 없으면 배속만."""
    if not cuts:
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(raw),
            "-af", f"atempo={speed}", "-c:a", "aac", "-b:a", "192k", str(out),
        ], check=True)
        return
    keeps: list[tuple[float, float | None]] = []
    prev = 0.0
    for cs, ce in cuts:
        keeps.append((prev, cs))
        prev = ce
    keeps.append((prev, None))
    parts = []
    for idx, (a, b) in enumerate(keeps):
        trim = f"atrim=start={a:.3f}" + (f":end={b:.3f}" if b is not None else "")
        parts.append(f"[0:a]{trim},asetpts=PTS-STARTPTS[k{idx}]")
    cat_in = "".join(f"[k{idx}]" for idx in range(len(keeps)))
    parts.append(f"{cat_in}concat=n={len(keeps)}:v=0:a=1[cat]")
    parts.append(f"[cat]atempo={speed}[out]")
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(raw),
        "-filter_complex", ";".join(parts), "-map", "[out]",
        "-c:a", "aac", "-b:a", "192k", str(out),
    ], check=True)


def _assemble_lines_even(
    raw: Path, out: Path, raw_spans: list[tuple[float, float]],
    speed: float, line_gap: float = 0.18, pad: float = 0.03,
) -> None:
    """줄별 speech 구간을 잘라 각 줄 뒤에 line_gap 무음을 붙여 concat → atempo → out.

    모든 줄 사이 간격이 line_gap으로 균일해진다 (띄어쓰기 일정).
    """
    parts, labels = [], []
    for i, (s, e) in enumerate(raw_spans):
        a = max(0.0, s - pad)
        b = e + pad
        parts.append(
            f"[0:a]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS,"
            f"apad=pad_dur={line_gap:.3f}[L{i}]"
        )
        labels.append(f"[L{i}]")
    parts.append(f"{''.join(labels)}concat=n={len(raw_spans)}:v=0:a=1[cat]")
    parts.append(f"[cat]atempo={speed}[out]")
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(raw),
        "-filter_complex", ";".join(parts), "-map", "[out]",
        "-c:a", "aac", "-b:a", "192k", str(out),
    ], check=True)


# ── 발음 교정 사전 (합성 텍스트에만 적용, 자막 표시는 원문) ──────────────
# 일레븐랩스가 틀리게 읽는 단어를 '소리 나는 대로' 다시 적어 교정한다. 실측(STT)으로 확인된 것만.
# 형님이 오독을 지적하면 여기 한 줄 추가 = 이후 모든 영상에 자동 적용 (다시는 같은 실수 X).
SYNTH_FIXES: dict[str, str] = {
    "숱치": "숟치",        # 숱치기 → '수치기' 오독 방지 (경음/오독)
    "숱을 쳐": "숟을 쳐",
    "짓이겨진": "짓니겨진",  # '지시겨진' 오독 방지 (연음/오독) — 이찬호 2026-07-20 지적
    "읽나": "잉나",          # 읽나요 = [잉나요]. 받침 ㄺ+ㄴ → 일레븐랩스 헛읽음 — 이찬호 2026-07-20 지적
    "읽는": "잉는",          # 읽는 = [잉는] (같은 ㄺ+ㄴ 자리)
    "읽어": "일거",          # 읽어야죠 = [일거야죠] (받침 ㄺ 연음) — 같은 읽 어근 오독 방지
    "잔곱슬": "잔꼽쓸",      # 잔곱슬 = EL이 [장홉슬] → 꼽(ㄲ)+쓸(ㅆ)로 강제. 꼽슬론 부족(이찬호 2026-07-22 재지적)
    "곱슬": "꼽쓸",          # 곱슬 단독도 꼽쓸(ㄲ+ㅆ)로 강화
    "거림이었": "거리미었",  # 찰랑거림이었 = 림+이 연음을 EL이 끊어 어색 → 소리대로 '거리미어쓰' (이찬호 2026-07-22)
    "드러낼 뿐": "드러낼뿐",  # '드러낼 뿐' 사이 쉼이 너무 김 → 공백 제거해 붙여읽기(이찬호 2026-07-22)
    "단발은": "단바른",      # 단발은 = [단바른] 연음을 EL이 끊어 어색 → 소리대로 (이찬호 2026-07-22)
}

# ── 문장부호별 강제 쉼(초, 배속 전) ──────────────────────────────────
# 대본 부호가 '어디서' 쉴지를 정하고, 코드가 '얼마나' 쉴지를 보장한다.
# (일레븐랩스가 마침표에서 안 쉬어도 코드가 최소 쉼을 넣어 '바로 붙여읽기'를 막는다.)
PUNCT_TARGET: dict[str, float] = {".": 0.40, "?": 0.42, "!": 0.42, "…": 0.34, ",": 0.16}


def apply_synth_fixes(text: str) -> str:
    for a, b in SYNTH_FIXES.items():
        text = text.replace(a, b)
    return text


def collect_pause_edits(
    characters: list[str], char_starts: list[float], char_ends: list[float],
    targets: dict[str, float], head_grace: float = 1.2, max_gap: float = 0.30,
) -> list[tuple[float, float, float]]:
    """무음 구간 [rs, re]을 목표 길이로 바꿀 편집 목록 (배속 전 raw 초).

    두 가지를 한다:
      1) 문장부호 뒤 무음 → 목표 길이 tgt로 (마침표 0.40 등). '어디서 얼마나' 쉴지 보장.
      2) 부호 없는 자리의 자연 무음이 max_gap보다 길면 → max_gap으로 잘라 '촘촘'하게.
         (일레븐랩스가 줄 사이에 제멋대로 벌리는 긴 공백을 없앤다 — 2026-07-20 이찬호
         "미용실에선 예뻤는데 / 작심삼일 할 걸 알면 너무 띄어쓰기 길다" 지적. 부호 리듬은
         유지하되 나머지 벌어짐만 촘촘히.)

    head_grace: 오디오 시작 이 시간(초) 이내 무음은 손대지 않는다(첫 마디 워밍업 보호).
    max_gap: 부호 없는 무음의 상한(초). 0이면 부호 없는 자리는 손대지 않음(구동작).
    """
    n = len(characters)
    ws = " \t\n　"
    edits: list[tuple[float, float, float]] = []
    i = 0
    while i < n:
        if characters[i] in targets or characters[i] in ws:
            run_start = i
            tgt = 0.0
            while i < n and (characters[i] in targets or characters[i] in ws):
                if characters[i] in targets:
                    tgt = max(tgt, targets[characters[i]])
                i += 1
            if run_start > 0 and i < n:
                rs, re = char_ends[run_start - 1], char_starts[i]
                if re > rs and rs >= head_grace:  # 시작부는 자연 흐름에 맡김
                    if tgt > 0:
                        edits.append((rs, re, tgt))                    # 부호 → 목표 쉼
                    elif max_gap > 0 and (re - rs) > max_gap:
                        edits.append((rs, re, max_gap))                # 부호 없는 긴 무음 → 촘촘히 컷
        else:
            i += 1
    return edits


def _remap_pause(t: float, edits: list[tuple[float, float, float]]) -> float:
    delta = 0.0
    for rs, re, tgt in edits:
        if t >= re:
            delta += tgt - (re - rs)
    return t + delta


def _apply_pause_edits(raw: Path, out: Path, edits: list[tuple[float, float, float]], speed: float) -> None:
    """무음 구간을 목표 길이로 치환(concat)하고 atempo → out. 편집 없으면 배속만."""
    if not edits:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw),
                        "-af", f"atempo={speed}", "-c:a", "aac", "-b:a", "192k", str(out)], check=True)
        return
    parts, labels, pos = [], [], 0.0
    for idx, (rs, re, tgt) in enumerate(edits):
        parts.append(f"[0:a]atrim=start={pos:.3f}:end={rs:.3f},asetpts=PTS-STARTPTS,apad=pad_dur={tgt:.3f}[s{idx}]")
        labels.append(f"[s{idx}]")
        pos = re
    parts.append(f"[0:a]atrim=start={pos:.3f},asetpts=PTS-STARTPTS[s{len(edits)}]")
    labels.append(f"[s{len(edits)}]")
    parts.append(f"{''.join(labels)}concat=n={len(labels)}:v=0:a=1[cat]")
    parts.append(f"[cat]atempo={speed}[out]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw),
                    "-filter_complex", ";".join(parts), "-map", "[out]",
                    "-c:a", "aac", "-b:a", "192k", str(out)], check=True)


def build_narration_single(
    lines,
    creds: dict,
    workdir: str | Path,
    out_path: str | Path,
) -> tuple[Path, list[tuple[float, float]]]:
    """전체 대본 단일 합성 → (나레이션 m4a 경로, 줄별 실측 타이밍) 반환.

    합성 후 줄 사이 긴 무음을 잘라 '뚝뚝 끊김'을 없애고, 자막 타이밍을 압축된
    오디오에 맞춰 다시 계산한다. 같은 대본+보이스 설정은 캐시를 재사용한다.
    """
    import base64
    import hashlib as _hashlib

    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    lines = list(lines)
    texts = [line.text for line in lines]
    # 대본 부호가 '어디서' 쉴지를, 코드가 '얼마나' 쉴지를 정한다 (prompts/06 라임 규약).
    #   마침표=내려읽고 쉼 · 쉼표=살짝 · 부호없음=붙여 흐름. 코드가 최소 쉼을 보장(강제).
    # 합성 텍스트엔 발음 교정(SYNTH_FIXES)만 적용 — 자막 표시는 원문 그대로.
    syn_texts = [apply_synth_fixes(t) for t in texts]
    full = " ".join(syn_texts)
    speed = float(creds.get("speed", DEFAULT_SPEED))
    targets = creds.get("punct_targets", PUNCT_TARGET)

    voice_key = json.dumps(
        [creds.get("voice_id"), creds.get("model_id"), creds.get("voice_settings")],
        ensure_ascii=False, sort_keys=True,
    )
    key = _hashlib.md5((voice_key + "|single|" + full).encode("utf-8")).hexdigest()[:10]
    raw = workdir / f"nar_full_{key}.mp3"
    meta = workdir / f"nar_full_{key}.json"

    if raw.exists() and meta.exists():
        resp_align = json.loads(meta.read_text(encoding="utf-8"))
    else:
        resp = synthesize_full_with_timestamps(full, creds)
        raw.write_bytes(base64.b64decode(resp["audio_base64"]))
        resp_align = resp["alignment"]
        meta.write_text(json.dumps(resp_align, ensure_ascii=False), encoding="utf-8")

    chars = resp_align["characters"]
    cstart = resp_align["character_start_times_seconds"]
    cend = resp_align["character_end_times_seconds"]

    # 문장부호 쉼 강제: 마침표 등 뒤 무음을 목표 길이로 치환 (일레븐랩스가 안 쉬어도 코드가 보장).
    edits = collect_pause_edits(chars, cstart, cend, targets)
    out = Path(out_path)
    _apply_pause_edits(raw, out, edits, speed)

    # 자막 타이밍: 편집 반영해 줄별 (시작,끝) 재계산 (배속 반영). 정렬은 합성 텍스트 기준.
    joined = "".join(chars)
    spans: list[tuple[float, float]] = []
    pos = 0
    for t in syn_texts:
        b = joined.index(t, pos)
        e = b + len(t)
        pos = e
        s_f = _remap_pause(cstart[b], edits) / speed
        e_f = _remap_pause(cend[e - 1], edits) / speed
        spans.append((round(s_f, 3), round(e_f, 3)))
    return out, spans


def build_narration(
    lines,
    creds: dict,
    workdir: str | Path,
    out_path: str | Path,
) -> Path:
    """대본 줄들(start·text 필드 필요)을 합성해 자막 타이밍에 배치한 나레이션 트랙(m4a)을 만든다."""
    import hashlib as _hashlib

    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    lines = list(lines)
    texts = [line.text for line in lines]
    voice_key = json.dumps(
        [creds.get("voice_id"), creds.get("model_id"), creds.get("voice_settings")],
        ensure_ascii=False, sort_keys=True,
    )
    paths: list[str] = []
    for i, line in enumerate(lines):
        # 같은 문장+같은 보이스 설정이면 재합성하지 않는다 (재렌더 반복 시 비용·시간 절약)
        key = _hashlib.md5((voice_key + "|" + "|".join(texts) + f"|{i}").encode("utf-8")).hexdigest()[:10]
        clip_path = workdir / f"tts_{i:02d}_{key}.mp3"
        if clip_path.exists() and clip_path.stat().st_size > 0:
            paths.append(str(clip_path))
            continue
        clip = synthesize(
            line.text, creds, clip_path,
            previous_text=" ".join(texts[:i]) or None,
            next_text=" ".join(texts[i + 1:]) or None,
        )
        paths.append(str(clip))

    starts = schedule_starts(
        [line.start for line in lines],
        [probe_duration(p) for p in paths],
        float(creds.get("speed", DEFAULT_SPEED)),
    )
    clips = list(zip(paths, starts))

    out = Path(out_path)
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for path, _start in clips:
        cmd += ["-i", path]
    cmd += [
        "-filter_complex", narration_filter(clips, float(creds.get("speed", DEFAULT_SPEED))),
        "-map", "[nar]", "-c:a", "aac", "-b:a", "192k", str(out),
    ]
    subprocess.run(cmd, check=True)
    return out
