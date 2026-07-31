"""드라이브 대용량 영상 = 통다운 없이 '스트리밍 부분추출' — 영구 박제(2026-07-28 이찬호 지시).

배경(재발방지):
  형이 인트레이에 올리는 원본(4K·1.8GB+)을 통째로 받으려다 **디스크 풀 + moov-at-end**
  (부분 head 다운로드는 디코드 불가)로 매번 막혔다. 무마식 해결 말고 전략으로 못박는다:
  ffmpeg가 **인증된 Drive media URL을 직접 읽어**(HTTP Range) 필요한 구간만 잘라낸다.
  → 1.8GB를 디스크에 안 올린다 = 용량·moov 문제 동시 소멸.

인증:
  gdrive.py가 쓰는 secrets/gdrive.json(refresh_token, drive.file 스코프)로 access_token을 즉석 발급.
  이 스코프는 '앱이 만든/올린 파일'만 보이므로, 코드방이 gdrive.py로 올린 인트레이 원본에 동작한다.
  (순수 공개링크 파일은 shorts/drive_download.py를 쓴다 — 역할 분리.)

쓰는 법(CLI):
    python3 -m shorts.drive_stream probe   <file_id>
    python3 -m shorts.drive_stream sheet   <file_id> --times 8,25,45,... -o sheet.jpg [--width 360]
    python3 -m shorts.drive_stream extract <file_id> --ss 84 --t 22 -o clip.mp4 \
            [--vf "hflip,crop=ih*4/5:ih,scale=1080:1350,pad=1080:1920:0:285:black,fps=30"] [--crf 20]

함수 API:
    from shorts import drive_stream as DS
    url, hdr = DS.authorized_source(file_id)      # ffmpeg -headers 로 넘길 (url, header문자열)
    DS.extract(file_id, ss=84, t=22, out="clip.mp4", vf=VF)
"""
from __future__ import annotations

import json
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_SECRETS = Path(__file__).resolve().parent.parent / "secrets" / "gdrive.json"
TOKEN_URL = "https://oauth2.googleapis.com/token"
MEDIA_URL = "https://www.googleapis.com/drive/v3/files/{fid}?alt=media"
META_URL = "https://www.googleapis.com/drive/v3/files/{fid}"

# 스펙 기본 프레이밍: 좌우반전 보정 없음. 4:5 확대크롭 + 상하 검정밴드(캔버스 1080x1920).
SPEC_VF = "crop=ih*4/5:ih,scale=1080:1350,pad=1080:1920:0:285:black,fps=30"


def access_token(secrets: str | Path = DEFAULT_SECRETS) -> str:
    """refresh_token으로 짧은 수명의 access_token을 즉석 발급."""
    s = json.loads(Path(secrets).read_text())
    for k in ("client_id", "client_secret", "refresh_token"):
        if not s.get(k):
            raise RuntimeError(f"secrets/gdrive.json 에 {k} 없음 — gdrive.py auth 먼저")
    data = urllib.parse.urlencode({
        "client_id": s["client_id"], "client_secret": s["client_secret"],
        "refresh_token": s["refresh_token"], "grant_type": "refresh_token",
    }).encode()
    with urllib.request.urlopen(TOKEN_URL, data=data, timeout=30) as r:
        return json.load(r)["access_token"]


def authorized_source(file_id: str, tok: str | None = None) -> tuple[str, str]:
    """ffmpeg/ffprobe에 넘길 (media_url, headers) 쌍. headers는 CRLF로 끝나는 Authorization 한 줄."""
    tok = tok or access_token()
    return MEDIA_URL.format(fid=file_id), f"Authorization: Bearer {tok}\r\n"


def metadata(file_id: str, tok: str | None = None) -> dict:
    tok = tok or access_token()
    url = META_URL.format(fid=file_id) + "?fields=name,size,mimeType,createdTime,videoMediaMetadata"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def probe(file_id: str, tok: str | None = None) -> dict:
    """스트리밍 ffprobe — duration(초)·width·height·size."""
    url, hdr = authorized_source(file_id, tok)
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-headers", hdr,
         "-show_entries", "format=duration,size:stream=width,height,codec_type",
         "-of", "json", url],
        capture_output=True, text=True, timeout=180,
    )
    if out.returncode != 0:
        raise RuntimeError(f"ffprobe 실패: {out.stderr.strip()[:400]}")
    j = json.loads(out.stdout)
    vs = next((s for s in j.get("streams", []) if s.get("codec_type") == "video"), {})
    fmt = j.get("format", {})
    return {"duration": float(fmt.get("duration", 0)), "size": int(fmt.get("size", 0)),
            "width": vs.get("width"), "height": vs.get("height")}


def extract(file_id: str, ss: float, t: float, out: str | Path,
            vf: str | None = SPEC_VF, crf: int = 20, tok: str | None = None,
            with_audio: bool = False) -> Path:
    """[ss, ss+t] 구간만 스트리밍으로 잘라 out에 저장(통다운 없음). vf=None이면 원본 프레이밍."""
    import time as _time
    out = Path(out)
    _tok = tok
    _cache = Path("/tmp/vid_cache") / f"{file_id}.mp4"   # 원본 로컬 캐시 우선(Drive throttle 회피)
    for _att in range(6):                # Drive rate throttle(403) 대비 재시도 + 토큰 갱신
        if _cache.is_file():
            _src, _hdrs = str(_cache), None
        else:
            url, hdr = authorized_source(file_id, _tok); _src, _hdrs = url, hdr
        cmd = ["ffmpeg", "-v", "error"] + (["-headers", _hdrs] if _hdrs else []) + ["-ss", str(ss), "-i", _src, "-t", str(t)]
        if vf:
            cmd += ["-vf", vf]
        cmd += (["-c:a", "aac", "-b:a", "128k"] if with_audio else ["-an"])
        cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", str(crf), str(out), "-y"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
        if r.returncode == 0:
            return out
        _e = r.stderr
        if any(s in _e for s in ("403", "Forbidden", "Invalid data", "truncat", "Server returned", "timed out", "reset")):
            _time.sleep(5 * (_att + 1)); _tok = access_token(); continue   # quota/rate/잘린 응답 → 재시도
        break
    raise RuntimeError(f"extract 실패: {r.stderr.strip()[:400]}")


def frame(file_id: str, at: float, out: str | Path, width: int = 360,
          hflip: bool = False, tok: str | None = None) -> Path:
    """at초 지점 썸네일 1장(구간 탐색용)."""
    url, hdr = authorized_source(file_id, tok)
    vf = (("hflip," if hflip else "") + f"scale={width}:-1")
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-headers", hdr, "-ss", str(at), "-i", url,
         "-frames:v", "1", "-vf", vf, "-q:v", "5", str(out), "-y"],
        capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        raise RuntimeError(f"frame 실패: {r.stderr.strip()[:300]}")
    return Path(out)


def sheet(file_id: str, times: list[float], out: str | Path, width: int = 360,
          hflip: bool = False, tok: str | None = None) -> Path:
    """구간 탐색용 컨택트시트(내부적으로 각 시각 프레임 추출 후 PIL 타일). ImageMagick 불필요."""
    from PIL import Image, ImageDraw, ImageFont
    tok = tok or access_token()
    tmp = Path(out).parent / "_ds_sheet_tmp"
    tmp.mkdir(exist_ok=True)
    paths = []
    for tt in times:
        p = tmp / f"f_{int(tt):05d}.jpg"
        frame(file_id, tt, p, width=width, hflip=hflip, tok=tok)
        paths.append((tt, p))
    im0 = Image.open(paths[0][1]); w, h = im0.size
    cols = 4; rows = (len(paths) + cols - 1) // cols; pad = 6; lab = 24
    sheet_img = Image.new("RGB", (cols * w + (cols + 1) * pad, rows * (h + lab) + (rows + 1) * pad), (20, 20, 20))
    d = ImageDraw.Draw(sheet_img)
    try:
        fnt = ImageFont.truetype("/root/.fonts/nsqr_eb.ttf", 18)
    except Exception:
        fnt = ImageFont.load_default()
    for i, (tt, p) in enumerate(paths):
        r_, c_ = divmod(i, cols); x = pad + c_ * (w + pad); y = pad + r_ * (h + lab + pad)
        sheet_img.paste(Image.open(p), (x, y))
        d.text((x + 4, y + h + 2), f"{tt:g}s", font=fnt, fill=(255, 212, 0))
    sheet_img.save(out, quality=82)
    for _, p in paths:
        p.unlink(missing_ok=True)
    tmp.rmdir()
    return Path(out)


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="드라이브 대용량 영상 스트리밍 부분추출")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_pr = sub.add_parser("probe"); p_pr.add_argument("file_id")
    p_sh = sub.add_parser("sheet"); p_sh.add_argument("file_id")
    p_sh.add_argument("--times", required=True, help="쉼표구분 초 목록 예: 8,25,45")
    p_sh.add_argument("-o", "--out", required=True); p_sh.add_argument("--width", type=int, default=360)
    p_sh.add_argument("--hflip", action="store_true")
    p_ex = sub.add_parser("extract"); p_ex.add_argument("file_id")
    p_ex.add_argument("--ss", type=float, required=True); p_ex.add_argument("--t", type=float, required=True)
    p_ex.add_argument("-o", "--out", required=True); p_ex.add_argument("--vf", default=SPEC_VF)
    p_ex.add_argument("--crf", type=int, default=20); p_ex.add_argument("--audio", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "probe":
        print(json.dumps(probe(a.file_id), ensure_ascii=False, indent=2))
    elif a.cmd == "sheet":
        times = [float(x) for x in a.times.split(",")]
        print(sheet(a.file_id, times, a.out, width=a.width, hflip=a.hflip))
    elif a.cmd == "extract":
        vf = None if a.vf.lower() == "none" else a.vf
        print(extract(a.file_id, a.ss, a.t, a.out, vf=vf, crf=a.crf, with_audio=a.audio))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
