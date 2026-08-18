"""인스타그램 릴스 업로드 (Instagram Graph API, 비즈니스/크리에이터 계정 필요).

secrets/instagram.json 형식:
    {
      "access_token": "장기 액세스 토큰",
      "ig_user_id": "인스타그램 비즈니스 계정 ID"
    }

절차: 미디어 컨테이너 생성 → rupload로 영상 전송 → 처리 대기 → 게시.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

GRAPH = "https://graph.facebook.com/v19.0"
RUPLOAD = "https://rupload.facebook.com/ig-api-upload/v19.0"


def load_credentials(path: str | Path) -> dict:
    creds = json.loads(Path(path).read_text(encoding="utf-8"))
    missing = {"access_token", "ig_user_id"} - creds.keys()
    if missing:
        raise ValueError(f"instagram 자격증명에 누락된 키: {sorted(missing)}")
    return creds


def _post(url: str, params: dict) -> dict:
    data = urllib.parse.urlencode(params).encode()
    with urllib.request.urlopen(urllib.request.Request(url, data=data, method="POST"), timeout=60) as r:
        return json.loads(r.read())


def _get(url: str, params: dict) -> dict:
    with urllib.request.urlopen(f"{url}?{urllib.parse.urlencode(params)}", timeout=60) as r:
        return json.loads(r.read())


def upload_photo(image_url: str, caption: str, creds: dict) -> str:
    """피드에 사진 1장을 게시하고 미디어 ID를 반환한다. image_url은 공개 URL이어야 한다."""
    token = creds["access_token"]
    user = creds["ig_user_id"]
    container = _post(
        f"{GRAPH}/{user}/media",
        {"image_url": image_url, "caption": caption, "access_token": token},
    )
    published = _post(
        f"{GRAPH}/{user}/media_publish",
        {"creation_id": container["id"], "access_token": token},
    )
    return published["id"]


def upload_carousel(image_urls: list[str], caption: str, creds: dict) -> str:
    """피드에 캐러셀(2~10장, 카드뉴스용)을 게시하고 미디어 ID를 반환한다."""
    if not 2 <= len(image_urls) <= 10:
        raise ValueError("캐러셀은 2~10장이어야 한다")
    token = creds["access_token"]
    user = creds["ig_user_id"]
    children = []
    for url in image_urls:
        item = _post(
            f"{GRAPH}/{user}/media",
            {"image_url": url, "is_carousel_item": "true", "access_token": token},
        )
        children.append(item["id"])
    container = _post(
        f"{GRAPH}/{user}/media",
        {
            "media_type": "CAROUSEL",
            "children": ",".join(children),
            "caption": caption,
            "access_token": token,
        },
    )
    published = _post(
        f"{GRAPH}/{user}/media_publish",
        {"creation_id": container["id"], "access_token": token},
    )
    return published["id"]


def upload_reel(video_path: str | Path, caption: str, creds: dict, timeout_sec: int = 600, room: str = "본진") -> str:
    """릴스를 업로드·게시하고 미디어 ID를 반환한다."""
    video_path = Path(video_path)
    token = creds["access_token"]
    user = creds["ig_user_id"]

    # 1) 컨테이너 생성 (로컬 업로드 모드)
    container = _post(
        f"{GRAPH}/{user}/media",
        {"media_type": "REELS", "upload_type": "resumable", "caption": caption, "access_token": token},
    )
    container_id = container["id"]
    upload_uri = container.get("uri", f"{RUPLOAD}/{container_id}")  # 응답 URI 사용

    # 2) 영상 바이너리 전송
    data = video_path.read_bytes()
    request = urllib.request.Request(
        upload_uri,  # 응답에서 받은 URI 사용 (버전 자동 맞춤)
        data=data,
        method="POST",
        headers={
            "Authorization": f"OAuth {token}",
            "offset": "0",
            "file_size": str(len(data)),
        },
    )
    with urllib.request.urlopen(request, timeout=600) as r:
        result = json.loads(r.read())
    if not result.get("success", True):
        raise RuntimeError(f"영상 전송 실패: {result}")

    # 3) 처리 완료 대기
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        status = _get(f"{GRAPH}/{container_id}", {"fields": "status_code", "access_token": token})
        code = status.get("status_code")
        if code == "FINISHED":
            break
        if code == "ERROR":
            raise RuntimeError(f"인스타그램 처리 실패: {status}")
        time.sleep(10)
    else:
        raise TimeoutError("인스타그램 영상 처리 대기 시간 초과")

    # 4) 게시
    published = _post(
        f"{GRAPH}/{user}/media_publish",
        {"creation_id": container_id, "access_token": token},
    )
    media_id = published["id"]

    # 5) 자동 로그 기록
    try:
        from scripts.publish_logger import log_publish
        title = video_path.stem
        log_publish("instagram", room, title, media_id, caption)
    except Exception:
        pass  # 로그 실패해도 발행은 성공

    return media_id


def _wait_ready(container_id: str, token: str, timeout_sec: int = 600) -> None:
    """영상 아이템은 인스타가 처리(FINISHED)할 때까지 기다려야 게시할 수 있다."""
    import time as _t
    t0 = _t.time()
    while _t.time() - t0 < timeout_sec:
        st = _get(f"{GRAPH}/{container_id}", {"fields": "status_code,status", "access_token": token})
        code = st.get("status_code")
        if code == "FINISHED":
            return
        if code == "ERROR":
            raise RuntimeError(f"컨테이너 {container_id} 처리 실패: {st.get('status')}")
        _t.sleep(5)
    raise TimeoutError(f"컨테이너 {container_id} 처리 대기 시간 초과")


def upload_mixed_carousel(items: list[dict], caption: str, creds: dict,
                          dry_run: bool = True) -> str:
    """사진·영상 섞인 캐러셀을 게시한다.

    items = [{"url": "...", "kind": "image"|"video"}, ...]  (2~10개)

    ⚠️ Graph API 는 로컬 파일을 받지 않는다. **인스타 서버가 직접 받아갈 수 있는 공개 URL**이어야 한다.
       구글드라이브 공유링크는 HTML 리다이렉트라 자주 거부된다 — 쓰지 말 것.

    dry_run=True 면 **아무것도 게시하지 않고** URL 도달 가능성만 실측해서 보고한다.
    발행은 되돌릴 수 없으므로 기본값이 dry_run 이다. 실제 게시는 명시적으로 dry_run=False.
    """
    if not 2 <= len(items) <= 10:
        raise ValueError("캐러셀은 2~10개여야 한다")
    token = creds["access_token"]
    user = creds["ig_user_id"]

    # 0) URL 실측 — 인스타가 못 받아갈 URL 이면 게시 자체가 실패한다
    problems = []
    for it in items:
        try:
            req = urllib.request.Request(it["url"], method="HEAD")
            with urllib.request.urlopen(req, timeout=30) as r:
                ctype = r.headers.get("Content-Type", "")
                clen = int(r.headers.get("Content-Length") or 0)
                ok_type = ("video" in ctype) if it["kind"] == "video" else ("image" in ctype)
                print(f"  {it['kind']:5s} {clen/1048576:7.2f}MB  {ctype:28s} {it['url']}")
                if not ok_type:
                    problems.append(f"{it['url']} → Content-Type 이 {ctype} (파일이 아니라 페이지일 수 있다)")
        except Exception as e:
            problems.append(f"{it['url']} → 접근 실패 {e}")
    if problems:
        for p in problems:
            print("  ⛔ " + p)
        raise RuntimeError(f"공개 URL {len(problems)}건이 인스타가 받아갈 수 없는 상태다. 게시 중단.")

    if dry_run:
        print(f"\n[DRY RUN] URL {len(items)}건 전부 도달 가능. 캡션 {len(caption)}자.")
        print("  실제 게시하려면 dry_run=False. **되돌릴 수 없다.**")
        return "(dry-run)"

    # 1) 자식 컨테이너
    children = []
    for it in items:
        params = {"is_carousel_item": "true", "access_token": token}
        if it["kind"] == "video":
            params["media_type"] = "VIDEO"
            params["video_url"] = it["url"]
        else:
            params["image_url"] = it["url"]
        child = _post(f"{GRAPH}/{user}/media", params)
        children.append((child["id"], it["kind"]))
        print(f"  자식 생성 {child['id']} ({it['kind']})")

    # 2) 영상은 처리 완료 대기
    for cid, kind in children:
        if kind == "video":
            _wait_ready(cid, token)
            print(f"  처리 완료 {cid}")

    # 3) 부모 컨테이너 → 게시
    container = _post(f"{GRAPH}/{user}/media", {
        "media_type": "CAROUSEL",
        "children": ",".join(c for c, _ in children),
        "caption": caption,
        "access_token": token,
    })
    _wait_ready(container["id"], token)
    published = _post(f"{GRAPH}/{user}/media_publish",
                      {"creation_id": container["id"], "access_token": token})
    return published["id"]
