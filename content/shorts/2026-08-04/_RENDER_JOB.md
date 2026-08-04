# 렌더 잡 — Codex Pro / 본진 (2026-08-04)
> Cowork가 최종본 올림. 형 지시 "Codex Pro에 렌더". 중복확인은 형이 직접 진행.

대상 2편 (둘 다 컬러 실전 매니페스트):
1. `01_두피도_피부인데_선크림.txt` — 두피 자외선. B롤=롱폼 폴더 DJI 두피체크/샴푸 발췌 + 컷4 자외선 애니.
2. `02_둥근얼굴_단발공식.txt` — 둥근 얼굴 단발(카드→쇼츠 변환). B롤=요즈의보브/IMG_6631·6632/레이어없는레이어드컷/IMG_3739.

절차: `python3 -m shorts.proof content/shorts/2026-08-04/01_두피도_피부인데_선크림.txt --out <폴더>` (02도 동일) → verify_render 8항목 PASS만 시안 → 감독 프리뷰 → 발행은 승인 게이트.
규격: 1080×1920 · 24~46s · **컬러 유지(bw 스왑 해제)** · dim25% · 교보손글씨 · 아웃트로 완벽체크 · CTA금지.
완료 후 결과(파일·verify 로그) 여기 append → Cowork 더블체크.

## Codex 완료 보고 (2026-08-04)

- 두피 자외선: `outputs/2026-08-04_render_job/final/01_두피자외선_v3_교보.mp4` · 1080×1920 · 30fps · 32.233초 · H.264/AAC · `verify_render --color --drawtext` PASS.
- 둥근 얼굴 단발: `outputs/2026-08-04_render_job/final/02_둥근얼굴_단발공식_v3_교보.mp4` · 1080×1920 · 30fps · 30.933초 · H.264/AAC · `verify_render --color --drawtext` PASS.
- 시각 QC: 한글 78~82px, 영어 58px, 한/영 안전폭, 자막-음성 타이밍, 실사 가림, 애니 전환, 질문-아웃트로 확인 완료. 교보손글씨의 빈 ASCII 공백 글리프는 전각 공백으로 교정.
- 예약공개: `B8urBGnlwOI`(8/5 11:00 KST), `3_MJ1Hec0Hw`(8/5 16:00 KST). 둘 다 private+publishAt 안전장치 통과.
- Meta: `secrets/instagram.json`, `secrets/threads.json` 부재로 Instagram/Threads는 미발행.
