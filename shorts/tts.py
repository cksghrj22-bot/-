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
DEFAULT_SPEED = 1.1

# 차노 프로페셔널 클론(31분 원본, multilingual_v2 파인튜닝 완료) 기준 나레이션 기본값.
# stability를 낮추고 style을 살짝 줘서 '또박또박 읽는 톤' 대신 말하는 억양을 살린다.
# secrets/elevenlabs.json의 "voice_settings"로 편별·세션별 덮어쓸 수 있다.
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
    # 합성 텍스트 다듬기 (자막 표시는 원문 그대로, 합성 입력만):
    #  ① 줄 끝 쉼표 제거 → 이어지는 줄은 안 끊고 흐른다.
    #  ② 문장이 끝나는 줄(요/죠/다 등 종결어미)엔 마침표를 붙여 → 거기서만 쉰다.
    # 레퍼런스 패턴 = 문장 끝에만 쉼, 나머지는 흐름.
    align_texts = [t.rstrip(" ,，·") for t in texts]  # 정렬은 말소리 기준(부호 없이)
    _SENT_END = ("요", "죠", "다", "까", "네", "자", "라")
    syn_texts = [
        (a + "." if a and a[-1] in _SENT_END and not a.endswith((".", "?", "!", "…")) else a)
        for a in align_texts
    ]
    full = " ".join(syn_texts)
    speed = float(creds.get("speed", DEFAULT_SPEED))
    keep = float(creds.get("gap_keep", 0.14))
    threshold = float(creds.get("gap_threshold", 0.34))

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

    out = Path(out_path)
    # natural_flow: 오디오를 손대지 않고 그대로(배속만) — 일레븐랩스의 자연 흐름 유지.
    # 쉼은 대본 문장부호가 정한다 (레퍼런스처럼 문장 끝에만 쉬려면 대본을 문장으로 이어 쓴다).
    if creds.get("natural_flow"):
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(raw),
            "-af", f"atempo={speed}", "-c:a", "aac", "-b:a", "192k", str(out),
        ], check=True)
        spans = align_line_spans(
            align_texts, resp_align["characters"],
            resp_align["character_start_times_seconds"], resp_align["character_end_times_seconds"],
            speed,
        )
        return out, spans

    # (기본) 줄별 speech 구간을 뽑아 매 줄 사이에 line_gap을 강제 — 균일한 띄어쓰기.
    raw_spans = align_line_spans(
        align_texts, resp_align["characters"],
        resp_align["character_start_times_seconds"], resp_align["character_end_times_seconds"],
        speed=1.0,
    )
    line_gap = float(creds.get("line_gap", 0.18))
    pad = float(creds.get("line_pad", 0.03))
    _assemble_lines_even(raw, out, raw_spans, speed, line_gap=line_gap, pad=pad)
    spans: list[tuple[float, float]] = []
    cum = 0.0
    for s, e in raw_spans:
        a = max(0.0, s - pad)
        seg = (e + pad) - a
        start_f = cum / speed
        cum += seg + line_gap
        spans.append((round(start_f, 3), round(cum / speed, 3)))
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
