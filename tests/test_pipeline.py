"""파이프라인 단위 테스트 (unittest, 외부 의존성 없음)."""

import tempfile
import unittest
from pathlib import Path

from pipeline.chunk import chunk_document, split_text
from pipeline.index import Index, tokenize
from pipeline.ingest import Document, load_directory, load_file


class TestIngest(unittest.TestCase):
    def test_load_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "note.md"
            p.write_text("# 제목\n\n본문입니다.", encoding="utf-8")
            doc = load_file(p)
            self.assertEqual(doc.source, str(p))
            self.assertIn("본문입니다", doc.text)
            self.assertEqual(doc.metadata["filename"], "note.md")

    def test_load_directory_filters_extensions(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "a.md").write_text("에이", encoding="utf-8")
            (Path(tmp) / "b.bin").write_bytes(b"\x00\x01")
            docs = list(load_directory(tmp))
            self.assertEqual(len(docs), 1)
            self.assertEqual(docs[0].text, "에이")


class TestChunk(unittest.TestCase):
    def test_split_respects_paragraphs(self):
        text = "첫 문단.\n\n둘째 문단.\n\n셋째 문단."
        pieces = split_text(text, max_chars=15, overlap=0)
        self.assertTrue(all(len(p) <= 15 for p in pieces))
        self.assertIn("첫 문단.", pieces[0])

    def test_long_paragraph_overlap(self):
        text = "가" * 100
        pieces = split_text(text, max_chars=40, overlap=10)
        self.assertTrue(all(len(p) <= 40 for p in pieces))
        # 겹침: 앞 조각 끝부분이 다음 조각 시작에 다시 등장
        self.assertEqual(pieces[0][-10:], pieces[1][:10])

    def test_invalid_params(self):
        with self.assertRaises(ValueError):
            split_text("텍스트", max_chars=0)
        with self.assertRaises(ValueError):
            split_text("텍스트", max_chars=10, overlap=10)

    def test_chunk_document_ids(self):
        doc = Document(doc_id="d1", source="s", text="하나.\n\n둘.")
        chunks = chunk_document(doc, max_chars=5, overlap=0)
        self.assertEqual([c.chunk_id for c in chunks], ["d1:0", "d1:1"])


class TestIndex(unittest.TestCase):
    def _build(self):
        index = Index()
        docs = [
            Document(doc_id="d1", source="a.md", text="파이썬 기초: 배우기 쉬운 언어."),
            Document(doc_id="d2", source="b.md", text="러스트는 메모리 안전성이 강점이다."),
            Document(doc_id="d3", source="c.md", text="파이썬으로 데이터 파이프라인을 만든다. 파이썬 파이썬."),
        ]
        for d in docs:
            index.add_all(chunk_document(d))
        return index

    def test_tokenize_korean_english(self):
        self.assertEqual(tokenize("Python 파이썬 3.12!"), ["python", "파이썬", "3", "12"])

    def test_search_ranks_by_relevance(self):
        index = self._build()
        results = index.search("파이썬", top_k=2)
        self.assertEqual(len(results), 2)
        # d3가 '파이썬' 빈도가 더 높아 상위
        self.assertEqual(results[0][0].doc_id, "d3")

    def test_search_no_match(self):
        index = self._build()
        self.assertEqual(index.search("존재하지않는단어"), [])

    def test_save_and_load_roundtrip(self):
        index = self._build()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "index.json"
            index.save(path)
            loaded = Index.load(path)
            self.assertEqual(set(loaded.chunks), set(index.chunks))
            original = index.search("메모리 안전성")[0][0].chunk_id
            restored = loaded.search("메모리 안전성")[0][0].chunk_id
            self.assertEqual(original, restored)


if __name__ == "__main__":
    unittest.main()
