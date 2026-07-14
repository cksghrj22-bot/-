"""수집기/브리핑 단위 테스트 (네트워크 없이 샘플 XML로 검증)."""

import tempfile
import unittest
from pathlib import Path

from pipeline.briefing import (
    index_items,
    item_to_document,
    load_config,
    render_briefing,
)
from pipeline.collect import FeedItem, FeedResult, parse_feed
from pipeline.index import Index

RSS_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>테스트 피드</title>
  <item>
    <title>첫 번째 뉴스</title>
    <link>https://example.com/1</link>
    <description>&lt;p&gt;본문   요약&lt;/p&gt;</description>
    <pubDate>Mon, 14 Jul 2026 07:00:00 +0900</pubDate>
  </item>
  <item>
    <title>두 번째 뉴스</title>
    <link>https://example.com/2</link>
  </item>
</channel></rss>"""

ATOM_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>아톰 피드</title>
  <entry>
    <title>아톰 항목</title>
    <link rel="alternate" href="https://example.com/atom/1"/>
    <summary>아톰 요약</summary>
    <updated>2026-07-14T07:00:00Z</updated>
  </entry>
</feed>"""


class TestParseFeed(unittest.TestCase):
    def test_rss(self):
        items = parse_feed(RSS_SAMPLE, "테스트")
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].title, "첫 번째 뉴스")
        self.assertEqual(items[0].link, "https://example.com/1")
        # HTML 태그 제거 + 공백 정규화
        self.assertEqual(items[0].summary, "본문 요약")

    def test_atom(self):
        items = parse_feed(ATOM_SAMPLE, "아톰")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].link, "https://example.com/atom/1")
        self.assertEqual(items[0].summary, "아톰 요약")


class TestBriefing(unittest.TestCase):
    def _results(self):
        return [
            FeedResult(
                feed_name="뉴스",
                items=[FeedItem(feed_name="뉴스", title="제목A", link="https://a", summary="요약A")],
            ),
            FeedResult(feed_name="죽은피드", error="timeout"),
        ]

    def test_item_to_document(self):
        item = FeedItem(feed_name="뉴스", title="제목", link="https://a", summary="요약")
        doc = item_to_document(item)
        self.assertEqual(doc.source, "https://a")
        self.assertIn("제목", doc.text)
        self.assertIn("요약", doc.text)

    def test_index_items_dedup(self):
        index = Index()
        results = self._results()
        added_first = index_items(index, results)
        added_second = index_items(index, results)
        self.assertEqual(added_first, 1)
        self.assertEqual(added_second, 0)  # 같은 항목 재수집 시 중복 추가 없음

    def test_render_briefing(self):
        text = render_briefing("2026-07-14", self._results(), {"total_chunks": 3, "added_today": 1})
        self.assertIn("# 아침 브리핑 — 2026-07-14", text)
        self.assertIn("[제목A](https://a)", text)
        self.assertIn("수집 실패: timeout", text)
        self.assertIn("전체 청크: 3개", text)

    def test_load_config_defaults_and_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = load_config(Path(tmp) / "없는파일.json")
            self.assertIn("feeds", missing)
            p = Path(tmp) / "config.json"
            p.write_text('{"briefing_dir": "out"}', encoding="utf-8")
            overridden = load_config(p)
            self.assertEqual(overridden["briefing_dir"], "out")
            self.assertIn("feeds", overridden)  # 누락 키는 기본값 유지


if __name__ == "__main__":
    unittest.main()
