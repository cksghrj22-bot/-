# Cowork 진행상황 — 트렁크 최신화 (Codex/Discord/CreatorOS 공용)

> Cowork(뇌)가 클라우드에서 직접 트렁크에 최신화. 상세 정본 = 차노기획실 Project(claude.ai). 다른 방/에이전트는 여기서 최신 상태 확인.

## 2026-08-04 통합 확정
- 역할: Cowork=뇌/총괄(폰 창구) · Codex=양산 손 · 본진(맥스튜디오) Claude Code=실행 손 · Creator OS=영상 엔진 손 · 감독=차노(판정).
- 부팅: 리포 AGENTS.md(Codex)·CLAUDE.md(Claude Code) + knowledge/. 형식=외부 고성과 클론, 생각=차노.
- 렌더 dim 정합: spec.py/verify_render/제작규격/스펙시트 = dim 25%(0.25) 통일 (본진 적용 대기).
- 분업: Cowork=지시서+더블체크(토큰 절약), 양산=Codex, 렌더·예약=본진, 판정=감독 1회.
- 촘촘 QA: 일레븐랩스·목소리·BGM·자막·급전환·아웃트로 실수 방지 체크 가동.

## 오늘 주제 큐 (미용 8 : 인간 4)
미용: H1 디자이너 자기머리 · H2 여름 습기 · H3 여름 두피 · H4 여름 숏컷 · H5 미용실간날만예쁜이유 · H6 색=스며듦 · H7 숱치기=공간 · H8 볼륨=모근각도.
인간: M1 브랜드에얹히지마라 · M2 노래·우화위로 · M3 일은AI가생각은사람이 · M4 커트=생각.
우선 제작: H1 · H2 · H3 · H5. (H1 제작표 완료)

## 본진 마무리 대기 (본진_실행_큐)
AGENTS.md 트렁크 반영 · dim 정합 spec.py 0→0.25 · Creator OS 정렬 · verify_render 강화(급전환·발음·밸런스·아웃트로).

## 2026-08-04 Codex 실행 가능 범위 보고
- 형 직접 지시로 Codex가 `렌더 → QC → YouTube 업로드/예약`까지 맡는다. 이번 지시는 기존 초안 전담 제한의 작업별 예외다.
- Full Access 실측: 테스트 171개 PASS(2 skipped), YouTube 조회·업로드 OAuth·ElevenLabs·Drive·외부 네트워크 정상.
- Meta는 `secrets/instagram.json`·`secrets/threads.json`이 없어 Instagram/Threads 발행 불가. 토큰이 들어오면 같은 파이프라인에서 처리 가능.
- 완료: `content/shorts/2026-08-04/_RENDER_JOB.md`의 두피 자외선·둥근 얼굴 단발 2편을 컬러 렌더하고 QC PASS 후 YouTube 예약공개 처리.
- 예약: 두피 자외선 `B8urBGnlwOI`(8/5 11:00 KST), 둥근 얼굴 단발 `3_MJ1Hec0Hw`(8/5 16:00 KST). 상세는 `knowledge/유튜브_예약현황.md`.
- 전달 결론: Codex는 현재 렌더·QC·YouTube 예약발행까지 독립 처리 가능. Instagram/Threads만 Meta 토큰 입력 전까지 Cowork/본진 담당.
