# 인스타 업로드 준비 (2026-07-22) — 카드 캐러셀 2종

## 상태
- ✅ 카드 최종 렌더 OK(이찬호 승인 2026-07-22). 캡션 2종 작성 완료(이 폴더).
- ⛔ 자동발행 블로커 = **Meta 토큰**(secrets/instagram.json: access_token·ig_user_id) + **공개 이미지 URL**.

## 두 가지 경로
### A. 지금 바로 가능 — 손 업로드(폰)
1. 이미지 저장: 커트편 6장(mixd_1~6) · 긴얼굴 7장(lfd_1~7) — 채팅/드라이브에서.
2. 인스타 앱 → 새 게시물 → 여러 장 선택(순서대로) → 캡션 붙여넣기(위 .md).
※ IG 캐러셀 API는 공개URL·비즈니스계정 필요해 까다로움 → 폰 수동이 가장 확실.

### B. 자동발행 — 토큰 들어오면
- 코드: `shorts/upload_instagram.py` `upload_carousel(image_urls, caption, creds)` (공개 이미지 URL 2~10장).
- 필요: ① secrets/instagram.json(access_token·ig_user_id) ② 카드 PNG를 공개 URL로(드라이브 공개링크 등).
- 발사(예): 이미지 공개URL 리스트 + 위 캡션 → upload_carousel 호출 러너.

## 이미지 재생성(언제든)
- 커트편: `python3 -m shorts.cardposter out/mixd.png --spec mixdetail`
- 긴얼굴: `python3 -m shorts.cardposter out/lfd.png --spec longfacedetail`
