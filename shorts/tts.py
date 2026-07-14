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
    return creds


def build_request(text: str, api_key: str, voice_id: str, model_id: str = DEFAULT_MODEL) -> urllib.request.Request:
    """TTS 합성 HTTP 요청을 만든다 (전송은 synthesize가 한다 — 테스트 분리용)."""
    body = json.dumps(
        {
            "text": text,
            "model_id": model_id,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }
    ).encode("utf-8")
    return urllib.request.Request(
        f"{API_BASE}/text-to-speech/{voice_id}?output_format=mp3_44100_128",
        data=body,
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        method="POST",
    )


def synthesize(text: str, creds: dict, out_path: str | Path, timeout: int = 60) -> Path:
    """한 줄을 mp3로 합성해 out_path에 저장한다."""
    req = build_request(text, creds["api_key"], creds["voice_id"], creds["model_id"])
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        out.write_bytes(r.read())
    return out


def narration_filter(clips: list[tuple[str, float]], speed: float = DEFAULT_SPEED) -> str:
    """줄별 mp3를 배속·지연 배치해 하나로 섞는 ffmpeg filter_complex 문자열.

    clips: [(파일경로, 시작초), ...] — 입력 인덱스는 리스트 순서와 동일하다고 가정.
    """
    parts = []
    labels = []
    for i, (_path, start) in enumerate(clips):
        delay = int(round(start * 1000))
        parts.append(f"[{i}:a]atempo={speed},adelay={delay}|{delay}[n{i}]")
        labels.append(f"[n{i}]")
    parts.append(f"{''.join(labels)}amix=inputs={len(clips)}:normalize=0:duration=longest[nar]")
    return ";".join(parts)


def build_narration(
    lines,
    creds: dict,
    workdir: str | Path,
    out_path: str | Path,
) -> Path:
    """대본 줄들(start·text 필드 필요)을 합성해 자막 타이밍에 배치한 나레이션 트랙(m4a)을 만든다."""
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    clips: list[tuple[str, float]] = []
    for i, line in enumerate(lines):
        clip = synthesize(line.text, creds, workdir / f"tts_{i:02d}.mp3")
        clips.append((str(clip), line.start))

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
