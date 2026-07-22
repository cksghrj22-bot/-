"""B롤 자동 정리 — 포토싱크가 흩뿌린 영상을 코드방_B롤_인트레이로 모은다.

배경(2026-07-23 이찬호): 포토싱크가 동영상을 새 '비디오'/'Documents' 폴더로
따로 넣어 인트레이가 아니라 엉뚱한 데 쌓임. 이 스크립트가 소스 폴더들의
영상을 인트레이 폴더로 이동(같은 드라이브 내 parents 변경 = 사본 안 생김).

⚠️ 실행 정책:
- 기본은 dry-run(무엇을 옮길지 출력만). 실제 이동은 `--go` 필요.
- 예약 실행(무인 자동)은 규약상 **본진(맥스튜디오)** 에서만. 여기선 코드 보관 + 수동 실행.
- secrets/gdrive.json 필요(기기 인증분). secrets는 절대 커밋 안 함.

사용:
    python3 -m shorts.broll_sort                 # dry-run(미리보기)
    python3 -m shorts.broll_sort --go            # 실제 이동
    python3 -m shorts.broll_sort --since 2026-07-22  # 그 날짜 이후 촬영분만
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request

from .gdrive import FILES_URL, access_token, load_secrets

# 코드방_B롤_인트레이 (정본 목적지)
INTRAY_FOLDER_ID = "1MBvVanqFgvBjk7hS2wjOaYN6oiaoBtlO"

# 포토싱크가 영상을 흩뿌리는 소스 폴더들(발견되는 대로 추가)
SOURCE_FOLDER_IDS = [
    "1cGR7Vgqr69SP6KD59VVziBWZ2EjgmW7y",  # '비디오' (수동 전송분)
    "1G86WrcS1NPnYcFqqYJ5DsiwED_c_-pzS",  # 'Documents' (자동 백업분)
]


def _get(url: str, token: str) -> dict:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())


def _list_videos(folder_id: str, token: str, since: str | None) -> list[dict]:
    q = f"'{folder_id}' in parents and mimeType contains 'video/' and trashed = false"
    if since:
        q += f" and modifiedTime > '{since}T00:00:00'"
    params = urllib.parse.urlencode({
        "q": q,
        "fields": "files(id,name,parents,modifiedTime),nextPageToken",
        "pageSize": "1000",
    })
    out, page = [], None
    while True:
        url = f"{FILES_URL}?{params}"
        if page:
            url += f"&pageToken={page}"
        data = _get(url, token)
        out.extend(data.get("files", []))
        page = data.get("nextPageToken")
        if not page:
            break
    return out


def _move(file_id: str, add: str, remove: str, token: str) -> None:
    url = f"{FILES_URL}/{file_id}?addParents={add}&removeParents={remove}&fields=id,parents"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"}, method="PATCH")
    urllib.request.urlopen(req).read()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--go", action="store_true", help="실제 이동(미지정 시 dry-run)")
    ap.add_argument("--since", default=None, help="이 날짜(YYYY-MM-DD) 이후 촬영분만")
    ap.add_argument("--secrets", default="secrets/gdrive.json")
    args = ap.parse_args(argv)

    token = access_token(load_secrets(args.secrets))
    total = 0
    for src in SOURCE_FOLDER_IDS:
        if src == INTRAY_FOLDER_ID:
            continue
        vids = _list_videos(src, token, args.since)
        for v in vids:
            total += 1
            tag = "MOVE" if args.go else "DRY "
            print(f"[{tag}] {v['name']}  ({v.get('modifiedTime','?')})  {src} → 인트레이")
            if args.go:
                _move(v["id"], INTRAY_FOLDER_ID, src, token)
    print(f"\n{'이동 완료' if args.go else '미리보기'}: 영상 {total}개"
          + ("" if args.go else "  — 실제 이동하려면 --go"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
