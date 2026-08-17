# 만화연재방  ·  코드 `M`

> **이 방의 진입점.** 방이 리뉴얼돼도(채팅 기억 0) 이 문서부터 읽으면 이어받는다.

## 하는 일
미용만화 「결이 이야기」 연재

## 착수 전 4줄 (예외 없음)
1. `_ROOMS.md` — 방 명부·구조도 **정본**
2. `_strategy/공유규약_전방공통.md` — 전 방 공통
3. `_strategy/만화연재방_전용규약.md` — **이 방 규약**
4. `_locks/active.json` + `knowledge/방_공유_작업로그.md` — 다른 방이 지금 뭘 하나. **겹치면 안 한다**

## 내 영역 (여기만 쓴다)
- `_out/만화/` · `_out/연재/`
- `_out/결이*` — 편별 산출 폴더 `_out/결이<편이름>_final__M/` (지금 있는 것: 고데기 · 부스스 · 악성곱슬)
- `content/manga/` (실제 위치) · `content/만화/`
- `content/manifests/만화_*.json` · `content/manifests/결이_*.json`
- `scripts/cards/comic_*` · `scripts/manga_*` · `rooms/만화연재방/`

> **2026-08-17 정정.** 이 목록이 실제와 어긋나 `scripts/room_territory.py` 게이트가 이 방 산출물을 **전부 「영역 밖」으로 튕기고 있었다.**
> 실측: `_out/결이고데기_final__M/c1.png` ❌ · `content/manga/고데기편_구조.json` ❌ · 이 방 매니페스트 `content/manifests/만화_*` 조차 ❌ · 통과하는 건 비어 있는 `_out/만화/` 뿐.
> 원인 ①`_out/결이/` 의 뒤 슬래시가 편별 폴더를 못 잡고 그 폴더 자체도 없음 ②콘텐츠 실제 위치는 `content/만화/` 가 아니라 `content/manga/` ③매니페스트 경로가 영역에 없었음.
> 조치: 이 목록 + 전용규약 표 + `room_territory.py` 의 **만화연재방 줄만** 정정. 다른 방 줄은 손대지 않음(회귀 실측 완료).

영역 밖 파일이 필요하면 → `_strategy/전체_산출물_인덱스.json` 확인 → 없으면 전략실에 요청. 직접 접근 ❌

## 이 방 정본 문서
- `knowledge/규격_나노바나나_매듭화풍_박제.md`
- `knowledge/규격_만화_커버_정본.md`
- `scripts/cards/comic_cover_gate.py`

## 지금 상태 (2026-08-17 실측)

| 편 | 컷 | 산출 경로 | 상태 |
|---|---|---|---|
| ① 악성곱슬 | 6/6 | `_out/결이악성곱슬_final__M/` | 컨택트시트 있음 |
| ② 부스스 | **3/6** (c2·c4·c5) | `_out/결이부스스_final__M/` | **c1·c3·c6 결번** |
| ③ (연재_3편) | — | `_out/연재_3편_최신.png` | 단일 파일 |
| ④ 고데기 | 6/6 | `_out/결이고데기_final__M/` | 구조 JSON = `content/manga/고데기편_구조.json` |

- 발행: 전 편 미발행. 발행은 차노 승인 후.
- 이 방은 `knowledge/방_공유_작업로그.md` 에 기록이 없었다 → 2026-08-17 소급 기록함.

## 끝낼 때 (둘 다)
```bash
# 1) 커밋 — 파일이 남는다
git pull --rebase origin main && git add -A && git commit -m "<한줄>" && git push origin HEAD:main

# 2) 로그 — 뭘 했는지가 남는다  (knowledge/방_공유_작업로그.md 맨 위에 추가만)
# - 2026-MM-DD (만화연재방) ✅/⛔ **한줄요약**
#   - 상세 / 파일 경로
```

## 본진에 시키는 법
```json
// _terminal_inbox/TASK_<이름>.json
{"room": "만화연재방", "task": "실행할 명령 또는 지시", "timeout": 30}
```
디스패처가 5초마다 물어간다. ⚠️ `status: done` 은 증거가 아니다 — 산출 파일·로그·permalink 중 하나를 **실측**하고 보고한다.

---
*정본: `_ROOMS.md` · 규약: `_strategy/만화연재방_전용규약.md`*
