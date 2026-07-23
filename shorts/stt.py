"""일레븐랩스 Scribe 음성전사 — 영상/오디오 → 단어 타임스탬프 JSON.

롱폼 편집에서 '원본에서 형이 한 말'을 그대로 살리려면, 먼저 발화를 전사해
말한 구간(단어 타임스탬프)을 알아야 한다. longform.build_ass가 쓰는 것과 같은
{"words":[{"type":"word","text","start","end"}...]} 포맷으로 저장한다.

사용:
    python3 -m shorts.stt 영상.mp4                 # → 영상.stt.json
    python3 -m shorts.stt a.mp4 b.mp4 --lang kor

secrets/elevenlabs.json 의 api_key 사용. 네트워크 필요.
"""
from __future__ import annotations
import json, subprocess, sys, urllib.request
from pathlib import Path

STT_URL = "https://api.elevenlabs.io/v1/speech-to-text"
DEFAULT_SECRETS = "secrets/elevenlabs.json"


def _api_key(secrets_path: str | Path = DEFAULT_SECRETS) -> str:
    creds = json.loads(Path(secrets_path).read_text(encoding="utf-8"))
    key = creds.get("api_key") or creds.get("xi_api_key") or creds.get("key")
    if not key:
        raise ValueError(f"{secrets_path} 에 api_key 없음")
    return key


def extract_audio(video: str | Path, out_mp3: str | Path, denoise: bool = True) -> Path:
    """영상에서 오디오만 뽑아 mp3(모노 16k)로. 전사 업로드 용량 절감.
    denoise=True(기본): 야외 360캠 바람소리 제거(highpass+afftdn+loudnorm) — 실측상 이거 없으면
    러닝 발화가 '[바람 소리]'로만 잡혀 0단어. 있으면 174단어 정상 전사(2026-07-23 실증)."""
    out_mp3 = Path(out_mp3)
    af = "highpass=f=150,afftdn=nf=-20,loudnorm" if denoise else None
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-vn"]
    if af:
        cmd += ["-af", af]
    cmd += ["-ac", "1", "-ar", "16000", "-b:a", "64k", str(out_mp3)]
    subprocess.run(cmd, check=True)
    return out_mp3


def _multipart(fields: dict, file_field: str, file_path: Path) -> tuple[bytes, str]:
    """간단 multipart/form-data 인코딩(외부 의존 없이)."""
    boundary = "----afcstt" + "boundaryX7"
    lines = []
    for k, v in fields.items():
        lines.append(f"--{boundary}".encode())
        lines.append(f'Content-Disposition: form-data; name="{k}"'.encode())
        lines.append(b"")
        lines.append(str(v).encode())
    data = file_path.read_bytes()
    lines.append(f"--{boundary}".encode())
    lines.append(f'Content-Disposition: form-data; name="{file_field}"; filename="{file_path.name}"'.encode())
    lines.append(b"Content-Type: audio/mpeg")
    lines.append(b"")
    lines.append(data)
    lines.append(f"--{boundary}--".encode())
    lines.append(b"")
    body = b"\r\n".join(lines)
    return body, boundary


def transcribe(audio: str | Path, api_key: str, language: str = "kor",
               model_id: str = "scribe_v1", timeout: int = 600) -> dict:
    """오디오 파일 → Scribe 응답(dict). words[].{text,start,end,type} 포함."""
    audio = Path(audio)
    body, boundary = _multipart(
        {"model_id": model_id, "language_code": language, "timestamps_granularity": "word"},
        "file", audio)
    req = urllib.request.Request(STT_URL, data=body, method="POST", headers={
        "xi-api-key": api_key,
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def to_words(resp: dict) -> list[dict]:
    """Scribe 응답을 longform 포맷 words 리스트로 정규화."""
    out = []
    for w in resp.get("words", []):
        if w.get("type") not in (None, "word"):
            # 공백/구두점 타입은 제외(단어만)
            if w.get("type") != "word":
                continue
        out.append({"type": "word", "text": w.get("text", ""),
                    "start": w.get("start", 0.0), "end": w.get("end", 0.0)})
    return out


def transcribe_video(video: str | Path, out_json: str | Path | None = None,
                     language: str = "kor", secrets_path: str | Path = DEFAULT_SECRETS) -> Path:
    """영상 → 오디오추출 → Scribe → {out}.stt.json 저장. 저장 경로 반환."""
    video = Path(video)
    out_json = Path(out_json) if out_json else video.with_suffix(".stt.json")
    tmp_mp3 = video.with_suffix(".stt.mp3")
    extract_audio(video, tmp_mp3)
    resp = transcribe(tmp_mp3, _api_key(secrets_path), language=language)
    words = to_words(resp)
    text = resp.get("text", " ".join(w["text"] for w in words))
    out_json.write_text(json.dumps({"text": text, "words": words}, ensure_ascii=False), encoding="utf-8")
    try:
        tmp_mp3.unlink()
    except OSError:
        pass
    return out_json


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="일레븐랩스 Scribe 전사 → .stt.json")
    ap.add_argument("videos", nargs="+")
    ap.add_argument("--lang", default="kor")
    ap.add_argument("--secrets", default=DEFAULT_SECRETS)
    args = ap.parse_args(argv)
    for v in args.videos:
        try:
            out = transcribe_video(v, language=args.lang, secrets_path=args.secrets)
            data = json.loads(Path(out).read_text(encoding="utf-8"))
            n = len(data["words"])
            dur = data["words"][-1]["end"] if data["words"] else 0
            print(f"✅ {v} → {out}  단어 {n}개 · 발화끝 {dur:.1f}s")
            print(f"   미리보기: {data['text'][:120]}")
        except Exception as e:
            print(f"⛔ {v} 전사 실패: {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
