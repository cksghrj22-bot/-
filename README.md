# 지식파이프라인

문서를 수집해 검색 가능한 지식 베이스로 만드는 파이프라인입니다.
외부 의존성 없이 Python 표준 라이브러리만으로 동작합니다 (Python 3.10+).

## 구조

```
pipeline/
  ingest.py    # 수집: 파일/디렉터리 → Document
  chunk.py     # 분할: Document → Chunk (문단 우선, 겹침 지원)
  index.py     # 인덱싱/검색: TF-IDF 역색인 (한글/영문 토큰화)
  __main__.py  # CLI
tests/
  test_pipeline.py
```

## 사용법

```bash
# 문서 추가 (파일 또는 디렉터리)
python -m pipeline add ./docs

# 검색
python -m pipeline search "파이프라인" --top-k 5
```

인덱스는 기본적으로 `data/index.json`에 저장됩니다 (`--index`로 변경 가능).

## 테스트

```bash
python -m unittest discover -s tests -v
```

## 로드맵

- [ ] URL/웹 페이지 수집기
- [ ] 임베딩 기반 시맨틱 검색 (선택적 의존성)
- [ ] 증분 업데이트 / 문서 삭제
