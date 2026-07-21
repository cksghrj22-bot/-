"""드라이브 공개링크 견고 다운로드 — 렌더용 B롤 바이트를 토큰 없이 안정적으로 받는다.

배경(2026-07-21 박제): 공개(anyone-with-link) 공유 파일은 토큰 없이 HTTPS로 받힌다.
그런데 그동안 ad-hoc curl로 받다가 카탈로그에 '0바이트·892K 잘림' 실패가 반복 기록됐다
(= 양동이 나르다 샌 곳). 원인 두 가지를 코드로 막는다:
  1) 대용량(대략 100MB+)은 구글 바이러스검사 인터스티셜(HTML)을 한 번 돌려준다 → confirm 토큰 필요.
  2) 네트워크 끊김 → 잘린 파일. 크기 검증 + 지수백오프 재시도로 막는다.

핵심 규약:
  - '앱이 만든 파일'만 보는 gdrive.py(drive.file) 토큰은 여기서 안 쓴다. 순수 공개링크.
  - 성공 판정: (a) 응답이 HTML 아님 (b) 받은 크기가 기대 크기와 일치(주면) 또는 최소 임계 이상.
사용:
    python3 -m shorts.drive_download <file_id> <dest_path> [--expected-size N]
"""
from __future__ import annotations

import http.cookiejar
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

USERCONTENT = "https://drive.usercontent.google.com/download"
LEGACY_UC = "https://drive.google.com/uc"
# 이보다 작은데 text/html이면 인터스티셜(진짜 영상 아님)로 본다.
HTML_SNIFF_BYTES = 2048
MIN_VIDEO_BYTES = 10_000  # 이보다 작으면 실패로 간주(빈/에러 응답)


def _looks_like_html(head: bytes) -> bool:
    low = head[:HTML_SNIFF_BYTES].lstrip().lower()
    return low.startswith(b"<!doctype html") or low.startswith(b"<html") or b"<title>google drive" in low


def _parse_confirm_token(html: bytes) -> dict[str, str]:
    """인터스티셜 HTML에서 확인 폼의 숨은 필드(confirm, uuid 등)를 뽑는다."""
    import re
    text = html.decode("utf-8", "replace")
    params: dict[str, str] = {}
    # <input type="hidden" name="confirm" value="t"> 형태 + download-form의 action 쿼리
    for name, value in re.findall(r'name="([^"]+)"\s+value="([^"]*)"', text):
        if name in ("confirm", "uuid", "id", "export", "at"):
            params[name] = value
    m = re.search(r'href="(/uc\?export=download[^"]+)"', text)
    if m and "confirm" not in params:
        q = urllib.parse.parse_qs(urllib.parse.urlparse(m.group(1).replace("&amp;", "&")).query)
        for k in ("confirm", "uuid"):
            if k in q:
                params[k] = q[k][0]
    return params


def _opener() -> urllib.request.OpenerDirector:
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def _fetch(opener, url: str, timeout: int = 1800) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (pipeline)"})
    with opener.open(req, timeout=timeout) as r:
        return r.read(), r.headers.get("Content-Type", "")


def download(file_id: str, dest: str | Path, *, expected_size: int | None = None,
             max_retries: int = 4) -> dict:
    """공개 file_id를 dest로 받는다. confirm 인터스티셜·끊김을 자동 처리.

    반환: {"path": str, "bytes": int, "attempts": int}. 실패 시 RuntimeError.
    """
    dest = Path(dest)
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            opener = _opener()
            # 1차: 모던 usercontent + confirm=t (대용량도 대부분 이걸로 바로 받힘)
            url = f"{USERCONTENT}?{urllib.parse.urlencode({'id': file_id, 'export': 'download', 'confirm': 't'})}"
            data, ctype = _fetch(opener, url)
            # 인터스티셜이면 토큰 뽑아 재요청
            if _looks_like_html(data) or ctype.startswith("text/html"):
                params = _parse_confirm_token(data)
                params.setdefault("id", file_id)
                params.setdefault("export", "download")
                params.setdefault("confirm", "t")
                data, ctype = _fetch(opener, f"{USERCONTENT}?{urllib.parse.urlencode(params)}")
                if _looks_like_html(data) or ctype.startswith("text/html"):
                    # 레거시 엔드포인트 마지막 시도
                    data, ctype = _fetch(opener, f"{LEGACY_UC}?{urllib.parse.urlencode(params)}")
            # 검증
            if _looks_like_html(data) or ctype.startswith("text/html"):
                raise RuntimeError("인터스티셜 HTML만 돌아옴(공유설정 anyone-with-link 확인 필요)")
            if len(data) < MIN_VIDEO_BYTES:
                raise RuntimeError(f"응답이 너무 작음({len(data)}바이트) — 잘림/에러 의심")
            if expected_size and abs(len(data) - expected_size) > max(1024, expected_size * 0.01):
                raise RuntimeError(f"크기 불일치: 받음 {len(data)} vs 기대 {expected_size} — 잘림 의심")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            return {"path": str(dest), "bytes": len(data), "attempts": attempt}
        except Exception as e:  # noqa: BLE001 — 네트워크/파싱 모두 재시도 대상
            last_err = e
            if attempt < max_retries:
                time.sleep(2 ** attempt)  # 2,4,8초 지수백오프
    raise RuntimeError(f"다운로드 실패({max_retries}회): {file_id} — {last_err!r}")


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="드라이브 공개링크 견고 다운로드")
    ap.add_argument("file_id")
    ap.add_argument("dest")
    ap.add_argument("--expected-size", type=int, default=None)
    ap.add_argument("--max-retries", type=int, default=4)
    args = ap.parse_args(argv)
    try:
        info = download(args.file_id, args.dest, expected_size=args.expected_size,
                        max_retries=args.max_retries)
        print(f"✅ 다운로드 완료: {info['path']} ({info['bytes']:,}바이트, {info['attempts']}회 시도)")
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"❌ {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
