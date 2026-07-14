"""Obsidian vault 수집기.

vault는 마크다운 폴더지만 세 가지 전처리가 필요하다:
- YAML 프런트매터(--- ... ---) 제거 (본문만 인덱싱)
- 위키링크 변환: [[노트|별칭]] → 별칭, [[노트]] → 노트, ![[첨부]] → 제거
- .obsidian/ .trash/ 등 시스템 폴더 제외
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

from .ingest import Document, _make_doc_id

SKIP_DIRS = {".obsidian", ".trash", ".git", "node_modules"}

_FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)
_EMBED_RE = re.compile(r"!\[\[[^\]]*\]\]")
_WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")


def clean_note(text: str) -> str:
    """옵시디언 문법을 검색 가능한 평문으로 정리한다."""
    text = _FRONTMATTER_RE.sub("", text)
    text = _EMBED_RE.sub("", text)
    text = _WIKILINK_RE.sub(lambda m: (m.group(2) or m.group(1)).strip(), text)
    return text.strip()


def load_vault(path: str | Path) -> Iterator[Document]:
    """vault의 모든 노트(.md)를 Document로 순회한다."""
    root = Path(path).expanduser()
    if not root.exists():
        raise FileNotFoundError(f"vault 경로가 없습니다: {root}")
    for f in sorted(root.rglob("*.md")):
        if any(part in SKIP_DIRS for part in f.relative_to(root).parts):
            continue
        raw = f.read_text(encoding="utf-8", errors="replace")
        text = clean_note(raw)
        if not text:
            continue
        note_name = f.stem
        # 노트 제목을 본문 맨 앞에 붙여 제목 검색이 되게 한다
        if not text.startswith("#"):
            text = f"# {note_name}\n\n{text}"
        yield Document(
            doc_id=_make_doc_id(str(f.relative_to(root)), text),
            source=f"obsidian:{f.relative_to(root)}",
            text=text,
            metadata={"vault": root.name, "note": note_name},
        )
