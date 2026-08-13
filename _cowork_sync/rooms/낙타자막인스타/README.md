# 낙타자막인스타 — 인스타/스레드 콘텐츠

> **필독: [공통_역량_규약.md](../공통_역량_규약.md)**

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
