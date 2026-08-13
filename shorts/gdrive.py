"""구글드라이브 직접 업로드 — 기기 인증(Device Flow) + 대용량 업로드.

코드방(클라우드 세션)은 브라우저를 못 열기 때문에 기기 인증을 쓴다:
세션이 링크+코드를 출력 → 이찬호가 폰에서 링크 열고 코드 입력 + 허용 →
세션이 토큰을 받아 secrets/gdrive.json에 저장 → 이후 영상 직접 업로드.

secrets/gdrive.json 형식 (gitignore — 절대 커밋 금지):
    {
      "client_id": "....apps.googleusercontent.com",   # OAuth 클라이언트 (유형: TV 및 제한된 입력 장치)
      "client_secret": "...",
      "refresh_token": "..."                            # auth 명령이 채운다
    }

사용:
    python3 -m shorts.gdrive auth                      # 최초 1회 — 링크+코드 출력 후 승인 대기
    python3 -m shorts.gdrive upload 영상.mp4 --folder-id <드라이브폴더ID>

주의: 기기 인증이 허용하는 권한(drive.file)은 "이 앱이 만든 파일"만 접근한다.
기존 폴더에 넣지 못하면 자동으로 「코드방_업로드」 폴더를 만들어 그곳에 올린다.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

DEVICE_CODE_URL = "https://oauth2.googleapis.com/device/code"
TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable&supportsAllDrives=true"
FILES_URL = "https://www.googleapis.com/drive/v3/files"
# 기기 인증(device flow)이 허용하는 스코프 = drive.file(앱 생성분) + youtube.upload 뿐.
# ⚠️전체 drive/drive.readonly는 기기 인증에서 거부된다 → SCOPE는 device-safe로 고정(test로 잠금).
SCOPE = "https://www.googleapis.com/auth/drive.file https://www.googleapis.com/auth/youtube.upload"

# 인트레이(형님 폰 PhotoSync분) 열람용 = drive.readonly. 기기 인증 불가 → **브라우저 OAuth** 필요
# (2026-07-25 이찬호 "인트레이 파일 볼 수 있게 · oauth 달라"). 브라우저 OAuth로 아래 3스코프를 한 번에
# 발급받아 refresh_token을 secrets/gdrive.json에 넣으면 upload+읽기+youtube 다 된다. list_folder가 그때 동작.
SCOPE_FULL = ("https://www.googleapis.com/auth/drive.file "
              "https://www.googleapis.com/auth/drive.readonly "
              "https://www.googleapis.com/auth/youtube.upload")
DEFAULT_SECRETS = "secrets/gdrive.json"
FALLBACK_FOLDER_NAME = "코드방_업로드"


def load_secrets(path: str | Path = DEFAULT_SECRETS) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"드라이브 자격증명 없음: {p} — client_id/client_secret를 넣고 "
            f"`python3 -m shorts.gdrive auth` 실행"
        )
    creds = json.loads(p.read_text(encoding="utf-8"))
    missing = {"client_id", "client_secret"} - creds.keys()
    if missing:
        raise ValueError(f"{p} 누락 필드: {sorted(missing)}")
    return creds


def _post_form(url: str, data: dict, timeout: int = 30) -> dict:
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())


def device_code_request(client_id: str) -> dict:
    """기기 인증 시작 — user_code(폰에 입력할 코드)와 verification_url을 받는다."""
    return _post_form(DEVICE_CODE_URL, {"client_id": client_id, "scope": SCOPE})


def poll_for_token(creds: dict, device_code: str, interval: int, timeout_sec: int = 600) -> dict:
    """이찬호가 폰에서 허용할 때까지 기다렸다가 토큰을 받는다."""
    waited = 0
    while waited < timeout_sec:
        time.sleep(interval)
        waited += interval
        resp = _post_form(TOKEN_URL, {
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        })
        err = resp.get("error")
        if err == "authorization_pending":
            continue
        if err == "slow_down":
            interval += 2
            continue
        return resp  # 성공(access_token/refresh_token) 또는 진짜 에러
    return {"error": "timeout", "error_description": f"{timeout_sec}초 내 승인 없음"}


def access_token(creds: dict) -> str:
    """refresh_token으로 액세스 토큰 발급."""
    if "refresh_token" not in creds:
        raise ValueError("refresh_token 없음 — `python3 -m shorts.gdrive auth` 먼저")
    resp = _post_form(TOKEN_URL, {
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "refresh_token": creds["refresh_token"],
        "grant_type": "refresh_token",
    })
    if "access_token" not in resp:
        raise RuntimeError(f"토큰 갱신 실패: {resp}")
    return resp["access_token"]


def _api(url: str, token: str, method: str = "GET", payload: dict | None = None, timeout: int = 60) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Authorization": f"Bearer {token}"}
    if data:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def ensure_fallback_folder(token: str) -> str:
    """앱 소유 「코드방_업로드」 폴더 ID (없으면 생성)."""
    q = urllib.parse.quote(
        f"name = '{FALLBACK_FOLDER_NAME}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    )
    found = _api(f"{FILES_URL}?q={q}&fields=files(id,name)", token).get("files", [])
    if found:
        return found[0]["id"]
    made = _api(FILES_URL, token, method="POST", payload={
        "name": FALLBACK_FOLDER_NAME, "mimeType": "application/vnd.google-apps.folder",
    })
    return made["id"]


def find_in_folder(name: str, folder_id: str, token: str) -> str | None:
    """폴더 안에서 같은 이름의(휴지통 아닌) 파일 ID를 찾는다. 없으면 None.
    drive.file 스코프에선 앱이 만든 파일만 보이므로, 이전에 앱이 올린 산출물 덮어쓰기에 적합."""
    q = urllib.parse.quote(f"name = '{name}' and '{folder_id}' in parents and trashed = false")
    files = _api(f"{FILES_URL}?q={q}&fields=files(id,name)&supportsAllDrives=true"
                 f"&includeItemsFromAllDrives=true", token).get("files", [])
    return files[0]["id"] if files else None


def list_folder(folder_id: str, secrets_path: str | Path = DEFAULT_SECRETS,
                video_only: bool = False) -> list[dict]:
    """폴더 안 파일 목록 [{id,name,mimeType,size}]. drive.readonly 스코프 필요
    (형님 폰 업로드분=인트레이 열람용, 2026-07-25). 스코프 없으면 앱 생성분만 보임."""
    token = access_token(load_secrets(secrets_path))
    clauses = [f"'{folder_id}' in parents", "trashed = false"]
    if video_only:
        clauses.append("mimeType contains 'video/'")
    q = urllib.parse.quote(" and ".join(clauses))
    out: list[dict] = []
    page = ""
    for _ in range(20):  # 페이지네이션(최대 20페이지)
        url = (f"{FILES_URL}?q={q}&fields=nextPageToken,files(id,name,mimeType,size)"
               f"&pageSize=100&supportsAllDrives=true&includeItemsFromAllDrives=true")
        if page:
            url += f"&pageToken={page}"
        r = _api(url, token)
        out.extend(r.get("files", []))
        page = r.get("nextPageToken", "")
        if not page:
            break
    return out


def download_file(file_id: str, dest: str | Path, secrets_path: str | Path = DEFAULT_SECRETS) -> Path:
    """드라이브 파일을 로컬에 다운로드한다. drive.readonly 스코프 필요."""
    p = Path(dest)
    p.parent.mkdir(parents=True, exist_ok=True)
    token = access_token(load_secrets(secrets_path))
    url = f"{FILES_URL}/{file_id}?alt=media&supportsAllDrives=true"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=1800) as r:
        with open(p, "wb") as f:
            while chunk := r.read(8 * 1024 * 1024):  # 8MB chunks
                f.write(chunk)
    return p


def upload_file(path: str | Path, folder_id: str | None = None,
                secrets_path: str | Path = DEFAULT_SECRETS, name: str | None = None,
                overwrite: bool = False) -> dict:
    """영상/파일을 드라이브에 올리고 {id, name, webViewLink}를 돌려준다.

    folder_id 접근이 안 되면(drive.file 권한 한계) 「코드방_업로드」 폴더로 폴백.
    overwrite=True 면 폴더 안 같은 이름 파일의 '내용만 교체'(파일 ID·링크 유지, 중복 0).
    """
    p = Path(path)
    creds = load_secrets(secrets_path)
    token = access_token(creds)
    meta: dict = {"name": name or p.name}
    ctype = "video/mp4" if p.suffix.lower() in (".mp4", ".mov") else "application/octet-stream"

    # 덮어쓰기: 폴더에 같은 이름 있으면 그 파일 '미디어만' PATCH 교체 → 같은 링크 유지.
    existing = None
    if overwrite and folder_id:
        try:
            existing = find_in_folder(meta["name"], folder_id, token)
        except urllib.error.HTTPError:
            existing = None

    def _start_session(parent: str | None) -> str:
        m = dict(meta)
        if parent:
            m["parents"] = [parent]
        body = json.dumps(m).encode("utf-8")
        req = urllib.request.Request(UPLOAD_URL, data=body, method="POST", headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Upload-Content-Type": ctype,
            "X-Upload-Content-Length": str(p.stat().st_size),
        })
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.headers["Location"]

    def _start_update(file_id: str) -> str:
        url = (f"https://www.googleapis.com/upload/drive/v3/files/{file_id}"
               f"?uploadType=resumable&supportsAllDrives=true")
        req = urllib.request.Request(url, data=b"{}", method="PATCH", headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Upload-Content-Type": ctype,
            "X-Upload-Content-Length": str(p.stat().st_size),
        })
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.headers["Location"]

    if existing:
        session = _start_update(existing)
        method = "PUT"
    else:
        try:
            session = _start_session(folder_id)
        except urllib.error.HTTPError as e:
            if folder_id and e.code in (403, 404):
                session = _start_session(ensure_fallback_folder(token))
            else:
                raise
        method = "PUT"

    data = p.read_bytes()
    req = urllib.request.Request(session, data=data, method=method,
                                 headers={"Content-Length": str(len(data))})
    with urllib.request.urlopen(req, timeout=1800) as r:
        uploaded = json.loads(r.read())
    info = _api(f"{FILES_URL}/{uploaded['id']}?fields=id,name,webViewLink&supportsAllDrives=true", token)
    info["overwritten"] = bool(existing)
    return info


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="구글드라이브 기기 인증 + 업로드")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_auth = sub.add_parser("auth", help="기기 인증 (링크+코드 출력 후 승인 대기)")
    p_auth.add_argument("--secrets", default=DEFAULT_SECRETS)
    p_up = sub.add_parser("upload", help="파일 업로드")
    p_up.add_argument("file")
    p_up.add_argument("--folder-id", default=None)
    p_up.add_argument("--name", default=None)
    p_up.add_argument("--overwrite", action="store_true",
                      help="폴더 내 같은 이름 파일 내용만 교체 (링크 유지·중복0)")
    p_up.add_argument("--secrets", default=DEFAULT_SECRETS)
    p_ls = sub.add_parser("list", help="폴더 내 파일 목록 (drive.readonly 스코프 필요)")
    p_ls.add_argument("folder_id")
    p_ls.add_argument("--video-only", action="store_true")
    p_ls.add_argument("--secrets", default=DEFAULT_SECRETS)
    p_dl = sub.add_parser("download", help="파일 다운로드 (drive.readonly 스코프 필요)")
    p_dl.add_argument("file_id")
    p_dl.add_argument("dest", help="저장할 로컬 경로")
    p_dl.add_argument("--secrets", default=DEFAULT_SECRETS)
    args = ap.parse_args(argv)

    if args.cmd == "download":
        try:
            p = download_file(args.file_id, args.dest, args.secrets)
            print(f"✅ 다운로드 완료: {p} ({p.stat().st_size // 1048576}MB)")
            return 0
        except urllib.error.HTTPError as e:
            print(f"❌ 다운로드 실패({e.code})", file=sys.stderr)
            return 1

    if args.cmd == "list":
        try:
            files = list_folder(args.folder_id, args.secrets, video_only=args.video_only)
        except urllib.error.HTTPError as e:
            print(f"❌ 목록 실패({e.code}) — drive.readonly 스코프 없으면 앱 생성분만 보임. "
                  f"형님 재인증 필요(gdrive auth) 또는 브라우저 OAuth 토큰.", file=sys.stderr)
            return 1
        for f in files:
            sz = f.get("size")
            szs = f" {int(sz)//1048576}MB" if sz else ""
            print(f"{f['id']}\t{f['name']}\t{f.get('mimeType','')}{szs}")
        print(f"\n총 {len(files)}개", file=sys.stderr)
        return 0

    if args.cmd == "auth":
        creds = load_secrets(args.secrets)
        resp = device_code_request(creds["client_id"])
        if "user_code" not in resp:
            print(f"❌ 기기 인증 시작 실패: {resp}\n   OAuth 클라이언트 유형이 "
                  f"「TV 및 제한된 입력 장치」인지 확인하세요.", file=sys.stderr)
            return 1
        print(f"📱 폰에서 열기: {resp.get('verification_url', 'https://www.google.com/device')}")
        print(f"🔑 코드 입력: {resp['user_code']}")
        print("   (허용을 누를 때까지 기다립니다...)")
        token = poll_for_token(creds, resp["device_code"], int(resp.get("interval", 5)))
        if "refresh_token" not in token:
            print(f"❌ 승인 실패: {token}", file=sys.stderr)
            return 1
        creds["refresh_token"] = token["refresh_token"]
        Path(args.secrets).write_text(json.dumps(creds, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✅ 연결 완료 — {args.secrets}에 저장. 이제 upload 명령을 쓸 수 있습니다.")
        return 0

    info = upload_file(args.file, folder_id=args.folder_id, secrets_path=args.secrets,
                       name=args.name, overwrite=args.overwrite)
    tag = "덮어씀(링크유지)" if info.get("overwritten") else "새로 올림"
    print(f"✅ 업로드 완료[{tag}]: {info['name']}\n🔗 {info.get('webViewLink', '(링크 없음)')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
