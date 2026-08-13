# 낙타자막인스타 — 인스타/스레드 콘텐츠

> **필독: [공통_역량_규약.md](../공통_역량_규약.md)**

## 🔌 연동 현황 (2026-08-14 확인 완료)

| 서비스 | 상태 | 명령어 |
|---|---|---|
| 인스타 릴스 | ✅ | `python3 -c "from shorts.upload_instagram import *; upload_reel('영상.mp4', '캡션', load_credentials('secrets/instagram.json'))"` |
| 인스타 사진 | ✅ | `python3 -c "from shorts.upload_instagram import *; upload_photo('URL', '캡션', load_credentials('secrets/instagram.json'))"` |
| 스레드 | ✅ | `python3 shorts/threads.py "텍스트"` |
| Gemini 이미지 | ✅ | `python3 scripts/gemini_image.py "프롬프트" output.png` |

**"인스타 발행 못한다" = 거짓말. 토큰 있고 스크립트 있다.**

## 업로드 스크립트

```bash
# 인스타그램
python3 shorts/upload_instagram.py <video_path>

# 스레드
python3 shorts/threads.py <content>
```

## 토큰 위치

- `secrets/instagram.json`
- `secrets/threads.json`

토큰 없으면 드라이브 `앳나운_영상/`에서 복사.

---

## 이미지 생성

```bash
# 카드뉴스/이미지 생성
python3 scripts/gemini_image.py "프롬프트" output.png
```
