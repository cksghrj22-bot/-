"""브리핑 단계: 수집 결과 + 지식 베이스 현황을 아침 브리핑 마크다운으로 만든다."""

from __future__ import annotations

import json
from pathlib import Path

from .chunk import chunk_document
from .collect import FeedItem, FeedResult, collect_feeds
from .index import Index
from .ingest import Document, _make_doc_id

DEFAULT_CONFIG = {
    "feeds": [
        {"name": "연합뉴스 최신", "url": "https://www.yna.co.kr/rss/news.xml", "limit": 5},
        {"name": "Hacker News", "url": "https://news.ycombinator.com/rss", "limit": 5},
    ],
    "briefing_dir": "briefings",
    "index": "data/index.json",
}


def load_config(path: str | Path = "config.json") -> dict:
    """config.json이 있으면 읽고, 없으면 기본값을 쓴다. 누락 키는 기본값으로 채운다."""
    config = dict(DEFAULT_CONFIG)
    p = Path(path)
    if p.exists():
        config.update(json.loads(p.read_text(encoding="utf-8")))
    return config


def item_to_document(item: FeedItem) -> Document:
    """수집 항목을 지식 베이스 문서로 변환한다 (제목+요약을 본문으로)."""
    text = f"{item.title}\n\n{item.summary}".strip()
    return Document(
        doc_id=_make_doc_id(item.link or item.title, text),
        source=item.link or item.feed_name,
        text=text,
        metadata={"feed": item.feed_name, "published": item.published},
    )


def index_items(index: Index, results: list[FeedResult]) -> int:
    """수집 항목을 인덱스에 추가하고, 새로 추가된 문서 수를 반환한다."""
    added = 0
    for result in results:
        for item in result.items:
            doc = item_to_document(item)
            chunks = chunk_document(doc)
            if chunks and chunks[0].chunk_id not in index.chunks:
                added += 1
            index.add_all(chunks)
    return added


def render_briefing(date_str: str, results: list[FeedResult], stats: dict) -> str:
    """브리핑 마크다운 본문을 만든다."""
    lines = [f"# 아침 브리핑 — {date_str}", ""]

    for result in results:
        lines.append(f"## {result.feed_name}")
        lines.append("")
        if result.error:
            lines.append(f"- (수집 실패: {result.error})")
        elif not result.items:
            lines.append("- (새 항목 없음)")
        else:
            for item in result.items:
                title = item.title
                entry = f"- [{title}]({item.link})" if item.link else f"- {title}"
                lines.append(entry)
                if item.summary:
                    lines.append(f"  - {item.summary[:150]}")
        lines.append("")

    lines.append("## 지식 베이스 현황")
    lines.append("")
    lines.append(f"- 전체 청크: {stats['total_chunks']}개")
    lines.append(f"- 오늘 새로 수집·인덱싱된 문서: {stats['added_today']}건")
    lines.append("")
    return "\n".join(lines)


def generate_briefing(date_str: str, config: dict) -> Path:
    """수집 → 인덱싱 → 브리핑 파일 생성까지 한 번에 실행하고 파일 경로를 반환한다."""
    results = collect_feeds(config["feeds"])

    index_path = Path(config["index"])
    index = Index.load(index_path) if index_path.exists() else Index()
    added = index_items(index, results)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index.save(index_path)

    stats = {"total_chunks": len(index.chunks), "added_today": added}
    text = render_briefing(date_str, results, stats)

    briefing_dir = Path(config["briefing_dir"])
    briefing_dir.mkdir(parents=True, exist_ok=True)
    output = briefing_dir / f"{date_str}.md"
    output.write_text(text, encoding="utf-8")
    return output
