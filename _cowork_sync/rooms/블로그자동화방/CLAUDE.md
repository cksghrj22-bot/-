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

