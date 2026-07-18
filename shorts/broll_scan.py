"""B롤 자동스캔·카탈로그 — 폰이 드라이브에 자동으로 쌓는 원본을 '기억'하는 시스템.

왜 필요한가 (2026-07-18 이찬호: "B롤 자동스캔 찾는 시스템 만들기"):
- 형님 폰은 촬영본을 구글드라이브 폴더(폰_자동업로드)에 자동으로 올린다.
- 코드방은 그걸 바로 읽어 렌더에 쓴다(승인 팝업 불필요 — MCP 커넥터가 사용자 권한으로 읽음).
- 문제: 폴더엔 0바이트 실패분·중복·이미 써먹은 영상이 섞여 있다. 매번 눈으로 고르면 실수하고,
  같은 배경영상을 두 번 써서 저품질(shorts_config source_video_policy 위반)이 난다.
- 그래서 '카탈로그'가 기억한다: 뭐가 쓸 수 있고(0바이트·중복 제외), 뭘 이미 썼는지(재사용 금지).
  카탈로그는 git에 커밋 → 방이 리뉴얼돼도(채팅 기억 0) 기억이 남는다.

스코프 경계 (중요):
- drive.file(기기 인증, gdrive.py)은 '앱이 만든 파일'만 본다 → 폰 자동업로드분을 **못** 본다.
- 그래서 폴더 스캔(목록 뽑기)은 **코드방(MCP Google Drive 커넥터)** 이 한다. 이 모듈은 네트워크를
  타지 않는다 — 코드방이 뽑아준 '목록(JSON)'을 받아 병합·판정만 한다(테스트가 오프라인 통과).

한 줄 흐름 (코드방이 매 렌더 앞에 돈다):
  1) 코드방: 드라이브 폰 폴더를 MCP로 스캔 → listing.json 저장
  2) python3 -m shorts.broll_scan merge listing.json      # 카탈로그에 병합(0바이트·중복 자동 제외)
  3) python3 -m shorts.broll_scan pick -n 1                # 안 쓴 원본 1개 추천(오래된 것부터)
  4) 코드방: 그 id를 download → 렌더
  5) python3 -m shorts.broll_scan use 09_제목 <id>          # 썼다고 표시(다신 안 뽑힘)

카탈로그: content/broll/카탈로그.json  (id → {name,size,created,source,ext,view,used_in})
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

CATALOG_PATH = "content/broll/카탈로그.json"

# 알려진 B롤 소스 폴더 (드라이브). 코드방이 스캔할 대상.
SOURCE_FOLDERS = {
    "174TFm5_cJyfi-U0X3HM_JKGN3gc3avYA": "폰_자동업로드",
    "1MBvVanqFgvBjk7hS2wjOaYN6oiaoBtlO": "코드방_인입",
}


def load(path: str | Path = CATALOG_PATH) -> dict:
    p = Path(path)
    if not p.exists():
        return {"sources": dict(SOURCE_FOLDERS), "clips": {}}
    cat = json.loads(p.read_text(encoding="utf-8"))
    cat.setdefault("sources", dict(SOURCE_FOLDERS))
    cat.setdefault("clips", {})
    return cat


def save(cat: dict, path: str | Path = CATALOG_PATH) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    # clips를 created(오래된 순)→id로 정렬해 저장 → diff 안정적, 사람이 읽기 쉬움.
    clips = dict(sorted(cat["clips"].items(),
                        key=lambda kv: (kv[1].get("created", ""), kv[0])))
    out = {k: v for k, v in cat.items() if k != "clips"}
    out["clips"] = clips
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


def _files_from(listing) -> list[dict]:
    """MCP search_files 응답(dict) 또는 파일 목록(list) 둘 다 받는다."""
    if isinstance(listing, dict):
        return listing.get("files", [])
    return list(listing)


def merge_listing(cat: dict, listing, source_name: str | None = None) -> dict:
    """드라이브 목록을 카탈로그에 병합. 반환: {added, skipped_zero, duplicate, updated}.

    - 0바이트(업로드 실패/진행중)는 건너뛴다.
    - 같은 id는 dict 키라 자동 dedup. 이미 있으면 메타만 갱신하되 used_in은 보존.
    """
    stats = {"added": 0, "skipped_zero": 0, "duplicate": 0, "updated": 0}
    seen_this_run: set[str] = set()
    for f in _files_from(listing):
        fid = f.get("id")
        if not fid:
            continue
        try:
            size = int(f.get("fileSize", f.get("size", 0)) or 0)
        except (TypeError, ValueError):
            size = 0
        if size <= 0:
            stats["skipped_zero"] += 1
            continue
        if fid in seen_this_run:
            stats["duplicate"] += 1
            continue
        seen_this_run.add(fid)
        parent = f.get("parentId", "")
        entry = {
            "name": f.get("title", f.get("name", "")),
            "size": size,
            "created": f.get("createdTime", ""),
            "source": source_name or cat.get("sources", {}).get(parent, parent),
            "ext": (f.get("fileExtension") or Path(f.get("title", "")).suffix.lstrip(".")).upper(),
            "view": f.get("viewUrl", ""),
        }
        if fid in cat["clips"]:
            entry["used_in"] = cat["clips"][fid].get("used_in", [])
            if cat["clips"][fid] != entry:
                stats["updated"] += 1
            cat["clips"][fid] = entry
        else:
            entry["used_in"] = []
            cat["clips"][fid] = entry
            stats["added"] += 1
    return stats


def usable(cat: dict) -> list[dict]:
    """쓸 수 있는 클립(0바이트 아님·아직 안 씀), 오래된 것부터."""
    items = [
        {"id": fid, **c}
        for fid, c in cat["clips"].items()
        if c.get("size", 0) > 0 and not c.get("used_in")
    ]
    return sorted(items, key=lambda c: (c.get("created", ""), c["id"]))


def pick(cat: dict, n: int = 1) -> list[dict]:
    """안 쓴 원본 n개 추천(오래된 순). 재사용 금지 정책을 코드로 강제."""
    return usable(cat)[:max(0, n)]


def mark_used(cat: dict, short: str, ids: list[str]) -> list[str]:
    """해당 id들을 '이 쇼츠에 썼다'고 표시. 반환: 실제로 표시된 id."""
    marked = []
    for fid in ids:
        c = cat["clips"].get(fid)
        if c is None:
            continue
        if short not in c.setdefault("used_in", []):
            c["used_in"].append(short)
        marked.append(fid)
    return marked


def summary(cat: dict) -> dict:
    clips = cat["clips"]
    used = sum(1 for c in clips.values() if c.get("used_in"))
    return {"total": len(clips), "usable": len(usable(cat)), "used": used}


def _fmt_mb(size: int) -> str:
    return f"{size / 1_048_576:.0f}MB"


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="B롤 자동스캔 카탈로그")
    ap.add_argument("--catalog", default=CATALOG_PATH)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_m = sub.add_parser("merge", help="드라이브 목록(JSON)을 카탈로그에 병합")
    p_m.add_argument("listing", help="코드방이 뽑아준 드라이브 목록 JSON 경로")
    p_m.add_argument("--source-name", default=None, help="소스 폴더 이름 강제 지정")

    sub.add_parser("list", help="쓸 수 있는 클립 목록(안 쓴 것)")
    p_p = sub.add_parser("pick", help="안 쓴 원본 추천")
    p_p.add_argument("-n", type=int, default=1)

    p_u = sub.add_parser("use", help="클립을 '썼다'고 표시")
    p_u.add_argument("short", help="쇼츠 이름(예: 09_제목)")
    p_u.add_argument("ids", nargs="+", help="파일 id(들)")

    sub.add_parser("stats", help="요약")
    args = ap.parse_args(argv)

    cat = load(args.catalog)

    if args.cmd == "merge":
        listing = json.loads(Path(args.listing).read_text(encoding="utf-8"))
        st = merge_listing(cat, listing, source_name=args.source_name)
        save(cat, args.catalog)
        s = summary(cat)
        print(f"✅ 병합: +{st['added']} 신규 · {st['updated']} 갱신 · "
              f"{st['skipped_zero']} 0바이트제외 · {st['duplicate']} 중복제외")
        print(f"   카탈로그: 총 {s['total']} · 쓸수있음 {s['usable']} · 사용됨 {s['used']}")
        return 0

    if args.cmd == "list":
        for c in usable(cat):
            print(f"{c['id']}  {c['name']:24} {_fmt_mb(c['size']):>7}  {c.get('source','')}")
        return 0

    if args.cmd == "pick":
        picks = pick(cat, args.n)
        if not picks:
            print("⚠️ 쓸 수 있는(안 쓴) B롤이 없음 — merge로 새 스캔을 넣거나 폰에서 더 촬영.",
                  file=sys.stderr)
            return 1
        for c in picks:
            print(f"{c['id']}\t{c['name']}\t{_fmt_mb(c['size'])}\t{c.get('view','')}")
        return 0

    if args.cmd == "use":
        marked = mark_used(cat, args.short, args.ids)
        save(cat, args.catalog)
        print(f"✅ '{args.short}'에 사용 표시: {len(marked)}개 — 다시는 추천 안 됨.")
        return 0

    if args.cmd == "stats":
        s = summary(cat)
        print(f"총 {s['total']} · 쓸수있음 {s['usable']} · 사용됨 {s['used']}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
