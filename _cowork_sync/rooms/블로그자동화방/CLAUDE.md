# 이 방은 「블로그자동화방」이다

> 형이 열어준 제목이 정본이다.

## 역할: 업무실 — 네이버 블로그 자동화

| 하는 일 | 안 하는 일 |
|---|---|
| 네이버 블로그 원고 작성 | 영상 |
| 임시저장 자동화 | 인스타 |
| 블로그 발행 | 만화 |

## 자주 쓰는 명령어

```bash
# 블로그 게이트
python3 scripts/blog_gate.py <원고.md>

# 블로그 원고 생성
python3 scripts/naver_draft.py <주제>

# 임시저장
python3 scripts/naver_save.py <원고.md>

# 발행
python3 scripts/naver_publish.py <원고.md>
```

## 산출물 경로

| 용도 | 경로 |
|---|---|
| 원고 대기 | `_blog_queue/` |
| 발행 잡 | `_publish_jobs/blog*` |
| 블로그 콘텐츠 | `content/블로그/` |

## 수정 가능 파일

| 파일 | 용도 |
|---|---|
| `_state/rooms/블로그자동화방.json` | 내 상태 |
| `scripts/naver_*.py` | 블로그 스크립트 |
| `_blog_queue/` | 원고 대기열 |

## 금지

- 영상/인스타/만화 (→ 각 방)
- `git reset --hard`
## 보고 규율

작업 끝나면 `_ROOMS_LOG.md`에 한 줄 남긴다:
```
- `MM-DD HH:MM` **블로그자동화방** — 무슨 작업. 산출물 경로. 다음 상태.
```


---
## 연동 상태 (2026-08-14 확인)
- ✅ 블로그 게이트: `scripts/blog_gate.py`
- 📂 원고: `_blog_queue/`
- 📂 산출물: `content/blog/`

## 해놓은 일 (최근)
- 블로그 게이트 스크립트 생성

## 🔒 공유 자원 (읽기만)
- secrets/, scripts/, CLAUDE.md, knowledge/ 규격 — **수정 금지**
- 설정 바꿔야 하면 → 전략실에 요청

## 설정 변경 요청
`_cowork_sync/요청큐.md`에 한 줄 추가:
```
- [방이름] 요청 내용 (급함/보통)
```

## 수정 가능 범위
| 폴더 | 용도 |
|---|---|
| `content/blog/` | 블로그 원고 |
| `_blog_queue/` | 발행 대기열 |
| `_terminal_inbox/` | 작업 요청 |
| `_state/rooms/블로그자동화방.json` | 내 상태 |
| `_ROOMS_LOG.md` | 작업 로그 (추가만) |
