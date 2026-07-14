"""청크 분할 단계: 문서를 검색 단위 조각으로 나눈다."""

from __future__ import annotations

from dataclasses import dataclass, field

from .ingest import Document


@dataclass
class Chunk:
    """인덱싱/검색의 최소 단위."""

    chunk_id: str
    doc_id: str
    source: str
    text: str
    metadata: dict = field(default_factory=dict)


def split_text(text: str, max_chars: int = 800, overlap: int = 100) -> list[str]:
    """문단 경계를 우선 존중하며 max_chars 이하 조각으로 나눈다.

    한 문단이 max_chars를 넘으면 overlap만큼 겹치게 잘라낸다.
    """
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    if not 0 <= overlap < max_chars:
        raise ValueError("overlap must satisfy 0 <= overlap < max_chars")

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    pieces: list[str] = []
    buffer = ""

    for para in paragraphs:
        if len(para) > max_chars:
            if buffer:
                pieces.append(buffer)
                buffer = ""
            start = 0
            while start < len(para):
                pieces.append(para[start : start + max_chars])
                start += max_chars - overlap
            continue
        candidate = f"{buffer}\n\n{para}" if buffer else para
        if len(candidate) <= max_chars:
            buffer = candidate
        else:
            pieces.append(buffer)
            buffer = para

    if buffer:
        pieces.append(buffer)
    return pieces


def chunk_document(doc: Document, max_chars: int = 800, overlap: int = 100) -> list[Chunk]:
    """Document를 Chunk 리스트로 변환한다."""
    return [
        Chunk(
            chunk_id=f"{doc.doc_id}:{i}",
            doc_id=doc.doc_id,
            source=doc.source,
            text=piece,
            metadata=dict(doc.metadata),
        )
        for i, piece in enumerate(split_text(doc.text, max_chars=max_chars, overlap=overlap))
    ]
