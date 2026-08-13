# 블로그자동화방 — 블로그/매거진 콘텐츠

> **필독: [공통_역량_규약.md](../공통_역량_규약.md)**

## 🔌 연동 현황 (2026-08-14 확인 완료)

| 서비스 | 상태 | 명령어 |
|---|---|---|
| Gemini 이미지 | ✅ | `python3 scripts/gemini_image.py "프롬프트" output.png` |
| 노션 발행 | ✅ | MCP `notion-create-pages` |
| 드라이브 | ✅ | `python3 shorts/gdrive.py` |
| 지식 검색 | ✅ | `python3 -m pipeline search "키워드"` |

**"이미지 못 만든다" = 거짓말. Gemini 연결돼있다.**

## 관련 프롬프트

- `prompts/04_매거진_블로그.md`

## 이미지 생성

지식파이프라인 우화 등 삽화 필요하면:

```bash
python3 scripts/gemini_image.py "파이프라인 우화 삽화: 물이 여러 관을 통해 흐르는 모습, 따뜻한 일러스트" output.png
```

## 지식 파이프라인 검색

```bash
python3 -m pipeline search "키워드"
```

---

## 할 수 있는 것

- 블로그 글 생성
- 삽화 이미지 생성 (Gemini)
- 드라이브 업로드
- 노션에 발행
