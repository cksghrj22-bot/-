"""B롤 카탈로그 헬스체크 — 각 usable 클립의 드라이브 file_id가 실제 다운로드되는지 확인.

2026-07-22: MVI_8991의 file_id가 죽어(로그인 페이지/404) 배치 렌더가 중간에 실패한 사고 이후 도입.
렌더 배치 전에 `python3 -m shorts.catalog_health` 한 줄로 죽은 소스를 미리 걸러낸다.

동작: 각 file_id에 range 0-800 요청 → HTML(로그인)·404·빈응답이면 DEAD.
--fix 를 주면 DEAD 클립을 카탈로그에서 usable:false 로 자동 표시(내용은 지우지 않음).
"""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

CATALOG = Path("knowledge/broll_catalog.json")


def _alive(fid: str | None) -> bool | None:
    """True=살아있음, False=죽음, None=file_id 없음."""
    if not fid:
        return None
    url = f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t"
    r = subprocess.run(["curl", "-sL", "-r", "0-800", url], capture_output=True)
    head = r.stdout[:400].lower()
    if b"<!doctype html" in head or b"<html" in head:
        return False
    if b'"error"' in head and b"404" in head:
        return False
    return b"ftyp" in r.stdout or len(r.stdout) >= 700


def check(catalog_path: str | Path = CATALOG, fix: bool = False) -> list[tuple[str, str]]:
    c = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
    rows = []
    for cl in c["clips"]:
        if not cl.get("usable", True):
            continue
        st = _alive(cl.get("file_id"))
        label = "OK" if st else ("NO_FID" if st is None else "DEAD")
        rows.append((cl["id"], label))
        if st is False and fix:
            cl["usable"] = False
            cl["note"] = cl.get("note", "") + " ⛔헬스체크 DEAD"
    if fix:
        Path(catalog_path).write_text(json.dumps(c, ensure_ascii=False, indent=2), encoding="utf-8")
    return rows


def main(argv: list[str] | None = None) -> int:
    fix = "--fix" in (argv or sys.argv[1:])
    rows = check(fix=fix)
    for cid, st in rows:
        print(f"{st:7} {cid}")
    dead = [cid for cid, st in rows if st == "DEAD"]
    print(f"\n총 {len(rows)}개 · DEAD {len(dead)}: {dead}" + ("  → usable:false 처리함" if (fix and dead) else ""))
    return 1 if dead and not fix else 0


if __name__ == "__main__":
    sys.exit(main())
