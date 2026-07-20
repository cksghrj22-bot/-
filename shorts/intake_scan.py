"""B롤 인입 자동스캔 — 「쇼츠_배경클립_넣는곳」 폴더의 신규 영상을 broll_catalog.json에 자동 등록.

A방 배정(2026-07-20 B방 예고): 형님이 인입 폴더(1ZgGhMY-CBEugxy06AFCZ23lYuz89HDYI)에
촬영 원본을 대량 업로드하면, 파일명으로 카테고리를 추정해 카탈로그에 신규 등록한다.

⚠️ 스코프: gdrive.py 토큰은 drive.file(앱 생성분만) → 형님 업로드는 못 봄.
    실제 스캔은 **전체 스코프 소스**가 필요하다. 그래서 이 모듈은 '파일목록을 주는 함수'를
    주입받는 구조(list_files_fn) — Google Drive MCP 결과든, broader-scope 토큰이든 꽂으면 된다.
    list_files_fn() → [{"id": str, "name": str}, ...] 를 돌려주면 나머지(분류·등록)는 이게 한다.

완성 쇼츠(자막 박힌 영상)는 배경 부적합 → 파일명에 '시안/보이스시안/완성/final' 들어가면 스킵.
카테고리 추정 불가 시 category=null·note에 '수동분류필요'로 등록(사람이 확인).
"""
from __future__ import annotations
import json
import re
from pathlib import Path

CATALOG = Path("knowledge/broll_catalog.json")
INTAKE_FOLDER_ID = "1ZgGhMY-CBEugxy06AFCZ23lYuz89HDYI"  # 쇼츠_배경클립_넣는곳

# 파일명 키워드 → 카테고리 (앞쪽이 우선). broll_catalog.json의 _카테고리와 일치.
KEYWORD_CATEGORY: list[tuple[str, str]] = [
    (r"염색|새치|탈색|그라데이션|고인그레이|커버|브라운|컬러|color", "color"),
    (r"아이롱|펌|웨이브|매직|와인딩|스타일링|롤", "perm"),
    (r"두피|스케일링|탈모|scalp", "scalp"),
    (r"상담|컨설팅|진단|consult", "consult"),
    (r"커트|가발|숱|볼륨|질감|가위|섹션|cut", "cut"),
    (r"운동|하이록스|hyrox|헬스|러닝|땀|workout|gym", "workout"),
    (r"책|독서|필기|수첩|기록|reading", "reading"),
    (r"도쿄|교토|오사카|여행|풍경|항공|드론|거리|강변|열차|aerial|dji|tokyo|kyoto", "aerial"),
]

# 배경 부적합(완성본·자막 박힘) → 스킵
SKIP_PATTERNS = re.compile(r"시안|보이스시안|완성|final|자막|_최신|카드", re.IGNORECASE)
VIDEO_EXT = re.compile(r"\.(mp4|mov|m4v|avi|mkv|webm)$", re.IGNORECASE)


def categorize(name: str) -> str | None:
    """파일명으로 카테고리 추정. 못 맞추면 None(수동분류)."""
    low = name.lower()
    for pat, cat in KEYWORD_CATEGORY:
        if re.search(pat, low):
            return cat
    return None


def _clip_id_from_name(name: str) -> str:
    """카탈로그 id로 쓸 안정 키 — 확장자 뗀 파일명(공백→_)."""
    base = VIDEO_EXT.sub("", name).strip()
    return re.sub(r"\s+", "_", base)


def register_new(files: list[dict], catalog_path: Path = CATALOG) -> dict:
    """files=[{id,name},...] 중 신규 영상만 카탈로그에 등록. 이미 있는 file_id는 스킵.

    반환: {"added": [...], "skipped_existing": [...], "skipped_nonvideo": [...],
           "skipped_finished": [...], "manual": [...]}
    """
    cat = json.loads(catalog_path.read_text(encoding="utf-8"))
    existing_ids = {c.get("file_id") for c in cat["clips"] if c.get("file_id")}
    existing_keys = {c["id"] for c in cat["clips"]}
    res = {"added": [], "skipped_existing": [], "skipped_nonvideo": [],
           "skipped_finished": [], "manual": []}
    for f in files:
        name, fid = f.get("name", ""), f.get("id")
        if not VIDEO_EXT.search(name):
            res["skipped_nonvideo"].append(name); continue
        if SKIP_PATTERNS.search(name):
            res["skipped_finished"].append(name); continue
        if fid in existing_ids:
            res["skipped_existing"].append(name); continue
        key = _clip_id_from_name(name)
        # 키 충돌 방지
        base_key = key
        n = 2
        while key in existing_keys:
            key = f"{base_key}_{n}"; n += 1
        category = categorize(name)
        note = f"인입 자동등록(2026-07-20~). 원본 '{name}'."
        if category is None:
            note = "⚠️수동분류필요 — 파일명으로 카테고리 추정 실패. " + note
            res["manual"].append(name)
        entry = {"id": key, "category": category, "file_id": fid, "start": 0,
                 "note": note, "uses": 0, "_인입": True}
        cat["clips"].append(entry)
        existing_ids.add(fid); existing_keys.add(key)
        res["added"].append({"id": key, "category": category, "name": name})
    if res["added"]:
        catalog_path.write_text(json.dumps(cat, ensure_ascii=False, indent=2), encoding="utf-8")
    return res


def scan_and_register(list_files_fn, catalog_path: Path = CATALOG) -> dict:
    """list_files_fn() → [{id,name},...] 를 받아 신규 등록. 소스는 주입(MCP/토큰 무관)."""
    files = list_files_fn()
    return register_new(files, catalog_path)


def _list_via_gdrive(folder_id: str = INTAKE_FOLDER_ID) -> list[dict]:
    """gdrive.py 토큰으로 폴더 나열 — ⚠️drive.file 스코프라 앱 생성분만 보임(형님 업로드 X).
    전체 스코프 소스가 생기면 이 함수 대신 그걸 scan_and_register에 주입한다."""
    from .gdrive import load_secrets, access_token
    import urllib.request, urllib.parse
    creds = load_secrets("secrets/gdrive.json")
    tok = access_token(creds)
    q = urllib.parse.quote(f"'{folder_id}' in parents and trashed=false")
    url = f"https://www.googleapis.com/drive/v3/files?q={q}&fields=files(id,name)&pageSize=500"
    r = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}"})
    return json.load(urllib.request.urlopen(r)).get("files", [])


if __name__ == "__main__":
    import sys
    try:
        res = scan_and_register(_list_via_gdrive)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        if res["added"]:
            print(f"\n✅ {len(res['added'])}개 신규 등록. 수동분류필요={len(res['manual'])}")
        else:
            print("\n신규 없음(또는 drive.file 스코프라 안 보임 — 전체스코프 소스 필요)")
    except Exception as e:
        print(f"스캔 실패: {e!r}", file=sys.stderr)
        sys.exit(1)
