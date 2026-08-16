# 차노책출판  ·  코드 `P`

> **이 방의 진입점.** 방이 리뉴얼돼도(채팅 기억 0) 이 문서부터 읽으면 이어받는다.

## 하는 일
에세이 · 기술서 · 어록집 · 사물관찰일기

## 착수 전 4줄 (예외 없음)
1. `_ROOMS.md` — 방 명부·구조도 **정본**
2. `_strategy/공유규약_전방공통.md` — 전 방 공통
3. `_strategy/차노책출판_전용규약.md` — **이 방 규약**
4. `_locks/active.json` + `knowledge/방_공유_작업로그.md` — 다른 방이 지금 뭘 하나. **겹치면 안 한다**

## 내 영역 (여기만 쓴다)
- `_out/책/`
- `content/책/`

영역 밖 파일이 필요하면 → `_strategy/전체_산출물_인덱스.json` 확인 → 없으면 전략실에 요청. 직접 접근 ❌

## 이 방 정본 문서
- `knowledge/차노_보이스.md`
- `knowledge/키워드_지도.md`
- `_obsidian_out/` (차노 날것 코퍼스)

## 끝낼 때 (둘 다)
```bash
# 1) 커밋 — 파일이 남는다
git pull --rebase origin main && git add -A && git commit -m "<한줄>" && git push origin HEAD:main

# 2) 로그 — 뭘 했는지가 남는다  (knowledge/방_공유_작업로그.md 맨 위에 추가만)
# - 2026-MM-DD (차노책출판) ✅/⛔ **한줄요약**
#   - 상세 / 파일 경로
```

## 본진에 시키는 법
```json
// _terminal_inbox/TASK_<이름>.json
{"room": "차노책출판", "task": "실행할 명령 또는 지시", "timeout": 30}
```
디스패처가 5초마다 물어간다. ⚠️ `status: done` 은 증거가 아니다 — 산출 파일·로그·permalink 중 하나를 **실측**하고 보고한다.

---
*정본: `_ROOMS.md` · 규약: `_strategy/차노책출판_전용규약.md`*
