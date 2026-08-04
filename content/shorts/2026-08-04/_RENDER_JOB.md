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

---
## ⚙️ 렌더 지정 (2026-08-04 이찬호 확정 — 되돌리지 말 것)
- **프리셋 = 컬러 확정** (매니페스트 지정 우선. 흑백으로 되돌리지 않는다. 근거: 결정사항_대장 '프리셋=매니페스트 우선'.)
- **02편 B롤 위치 = 드라이브 「코드방_B롤_인트레이」** (ID `1MBvVanqFgvBjk7hS2wjOaYN6oiaoBtlO`, anyone-reader). 일반 소스폴더 아님 → 인트레이 최신 클립에서 매칭.
- BGM = 앳나운_영상 BGM 폴더 지정곡.
- 발행·예약 자동 금지 = 감독 프리뷰 게이트 유지.

## 감독 프리뷰 재렌더 결과 (2026-08-04 · 발행 금지 지시)

- 실행: `python3 -m shorts.proof content/shorts/2026-08-04 --only 01|02 --preset style_preset_mind --grade warm_film ...`로 각 대본을 분리 렌더. 컬러 유지·dim 25% 임시 설정, 기존 실사+애니 베이스와 `bgm_piano_long.mp3` 재사용.
- 두피 자외선: `outputs/2026-08-04_supervisor_preview_proof/01/01_두피도_피부인데_선크림_감독프리뷰.mp4` · 1080×1920 · 30fps · 31.300초 · H.264/AAC · 7,718,666 bytes.
- 둥근 얼굴 단발: `outputs/2026-08-04_supervisor_preview_proof/02/02_둥근얼굴_단발공식_감독프리뷰.mp4` · 1080×1920 · 30fps · 31.533초 · H.264/AAC · 11,340,081 bytes.
- 게이트: 각 ASS 기준 `python3 -m shorts.verify_render <mp4> <ass> --color --drawtext` **8항목 PASS**. 전체 테스트 171 PASS(2 skipped).
- 이중 QC: 컨택트시트로 제목 두 줄 위치·본문 14자 안전폭·컬러·dim·실사/애니 전환·마지막 질문·2.6초 아웃트로 확인. 교보손글씨는 macOS libass 폴백을 피하려고 repo fontfile 직접 렌더.
- 상태: **감독 프리뷰 시안 — 발행본 아님.** 이번 작업에서 Drive 업로드·YouTube/Instagram/Threads 업로드·예약·발행 전부 실행하지 않음. 기존 예약 내역에도 변경 없음.

---
## ▶ 새 렌더잡 (2026-08-04 저녁 · Cowork) — status: 대기
> 형 지시: 자외선편과 냄새편은 별개 개념 → 둘 다 감. "B롤만 잘 써." codex exec로 렌더(나이틀리 트리거). **발행·예약 절대 금지, 시안까지만.** 착수 전 git pull + claim(진행중 표시).

대상:
- `01_두피도_피부인데_선크림.txt` — **재렌더**. ⚠️이전본 문제: 글자 화면 밖 벗어남 + 억지 애니. 수정: **자막 각 줄 안전폭 엄수(화면 밖 금지)**, **애니 빼고 실사 두피(롱폼 DJI 정수리·두피체크) 위주**. 텍스트는 그대로.
- `03_두피_냄새_말리는법.txt` — **신규 렌더**. B롤=롱폼 두피 DJI 샴푸·드라이·클로즈업. 실사 위주.
- `02_둥근얼굴_단발공식.txt` — 자막 화면 밖 벗어남 있으면 **자막만 안전폭 재렌더**(내용 유지). B롤=중단발 실사(요즈의보브/IMG_6631·6632/레이어드컷/IMG_3739).

공통 규격: 1080×1920 · 컬러 · dim25% · 교보손글씨(폴백 금지) · **자막 안전폭·2줄** · 아웃트로 완벽체크 · CTA금지 · verify_render PASS만.
완료 후 결과 여기 append. 발행·예약은 감독 판정 후.

## 📸 미리보기 규약 (Cowork가 여기서 띄우려고)
- 렌더 시안마다 **컨택트시트 PNG**(대표 프레임 6~9장 격자, 자막 보이게)를 `outputs/.../contact/` 에 생성하고 **트렁크에 커밋**(작은 PNG만).
- full mp4는 드라이브 `_최신_바로보기/`에 두고 링크만.
- → Cowork가 컨택트시트 pull해서 감독에게 여기(Cowork)서 띄우고, full은 드라이브 링크로. (영상 원본은 git에 넣지 않음)
