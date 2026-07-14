"""인덱싱/검색 단계: TF-IDF 기반 역색인. 표준 라이브러리만 사용한다."""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path

from .chunk import Chunk

# 한글/영문/숫자 토큰 (영문은 소문자 정규화)
_TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣]+")


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


class Index:
    """청크들을 담아 TF-IDF 코사인 유사도로 검색하는 인덱스."""

    def __init__(self) -> None:
        self.chunks: dict[str, Chunk] = {}
        self.postings: dict[str, dict[str, int]] = defaultdict(dict)  # term -> {chunk_id: tf}

    def add(self, chunk: Chunk) -> None:
        if chunk.chunk_id in self.chunks:
            return
        self.chunks[chunk.chunk_id] = chunk
        for term, tf in Counter(tokenize(chunk.text)).items():
            self.postings[term][chunk.chunk_id] = tf

    def add_all(self, chunks: list[Chunk]) -> None:
        for c in chunks:
            self.add(c)

    def _idf(self, term: str) -> float:
        df = len(self.postings.get(term, {}))
        if df == 0:
            return 0.0
        return math.log(1 + len(self.chunks) / df)

    def search(self, query: str, top_k: int = 5) -> list[tuple[Chunk, float]]:
        """질의와의 TF-IDF 점수 상위 top_k 청크를 반환한다."""
        query_terms = Counter(tokenize(query))
        scores: dict[str, float] = defaultdict(float)
        for term, q_tf in query_terms.items():
            idf = self._idf(term)
            if idf == 0.0:
                continue
            for chunk_id, tf in self.postings[term].items():
                scores[chunk_id] += q_tf * (1 + math.log(tf)) * idf

        ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))[:top_k]
        return [(self.chunks[cid], score) for cid, score in ranked]

    # --- 영속화 ---

    def save(self, path: str | Path) -> None:
        payload = {
            "chunks": [asdict(c) for c in self.chunks.values()],
        }
        Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "Index":
        index = cls()
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        index.add_all([Chunk(**c) for c in payload["chunks"]])
        return index
