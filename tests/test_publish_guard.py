"""publishAt 안전장치 — 과거 시각이면 즉시공개 사고를 막고자 예외 (이찬호 2026-07-19)."""
import unittest
from datetime import datetime, timedelta, timezone

from shorts.upload_youtube import build_metadata


class TestPublishGuard(unittest.TestCase):
    def test_past_publish_at_raises(self):
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        with self.assertRaises(ValueError):
            build_metadata("제목", publish_at=past)

    def test_future_publish_at_ok(self):
        fut = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m = build_metadata("제목", publish_at=fut)
        self.assertEqual(m["status"]["privacyStatus"], "private")
        self.assertEqual(m["status"]["publishAt"], fut)

    def test_no_publish_at_is_private_default(self):
        m = build_metadata("제목")
        self.assertEqual(m["status"]["privacyStatus"], "private")
        self.assertNotIn("publishAt", m["status"])

    def test_bad_format_raises(self):
        with self.assertRaises(ValueError):
            build_metadata("제목", publish_at="내일오전")


if __name__ == "__main__":
    unittest.main()
