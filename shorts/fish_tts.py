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

# 읽기 규약 공유: 일레븐랩스에 쌓아온 발음교정 사전을 피쉬에도 그대로 적용.
# (2026-07-24 이찬호 "읽기에 관한 지금까지의 일들을 다 피쉬에 학습시켜")
# 형님이 오독 지적 → shorts/tts.py의 SYNTH_FIXES 한 줄 추가 = 일레븐·피쉬 양쪽 자동 반영.
try:
    from shorts.tts import apply_synth_fixes
except Exception:
    def apply_synth_fixes(text):  # tts.py 임포트 실패 시 무보정(안전)
        return text

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
    payload["text"] = apply_synth_fixes(text)  # 발음교정(읽기 규약) 적용 — 자막 원문과 별개, 합성 텍스트만
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


def _mp3_dur(p) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout.strip()
    return float(out or 0.0)


def synth_to_file(text: str, creds: dict, out_path, max_retries: int = 3) -> Path:
    """text → mp3. ⚠️ 피쉬가 가끔 짧은 줄에서 길이 폭주(47초 등) → 예상 길이 초과 시 재합성.
    (2026-07-24 태도 숏 l01 47초 사고). 글자수 기반 상한: chars*0.32 + 3.5초."""
    out = Path(out_path)
    cap = len(text) * 0.32 + 3.5   # 관대한 상한(정상은 이 안)
    best = None; best_d = 1e9
    for _ in range(max_retries):
        data = synthesize(text, creds)
        out.write_bytes(data)
        d = _mp3_dur(out)
        if d <= cap:
            return out
        if d < best_d:  # 폭주 중 그나마 짧은 것 보관
            best_d = d; best = data
    if best is not None:
        out.write_bytes(best)  # 다 폭주면 가장 짧은 것
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
