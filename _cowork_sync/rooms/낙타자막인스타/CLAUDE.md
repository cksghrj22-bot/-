# 이 방은 「낙타자막인스타」다

> 형이 열어준 제목이 정본이다.

## 역할: 업무실 — 인스타·스레드 실행

| 하는 일 | 안 하는 일 |
|---|---|
| ①낙타 자막바 카드 제작 | 유튜브 쇼츠 |
| ③에이엠톤 사진카드 | 만화 카드 |
| ④스레드 게시 | 블로그 |
| 인스타 발행 | 전사 상황판 |

## 방코드: `N`

## 자주 쓰는 명령어

```bash
# 낙타 카드 렌더
python3 scripts/cards/render_exercise_nakta_6_v2.py

# 낙타 게이트 (검수)
python3 scripts/cards/nakta_gate.py <폴더>

# 에이엠톤 렌더
python3 scripts/cards/render_amtone.py

# 인스타 업로드
python3 shorts/upload_instagram.py <이미지>

# 스레드 업로드
python3 shorts/threads.py <이미지>
```

## 규격 정본

| 용도 | 경로 |
|---|---|
| 낙타 자막바 | `knowledge/규격_자막_두_체계_분리.md` |
| 에이엠톤 두 줄 | `knowledge/규격_에이엠톤식_좌하단두줄_v1.md` |
| 카드 폼 | `knowledge/규격_결이연재_카드폼.md` |

## 산출물 경로

| 용도 | 경로 |
|---|---|
| 낙타 카드 | `_out/cards/` |
| 에이엠톤 | `_out/amtone/` |
| 발행 대기 | `_publish_jobs/` |

## 수정 가능 파일

| 파일 | 용도 |
|---|---|
| `_state/rooms/낙타자막인스타.json` | 내 상태 |
| `scripts/cards/render_*_nakta_*.py` | 낙타 렌더러 |
| `scripts/cards/render_amtone.py` | 에이엠톤 렌더러 |

## 금지

- 쇼츠 렌더 (→ 유튜브쇼츠방)
- 만화 카드 (→ 만화연재방)
- `git reset --hard`
## 보고 규율

작업 끝나면 `_ROOMS_LOG.md`에 한 줄 남긴다:
```
- `MM-DD HH:MM` **낙타자막인스타** — 무슨 작업. 산출물 경로. 다음 상태.
```

