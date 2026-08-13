# 교육디렉터방 — 교육 콘텐츠 기획

> **필독: [공통_역량_규약.md](../공통_역량_규약.md)**

## 🔌 연동 현황 (2026-08-14 확인 완료)

| 서비스 | 상태 | 명령어 |
|---|---|---|
| Gemini 이미지 | ✅ | `python3 scripts/gemini_image.py` |
| 드라이브 | ✅ | `python3 shorts/gdrive.py` |
| 노션 | ✅ | MCP `notion-*` |
| 지식 검색 | ✅ | `python3 -m pipeline search` |

**"이미지/도식 못 만든다" = 거짓말. 다 연결돼있다.**

## 역할

- 교육 시스템 설계
- 교육 콘텐츠 제작
- 성장타워 구조 설계

## 관련 자료 위치

- `content/교육/` — 교육 산출물
- `knowledge/00_교육디렉터실_정본목차_여기부터.md` — 정본

## 할 수 있는 것

| 작업 | 방법 |
|---|---|
| 도식/다이어그램 | HTML 아티팩트 생성 |
| 이미지 생성 | `python3 scripts/gemini_image.py` |
| 드라이브 검색 | MCP `search_files` |
| 기존 자료 검색 | `python3 -m pipeline search` |
