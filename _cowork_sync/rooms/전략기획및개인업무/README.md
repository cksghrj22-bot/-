# 전략기획 및 개인업무

> **필독: [공통_역량_규약.md](../공통_역량_규약.md)**

## 🔌 연동 현황 (2026-08-14 확인 완료)

| 서비스 | 상태 | 명령어 |
|---|---|---|
| 노션 | ✅ | MCP `notion-*` |
| 캘린더 | ✅ | MCP `Google_Calendar__*` |
| 메일 | ✅ | MCP `Gmail__*` |
| 드라이브 | ✅ | `python3 shorts/gdrive.py` |
| 브라우저 | ✅ | MCP `claude-in-chrome__*` |

**"설정 못 바꾼다" = 거짓말. 브라우저로 직접 들어가면 된다.**

## 할 수 있는 것

| 작업 | 방법 |
|---|---|
| 노션 검색/수정 | MCP `notion-*` |
| 캘린더 확인 | MCP `Google_Calendar` |
| 메일 확인 | MCP `Gmail` |
| 드라이브 정리 | `python3 shorts/gdrive.py` |
| 지식 검색 | `python3 -m pipeline search "키워드"` |

## 브라우저 자동화

원격 설정 변경, API 연결 등 브라우저로 가능.

```bash
mcp__claude-in-chrome__tabs_create_mcp url="https://..."
mcp__claude-in-chrome__read_page
mcp__claude-in-chrome__computer action="click" coordinate=[x, y]
```
