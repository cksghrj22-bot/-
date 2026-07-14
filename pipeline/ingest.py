"""문서 수집 단계: 파일/디렉터리에서 텍스트 문서를 읽어들인다."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".rst", ".py", ".json", ".csv"}


@dataclass
class Document:
    """수집된 문서 한 건."""

    doc_id: str
    source: str
    text: str
    metadata: dict = field(default_factory=dict)


def _make_doc_id(source: str, text: str) -> str:
    return hashlib.sha256(f"{source}\n{text}".encode("utf-8")).hexdigest()[:16]


def load_file(path: str | Path) -> Document:
    """단일 텍스트 파일을 Document로 읽는다."""
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    return Document(
        doc_id=_make_doc_id(str(p), text),
        source=str(p),
        text=text,
        metadata={"filename": p.name, "size": len(text)},
    )


def load_directory(path: str | Path, recursive: bool = True) -> Iterator[Document]:
    """디렉터리에서 텍스트 확장자 파일들을 순회하며 읽는다."""
    p = Path(path)
    pattern = "**/*" if recursive else "*"
    for f in sorted(p.glob(pattern)):
        if f.is_file() and f.suffix.lower() in TEXT_EXTENSIONS:
            yield load_file(f)
