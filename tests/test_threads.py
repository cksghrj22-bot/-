"""shorts.threads 스레드 발행 모듈 테스트 — 네트워크 없이."""

import json
import tempfile
import unittest
from pathlib import Path

from shorts import threads


class TestSecrets(unittest.TestCase):
    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            threads.load_secrets("secrets/없는파일.json")

    def test_missing_token_raises(self):
        f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump({"user_id": "1"}, f); f.close()
        with self.assertRaises(ValueError):
            threads.load_secrets(f.name)


class TestExtractBody(unittest.TestCase):
    def test_body_after_divider(self):
        md = "# 제목\n- 메타정보\n\n---\n\n본문 첫 줄.\n둘째 줄."
        self.assertEqual(threads.extract_body(md), "본문 첫 줄.\n둘째 줄.")

    def test_no_divider_returns_all(self):
        self.assertEqual(threads.extract_body("그냥 본문"), "그냥 본문")


if __name__ == "__main__":
    unittest.main()
