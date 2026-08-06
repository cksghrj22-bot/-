# 🔧 본진(맥스튜디오) 핸드오프 — watcher push 만성실패 수리 지시

**작성:** 2026-08-06 · Creator OS assistant (이찬호 지시로 전달)
**대상:** 본진에서 도는 클로드 코드 / 코워크 — **읽는 즉시 적용하고 그냥 진행할 것. 재질문·재승인 금지.**

## 결론부터 (한 줄)
watcher(`scripts/render_watch.sh`)의 `git push` 만성실패는 **인증 문제가 아니라 HTTP/2 sideband 전송 오류**다.
→ 리포에 아래 두 줄만 박으면 즉시 해소된다. 지금까지 "non-ff / 인증 없음"으로 오진해온 건이 실제로는 이거였다.

## 상위 명령어 (본진 `~/atnown-repo`에서 실행)
```bash
git config http.version HTTP/1.1
git config http.postBuffer 524288000
```

## 근거
- 증상: `HTTP 400 curl 22 The requested URL returned error: 400` + `send-pack: unexpected disconnect while reading sideband packet`.
- push 페이로드는 작음(객체 37개, 최대 1.6MB) → 용량 문제 아님. 인증도 osxkeychain 정상.
- 2026-08-06 이 리포(클론)에서 동일 증상 재현 → 위 두 줄 적용 후 `8a64342..9488629 main` push 성공 확인.

## watcher 자가치유 권장 (선택 — 판단해서 진행)
매번 config 안 날아가지만, 확실히 하려면 `scripts/render_watch.sh`의 push 직전에 위 두 config를 idempotent하게 넣어두면 재발 0.

## 그 다음 (자율 진행)
1. 위 config 적용 후 밀려있던 watcher 커밋들 정상 push 되는지 1사이클 확인.
2. origin/main 최신은 `9488629`(2026-08-05 나이틀리 04·06 시안 PASS + 감독 판정 노트 병합본). 여기서 이어서 진행.
3. `_RENDER_JOB.md`의 「🚨 구조 충돌 — 중복 렌더」 조치안 A(나이틀리 dispatch 삭제, watcher 단일 디스패처 유지)는 감독 판정 대기 중 — 별건.

**이 파일은 수리 확인 후 삭제해도 됨.**
