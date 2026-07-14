"""옵시디언 수집기 테스트."""

import tempfile
import unittest
from pathlib import Path

from pipeline.obsidian import clean_note, load_vault

NOTE = """---
tags: [씨앗, 미용]
created: 2026-07-14
---
# 공간의 의미

[[숱치기]]는 결국 [[공간 만들기|공간]]이다.
![[두피사진.png]]
"""


class TestCleanNote(unittest.TestCase):
    def test_strips_frontmatter_and_links(self):
        text = clean_note(NOTE)
        self.assertNotIn("tags:", text)
        self.assertNotIn("[[", text)
        self.assertNotIn("![[", text)
        self.assertIn("숱치기는 결국 공간이다.", text)
        self.assertTrue(text.startswith("# 공간의 의미"))


class TestLoadVault(unittest.TestCase):
    def test_skips_system_dirs_and_adds_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".obsidian").mkdir()
            (root / ".obsidian" / "config.md").write_text("설정", encoding="utf-8")
            (root / "노트폴더").mkdir()
            (root / "노트폴더" / "내생각.md").write_text("본문입니다", encoding="utf-8")
            docs = list(load_vault(root))
            self.assertEqual(len(docs), 1)
            self.assertEqual(docs[0].metadata["note"], "내생각")
            self.assertTrue(docs[0].text.startswith("# 내생각"))
            self.assertTrue(docs[0].source.startswith("obsidian:"))

    def test_missing_path_raises(self):
        with self.assertRaises(FileNotFoundError):
            list(load_vault("/없는/경로/vault"))


if __name__ == "__main__":
    unittest.main()
