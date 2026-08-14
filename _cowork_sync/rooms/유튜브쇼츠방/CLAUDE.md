# 이 방은 「유튜브쇼츠방」이다

> 형이 열어준 제목이 정본이다.

## 역할: 업무실 — 쇼츠·AI일기 렌더

| 하는 일 | 안 하는 일 |
|---|---|
| 유튜브 쇼츠 렌더링 | 인스타 카드 |
| AI일기 영상 | 낙타 자막바 |
| ②쇼츠 하단자막 (ASS) | 에이엠톤 |
| 쇼츠 발행 | 만화 |

## 방코드: `A`

## 자주 쓰는 명령어

```bash
# 쇼츠 렌더
python3 -m shorts.render <잡.json>

# 쇼츠 게이트 (검수 + 스샷시트)
python3 scripts/shorts_gate.py <영상.mp4>

# 유튜브 업로드
python3 shorts/upload_youtube.py <영상>

# TTS 생성
python3 shorts/tts.py <대본>
```

## 규격 정본

| 용도 | 경로 |
|---|---|
| 보완게이트 | `pipeline/보완_정본.md` |
| 제작규격 | `knowledge/제작규격_정본.md` |
| 자막 체계 | `knowledge/규격_자막_두_체계_분리.md` |

## 자막 규격

- 쇼츠 하단자막: 1080×1920, y=1436 (한글), y=1500 (영어)
- AI일기 분할: y=1200 (한글), y=1260 (영어)
- 길이: 26~59초

## 산출물 경로

| 용도 | 경로 |
|---|---|
| 렌더 결과 | `_jobs/_done/` |
| 프리뷰 | `_tmp/preview/` |
| 발행 대기 | `_publish_jobs/` |

## 수정 가능 파일

| 파일 | 용도 |
|---|---|
| `_state/rooms/유튜브쇼츠방.json` | 내 상태 |
| `shorts/*.py` | 쇼츠 스크립트 |
| `scripts/shorts_gate.py` | 쇼츠 게이트 |

## 금지

- 인스타 카드 (→ 낙타자막인스타)
- 만화 카드 (→ 만화연재방)
- `git reset --hard`
## 보고 규율

작업 끝나면 `_ROOMS_LOG.md`에 한 줄 남긴다:
```
- `MM-DD HH:MM` **유튜브쇼츠방** — 무슨 작업. 산출물 경로. 다음 상태.
```


---
## 연동 상태 (2026-08-14 확인)
- ✅ 유튜브 업로드: `secrets/youtube.json`
- ✅ 일레븐랩스 TTS: `secrets/elevenlabs.json`
- ✅ 쇼츠 게이트: `scripts/shorts_gate.py`
- ✅ 드라이브 업로드: `shorts/gdrive.py`
- 📂 클립풀: `_clips_pool/senior/`, `_clips_pool/ai일기/`
- 📂 산출물: `_out/`, `_jobs/_done/`

## 해놓은 일 (최근)
- S1_senior_v5.mp4 게이트 통과 (2026-08-14)
- AI일기 ep1 렌더
- 게이트 자동 로그 기능 추가 (`_ROOMS_LOG.md`)

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
| `_out/` | 렌더 산출물 |
| `content/shorts/` | 쇼츠 대본/매니페스트 |
| `_clips_pool/` | 클립 소스 |
| `_terminal_inbox/` | 작업 요청 |
| `_state/rooms/유튜브쇼츠방.json` | 내 상태 |
| `_ROOMS_LOG.md` | 작업 로그 (추가만) |
