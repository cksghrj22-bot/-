# Fish Audio TTS 연동 (일레븐랩스 대안). (2026-07-24 이찬호 "피쉬오디오 연동해")
# secrets/fish.json 예:
#   {
#     "api_key": "..."            ← fish.audio → API Keys
#     "reference_id": "..."       ← (선택) 플레이그라운드에서 만든 보이스 모델 ID. 없으면 기본 보이스.
#     "model": "s1",              ← (선택) s1 | speech-1.6 | speech-1.5. 기본 s1(최신)
#     "params": { ... }           ← (선택) temperature/top_p 등 덮어쓰기
#   }
# 키만 넣으면 즉시 가동. 절대 커밋 금지(secrets/ gitignore).
import json, sys, subprocess
import urllib.request
from pathlib import Path

TTS_URL = "https://api.fish.audio/v1/tts"
DEFAULT_MODEL = "s1"
DEFAULT_SECRETS = "/home/user/-/secrets/fish.json"
DEFAULT_PARAMS = {
    "format": "mp3",
    "mp3_bitrate": 128,
    "chunk_length": 200,
    "normalize": True,   # 문장부호 기반 정규화 (일레븐랩스 speechnorm 대응)
    "latency": "normal",
}


def load_credentials(path=DEFAULT_SECRETS) -> dict:
    creds = json.loads(Path(path).read_text(encoding="utf-8"))
    if "api_key" not in creds:
        raise KeyError("fish.json에 api_key 없음")
    creds["model"] = creds.get("model", DEFAULT_MODEL)
    creds["params"] = {**DEFAULT_PARAMS, **creds.get("params", {})}
    return creds


def build_request(text: str, creds: dict) -> urllib.request.Request:
    payload = dict(creds["params"])
    payload["text"] = text
    if creds.get("reference_id"):
        payload["reference_id"] = creds["reference_id"]
    body = json.dumps(payload).encode("utf-8")
    return urllib.request.Request(
        TTS_URL, data=body, method="POST",
        headers={
            "Authorization": f"Bearer {creds['api_key']}",
            "Content-Type": "application/json",
            "model": creds["model"],            # Fish는 모델을 헤더로 지정
            "User-Agent": "atnown-coderoom/1.0",
        },
    )


def synthesize(text: str, creds: dict, timeout: int = 120) -> bytes:
    """text → mp3 bytes."""
    req = build_request(text, creds)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def synth_to_file(text: str, creds: dict, out_path) -> Path:
    out = Path(out_path)
    out.write_bytes(synthesize(text, creds))
    return out


def build_narration_single(lines, creds, workdir, out_path):
    """render 파이프라인 호환: lines=[SimpleNamespace(text=...)...] → 줄별 합성 후 이어붙이고 spans 반환.
    반환: (out_path, spans[(start,end)...], total). tts.build_narration_single과 시그니처 호환."""
    workdir = Path(workdir); workdir.mkdir(parents=True, exist_ok=True)
    parts, spans, cursor = [], [], 0.0
    for i, ln in enumerate(lines):
        p = workdir / f"fish_{i:02d}.mp3"
        synth_to_file(ln.text, creds, p)
        d = _dur(p)
        spans.append((cursor, cursor + d)); cursor += d
        parts.append(p)
    # concat
    lst = workdir / "fish_concat.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts), encoding="utf-8")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0",
                    "-i", str(lst), "-c", "copy", str(out_path)], check=True)
    return Path(out_path), spans, cursor


def _dur(p) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout.strip()
    return float(out or 0.0)


if __name__ == "__main__":
    # 연동 테스트: python3 -m shorts.fish_tts "테스트 문장" [out.mp3]
    txt = sys.argv[1] if len(sys.argv) > 1 else "안녕하세요, 앳나운 차노쌤입니다. 피쉬오디오 연동 테스트입니다."
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/fish_test.mp3"
    try:
        creds = load_credentials()
    except FileNotFoundError:
        print("secrets/fish.json 없음 — fish.audio API 키를 넣어야 가동됩니다.")
        sys.exit(2)
    try:
        synth_to_file(txt, creds, out)
        print(f"OK 합성 완료 → {out} ({_dur(out):.2f}s, model={creds['model']})")
    except urllib.error.HTTPError as e:
        print(f"실패 HTTP {e.code}: {e.read().decode()[:300]}")
        sys.exit(1)
