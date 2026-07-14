"""수집 단계: RSS/Atom 피드에서 새 항목을 가져온다. 표준 라이브러리만 사용."""

from __future__ import annotations

import re
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

_ATOM_NS = "{http://www.w3.org/2005/Atom}"
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


@dataclass
class FeedItem:
    """피드에서 수집한 항목 한 건."""

    feed_name: str
    title: str
    link: str
    summary: str = ""
    published: str = ""


def _clean(text: str | None) -> str:
    if not text:
        return ""
    return _WS_RE.sub(" ", _TAG_RE.sub(" ", text)).strip()


def parse_feed(xml_text: str, feed_name: str) -> list[FeedItem]:
    """RSS 2.0 또는 Atom XML을 FeedItem 리스트로 파싱한다."""
    root = ET.fromstring(xml_text)
    items: list[FeedItem] = []

    # RSS 2.0: <item><title/><link/><description/><pubDate/>
    for node in root.iter("item"):
        items.append(
            FeedItem(
                feed_name=feed_name,
                title=_clean(node.findtext("title")),
                link=(node.findtext("link") or "").strip(),
                summary=_clean(node.findtext("description")),
                published=_clean(node.findtext("pubDate")),
            )
        )

    # Atom: <entry><title/><link href/><summary|content/><updated/>
    for node in root.iter(f"{_ATOM_NS}entry"):
        link = ""
        for l in node.findall(f"{_ATOM_NS}link"):
            if l.get("rel") in (None, "alternate"):
                link = l.get("href", "")
                break
        items.append(
            FeedItem(
                feed_name=feed_name,
                title=_clean(node.findtext(f"{_ATOM_NS}title")),
                link=link,
                summary=_clean(
                    node.findtext(f"{_ATOM_NS}summary")
                    or node.findtext(f"{_ATOM_NS}content")
                ),
                published=_clean(
                    node.findtext(f"{_ATOM_NS}updated")
                    or node.findtext(f"{_ATOM_NS}published")
                ),
            )
        )

    return [i for i in items if i.title]


def fetch_feed(url: str, feed_name: str, timeout: int = 20) -> list[FeedItem]:
    """URL에서 피드를 내려받아 파싱한다."""
    request = urllib.request.Request(
        url, headers={"User-Agent": "knowledge-pipeline/0.1 (+rss collector)"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        xml_text = response.read().decode("utf-8", errors="replace")
    return parse_feed(xml_text, feed_name)


@dataclass
class FeedResult:
    """피드 하나의 수집 결과 (성공 항목 또는 오류 메시지)."""

    feed_name: str
    items: list[FeedItem] = field(default_factory=list)
    error: str = ""


def collect_feeds(feeds: list[dict]) -> list[FeedResult]:
    """설정된 피드 목록을 순회 수집한다. 개별 피드 실패는 전체를 멈추지 않는다.

    feeds 항목 형식: {"name": str, "url": str, "limit": int(선택, 기본 5)}
    """
    results: list[FeedResult] = []
    for feed in feeds:
        name = feed["name"]
        limit = int(feed.get("limit", 5))
        try:
            items = fetch_feed(feed["url"], name)[:limit]
            results.append(FeedResult(feed_name=name, items=items))
        except Exception as exc:  # noqa: BLE001 - 피드 하나가 죽어도 브리핑은 나가야 한다
            results.append(FeedResult(feed_name=name, error=str(exc)))
    return results
