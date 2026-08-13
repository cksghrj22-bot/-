# 유튜브쇼츠방 — 쇼츠 제작 + 리뷰

> **필독: [공통_역량_규약.md](../공통_역량_규약.md)**

## 🔌 연동 현황 (2026-08-14 확인 완료)

| 서비스 | 상태 | 명령어 |
|---|---|---|
| 유튜브 업로드 | ✅ | `python3 shorts/upload_youtube.py` |
| 인스타 릴스 | ✅ | `shorts/upload_instagram.py` |
| 스레드 | ✅ | `shorts/threads.py` |
| 드라이브 | ✅ | `shorts/gdrive.py` |
| TTS | ✅ | `scripts/tts_fish.py` |

**"발행 못한다" = 거짓말. 위 명령어 실행하면 된다.**

## 핵심 규약

1. **수치_체크리스트_정본.md 안 돌리면 렌더 금지**
2. 싱크 ≤ 0.15초 / 컷 ≥ 2.2초 / 아웃트로 ≥ 2.2초

## 영상 리뷰 방법 (싱크/컷 확인)

### 1. 드라이브에서 영상 다운로드
```bash
python3 shorts/gdrive.py download <file_id> /tmp/review.mp4
```

### 2. 메타데이터 확인
```bash
ffprobe -v quiet -print_format json -show_format -show_streams /tmp/review.mp4
```

### 3. 프레임 추출 (시각적 확인)
```bash
mkdir -p /tmp/frames
ffmpeg -i /tmp/review.mp4 -vf "fps=1" -q:v 2 /tmp/frames/frame_%03d.jpg
```

### 4. 특정 구간 캡쳐
```bash
ffmpeg -i /tmp/review.mp4 -ss 00:00:05 -frames:v 1 /tmp/check.jpg
```

### 5. 브라우저로 직접 재생
```
mcp__claude-in-chrome__navigate → 드라이브 URL
```

---

## 수치 체크리스트 기준

| 항목 | 기준 |
|---|---|
| 컷 최소 | **2.2초** |
| 컷 최대 | 6.0초 |
| 아웃트로 | **2.2초 이상** |
| 싱크 평균 | ≤ 0.15초 |
| 싱크 최대 | ≤ 0.30초 |
| 자막 먼저 | +0.20초까지 |
| 자막 늦음 | **-0.10초까지** |

---

## 대본 → 렌더 플로우

1. 대본 작성 (`prompts/02_쇼츠_대량생산.md`)
2. 나레이션 라임 적용 (`prompts/06_나레이션_라임.md`)
3. 체크리스트 통과 (`수치_체크리스트_정본.md`)
4. Codex 렌더 요청 (수동 dispatch 금지)
5. 렌더 후 영상 리뷰

---

## 스크립트 위치

- `shorts/gdrive.py` — 드라이브 업/다운로드
- `shorts/subtitle.py` — ASS 자막 생성
- `shorts/render.py` — ffmpeg 렌더
