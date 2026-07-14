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


def build_narration_single(
    lines,
    creds: dict,
    workdir: str | Path,
    out_path: str | Path,
) -> tuple[Path, list[tuple[float, float]]]:
    """전체 대본 단일 합성 → (나레이션 m4a 경로, 줄별 실측 타이밍) 반환.

    타이밍은 배속 적용 후 기준 — 자막을 이 값으로 다시 깔면 말과 완전 동기화된다.
    같은 대본+보이스 설정은 캐시를 재사용한다.
    """
    import base64
    import hashlib as _hashlib

    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    lines = list(lines)
    texts = [line.text for line in lines]
    full = "\n".join(texts)
    speed = float(creds.get("speed", DEFAULT_SPEED))

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

    spans = align_line_spans(
        texts, resp_align["characters"],
        resp_align["character_start_times_seconds"], resp_align["character_end_times_seconds"],
        speed,
    )
    out = Path(out_path)
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(raw),
        "-af", f"atempo={speed}", "-c:a", "aac", "-b:a", "192k", str(out),
    ], check=True)
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
