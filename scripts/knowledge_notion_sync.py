#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""트렁크/옵시디언 인박스/knowledge markdown -> Notion 지식 라이브러리 색인."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import time
import traceback
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path.home() / "atnown-content-pipeline"
TRUNK = Path.home() / "atnown-trunk"
CONFIG = ROOT / "secrets" / "notion.json"
LOG = ROOT / "logs" / "knowledge_notion_sync.log"
BRIEFING = ROOT / "_cowork_sync" / "briefings" / "노션옵시디언_연동_결과.txt"
STATE = ROOT / "_status" / "knowledge_notion_sync.json"
NOTION_VERSION = "2022-06-28"

SCAN_ROOTS = [
    TRUNK,
    ROOT / "_obsidian_in",
    ROOT / "knowledge",
]

STOP_DIRS = {
    ".git", ".obsidian", "node_modules", "__pycache__", "_jobs", "_publish_jobs",
    "logs", ".venv", "venv", "dist", "build",
}

CLASS_NAMES = ("구술", "재정의", "규칙", "산출", "씨앗")
BUILTIN_TERMS = {
    "커트", "질감", "텍스처", "레이어드", "볼륨", "공간", "움직임", "펌", "앞머리",
    "두피", "말리는 법", "재현", "방향", "무드", "A라인", "교육", "시스템", "서사",
    "가치", "옵시디언", "노션", "지식 라이브러리", "파이프라인", "씨앗", "정본",
}


def log(line: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{stamp}] {line}\n")


def load_config() -> dict:
    with CONFIG.open(encoding="utf-8") as f:
        cfg = json.load(f)
    missing = [k for k in ("token", "knowledge_database_id") if not cfg.get(k)]
    if missing:
        raise SystemExit("missing notion config: " + ", ".join(missing))
    return cfg


def notion(cfg: dict, method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request("https://api.notion.com/v1" + path, data=data, method=method)
    req.add_header("Authorization", "Bearer " + cfg["token"].strip())
    req.add_header("Notion-Version", NOTION_VERSION)
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "AtnownKnowledgeSync/1.0")
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 4:
                time.sleep(2 + attempt * 2)
                continue
            detail = e.read().decode("utf-8", errors="replace")[:1000]
            raise RuntimeError(f"HTTP {e.code} {path}: {detail}") from e
        except (TimeoutError, urllib.error.URLError, OSError):
            if attempt < 4:
                time.sleep(2 + attempt * 2)
                continue
            raise
    raise RuntimeError("unreachable")


def text_prop(value: str, limit: int = 1900) -> dict:
    value = (value or "")[:limit]
    return {"rich_text": [{"text": {"content": value}}]} if value else {"rich_text": []}


def title_prop(value: str) -> dict:
    return {"title": [{"text": {"content": (value or "무제")[:180]}}]}


def tags_prop(values: list[str]) -> dict:
    # 콤마로 분리하고 각각 정리 (Notion multi_select는 콤마를 옵션 이름에 허용 안 함)
    cleaned = []
    for v in values:
        for part in v.split(","):
            part = part.strip()
            if part and part not in cleaned:
                cleaned.append(part[:100])
    return {"multi_select": [{"name": t} for t in cleaned[:20]]}


def select_prop(value: str) -> dict:
    return {"select": {"name": value}}


def date_prop(value: str) -> dict:
    return {"date": {"start": value}}


def text_value(prop: dict) -> str:
    typ = prop.get("type")
    if typ == "rich_text":
        return "".join(x.get("plain_text", "") for x in prop.get("rich_text", []))
    if typ == "title":
        return "".join(x.get("plain_text", "") for x in prop.get("title", []))
    if typ == "date":
        return ((prop.get("date") or {}).get("start") or "")
    return ""


def query_existing(cfg: dict) -> dict[str, dict]:
    db = cfg["knowledge_database_id"]
    out: dict[str, dict] = {}
    cursor = None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        res = notion(cfg, "POST", f"/databases/{db}/query", body)
        for page in res.get("results", []):
            props = page.get("properties", {})
            src = text_value(props.get("출처경로", {})).strip()
            if src:
                out[src] = {
                    "id": page["id"],
                    "hash": text_value(props.get("파일해시", {})).strip(),
                }
        if not res.get("has_more"):
            return out
        cursor = res.get("next_cursor")


def iter_markdown_files() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in STOP_DIRS and not d.startswith(".")]
            for name in filenames:
                if name.endswith(".md"):
                    files.append(Path(dirpath) / name)
    return sorted(set(files), key=lambda p: str(p))


def rel_source(path: Path) -> str:
    for base in (TRUNK, ROOT):
        try:
            return f"{base.name}/{path.relative_to(base).as_posix()}"
        except ValueError:
            pass
    return str(path)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def frontmatter(text: str) -> dict:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    data: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            data[k.strip().lower()] = v.strip().strip('"').strip("'")
    return data


def title_for(path: Path, text: str, fm: dict) -> str:
    if fm.get("title") or fm.get("name"):
        return fm.get("title") or fm.get("name")
    for line in text.splitlines()[:40]:
        m = re.match(r"^#\s+(.+)", line.strip())
        if m:
            return m.group(1).strip()[:180]
    return path.stem


def load_vocab() -> set[str]:
    vocab = set(BUILTIN_TERMS)
    for p in (TRUNK / "knowledge" / "재정의_카드_대장.md", TRUNK / "knowledge" / "키워드_지도.md"):
        if not p.exists():
            continue
        txt = read_text(p)
        for cell in re.findall(r"\*\*([^*]{2,40})\*\*|(?:^|\|)\s*([가-힣A-Za-z0-9/· _-]{2,30})\s*(?=\|)", txt, re.M):
            for part in cell:
                if not part:
                    continue
                for term in re.split(r"[=/·,()↔]+", part):
                    term = term.strip()
                    if 2 <= len(term) <= 20:
                        vocab.add(term)
    return vocab


def keywords(title: str, text: str, fm: dict, vocab: set[str]) -> list[str]:
    found: list[str] = []
    raw = " ".join([title, fm.get("keywords", ""), fm.get("tags", ""), text[:6000]])
    for tag in re.findall(r"#([0-9A-Za-z가-힣_-]{2,30})", raw):
        found.append(tag)
    for term in sorted(vocab, key=len, reverse=True):
        if term and term in raw:
            found.append(term)
    for term in re.findall(r"\*\*([^*]{2,24})\s*=\s*([^*]{2,24})\*\*", raw):
        found.extend([x.strip() for x in term])
    words = re.findall(r"[가-힣A-Za-z][가-힣A-Za-z0-9_-]{2,}", title)
    found.extend(words)
    out = []
    seen = set()
    for x in found:
        x = re.split(r"[,，.!?;:、\"“”‘’]", x, 1)[0]
        x = re.sub(r"\s+", " ", x).strip(" -_#|[]()")
        if x.count(" ") > 3:
            continue
        if 2 <= len(x) <= 30 and x not in seen:
            seen.add(x)
            out.append(x)
    return out[:20]


def category(path: Path, title: str, text: str) -> str:
    s = f"{path.as_posix()} {title} {text[:2000]}"
    if any(x in s for x in ("구술", "보이스", "한마디", "영상일기", "브레인_생각")):
        return "구술"
    if "재정의" in s or re.search(r"\*\*[^*]{2,30}\s*=\s*[^*]{2,30}\*\*", s):
        return "재정의"
    if any(x in s for x in ("규칙", "정본", "프로토콜", "가이드", "README", "시스템", "런북")):
        return "규칙"
    if any(x in s for x in ("씨앗", "아이디어", "후보", "seed")):
        return "씨앗"
    return "산출"


def file_url(path: Path) -> str:
    return "file://" + urllib.request.pathname2url(str(path))


def make_blocks(text: str) -> list[dict]:
    body = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S).strip()[:18000]
    chunks = [body[i:i + 1900] for i in range(0, len(body), 1900)][:10]
    return [
        {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": c}}]}}
        for c in chunks if c.strip()
    ]


def page_props(item: dict) -> dict:
    return {
        "제목": title_prop(item["title"]),
        "키워드": tags_prop(item["keywords"]),
        "분류": select_prop(item["category"]),
        "출처경로": text_prop(item["source"]),
        "날짜": date_prop(item["date"]),
        "본문": text_prop(item["snippet"]),
        "링크": {"url": item["url"]},
        "파일해시": text_prop(item["hash"]),
        "수정시각": date_prop(item["mtime_iso"]),
    }


def build_item(path: Path, vocab: set[str]) -> dict:
    text = read_text(path)
    fm = frontmatter(text)
    title = title_for(path, text, fm)
    mtime = dt.datetime.fromtimestamp(path.stat().st_mtime).astimezone()
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {
        "path": path,
        "source": rel_source(path),
        "title": title,
        "keywords": keywords(title, text, fm, vocab),
        "category": category(path, title, text),
        "date": mtime.strftime("%Y-%m-%d"),
        "mtime_iso": mtime.isoformat(timespec="seconds"),
        "snippet": re.sub(r"\s+", " ", text).strip()[:1800],
        "url": file_url(path),
        "hash": digest,
        "blocks": make_blocks(text),
    }


def sync() -> dict:
    cfg = load_config()
    vocab = load_vocab()
    existing = query_existing(cfg)
    created = updated = unchanged = failed = 0
    errors: list[str] = []
    files = iter_markdown_files()
    for idx, path in enumerate(files, 1):
        try:
            item = build_item(path, vocab)
            old = existing.get(item["source"])
            if old and old.get("hash") == item["hash"]:
                unchanged += 1
                continue
            props = page_props(item)
            if old:
                notion(cfg, "PATCH", f"/pages/{old['id']}", {"properties": props})
                updated += 1
            else:
                notion(cfg, "POST", "/pages", {
                    "parent": {"database_id": cfg["knowledge_database_id"]},
                    "properties": props,
                    "children": item["blocks"],
                })
                created += 1
            time.sleep(0.35)
            if idx % 50 == 0:
                log(f"progress {idx}/{len(files)} created={created} updated={updated} unchanged={unchanged}")
        except Exception as e:
            failed += 1
            errors.append(f"{rel_source(path)}: {type(e).__name__}: {e}")
            log(errors[-1])
    result = {
        "ok": failed == 0,
        "scanned": len(files),
        "created": created,
        "updated": updated,
        "unchanged": unchanged,
        "failed": failed,
        "database_id": cfg["knowledge_database_id"],
        "database_url": cfg.get("knowledge_database_url", ""),
        "finished_at": dt.datetime.now().isoformat(timespec="seconds"),
        "errors": errors[:20],
    }
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> None:
    try:
        res = sync()
        print(json.dumps(res, ensure_ascii=False))
    except Exception:
        tb = traceback.format_exc()
        log(tb)
        raise


if __name__ == "__main__":
    main()
