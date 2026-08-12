- [x] 2026-08-11 상태: `TASK_TTS_QUOTA_GATE_0809.md` 2번 완료 — TTS 실패 하드 스톱 적용(HTTP 200 아님 중단, 1000바이트 미만 실패, 합산 보이스 0.5초 미만 중단).
- [x] 2026-08-11 상태: `TASK_TTS_QUOTA_GATE_0809.md` 3번 완료 — `_tts_cache/<sha256(text+voice_id+model_id+settings)>.mp3` 캐시 적용, 캐시 적중 시 ElevenLabs API 미호출.
- [x] 2026-08-11 상태: `TASK_TTS_QUOTA_GATE_0809.md` 4번 완료 — 렌더 전 `TTS_PREFLIGHT`로 필요/캐시적중/실제청구 문자수 및 quota probe 확인.
- [x] 2026-08-11 상태: `TASK_RENDER_FIX_0809.md` 6번 완료 — faster-whisper 로컬 듣기 게이트 적용(`voice_present_ok`, 세그먼트 0이면 즉시 FAIL).
- [x] 2026-08-11 상태: 로컬 게이트 자체 테스트 완료 — 기존 12편 기준 정상 8 PASS / 무음 4 FAIL은 교체 전 원본 기준이며, 현재 디스크 산출물은 재렌더 후 12 PASS / 0 FAIL; 0세그먼트 즉시 FAIL 단위 테스트 확인.

# codex 렌더 OK 결과

- [x] `TASK_TTS_QUOTA_GATE_0809.md` 2번: TTS 실패 하드 스톱 완료(HTTP 200 아님 중단, 401/quota stop marker, 1000바이트 미만 실패, 합산 보이스 0.5초 미만 중단).
- [x] `TASK_TTS_QUOTA_GATE_0809.md` 3번: TTS 캐시 완료(`_tts_cache/<sha256(text+voice_id+model_id+settings)>.mp3` + alignment, 성공 응답만 저장, 캐시 적중 시 API 미호출).
- [x] `TASK_TTS_QUOTA_GATE_0809.md` 4번: 렌더 전 잔량 사전 확인 완료(`TTS_PREFLIGHT`로 필요/캐시적중/실제청구 문자수 로그, 캐시 미스가 있을 때 1글자 probe로 quota 확인).
- [x] `TASK_RENDER_FIX_0809.md` 6번: faster-whisper 로컬 듣기 게이트 완료(`voice_present_ok` 세그먼트 60% 이상, 0세그먼트 즉시 FAIL, 첫발화/일치율/싱크 측정).
- [x] 로컬 게이트 자체 테스트: 현재 12편 기준 12/12 PASS. 0세그먼트 파일은 `voice_present_ok=false`, `read_ok=false`, `sync_ok=false`로 즉시 FAIL.

작성: 2026-08-11

기준: ffmpeg 4fps/32x57 검정 샘플, faster-whisper small/cpu/int8 로컬 STT.
비고: B방 잡 기본값 `thumb:false` 유지.

| 파일명 | 길이 | 검정% | 세그먼트수 | 첫발화시각 | 일치율 | 통과여부 |
|---|---:|---:|---:|---:|---:|---|
| _jobs/_done/S1_v2.mp4 | 46.6s | 35.3% | 18 | 0.00s | 97.2% | PASS |
| _jobs/_done/S2_v2.mp4 | 42.9s | 34.5% | 10 | 0.82s | 98.1% | PASS |
| _jobs/_done/S3_v2.mp4 | 38.3s | 34.0% | 10 | 0.82s | 99.5% | PASS |
| _jobs/_done/S4_v2.mp4 | 40.3s | 0.0% | 12 | 0.82s | 96.6% | PASS |
| _jobs/_done/S5_v2.mp4 | 40.5s | 28.4% | 11 | 0.85s | 97.0% | PASS |
| _jobs/_done/S6_v2.mp4 | 50.0s | 28.5% | 17 | 0.00s | 92.6% | PASS |
| _jobs/_done/S7_v2.mp4 | 37.0s | 31.1% | 14 | 0.16s | 94.1% | PASS |
| _jobs/_ascii/SEED1.mp4 | 35.1s | 14.3% | 13 | 0.00s | 98.0% | PASS |
| _jobs/_ascii/SEED5.mp4 | 35.9s | 20.1% | 12 | 0.15s | 93.9% | PASS |
| _jobs/_ascii/SEED13.mp4 | 36.2s | 11.7% | 11 | 0.00s | 94.6% | PASS |
| _jobs/_ascii/SEED17.mp4 | 35.9s | 31.2% | 12 | 0.17s | 98.6% | PASS |
| _jobs/_ascii/YS_v3.mp4 | 30.4s | 28.7% | 17 | 0.00s | 99.4% | PASS |

## 게이트 확인

- `voice_present_ok`: 세그먼트 수가 대본 문장 수의 60% 이상일 때만 통과. 0세그먼트는 즉시 FAIL.
- `sync_ok`: 첫 세그먼트 시작 1.2초 이하.
- `read_ok`: 전사문과 대본 일치율 90% 이상.
- `black_ok`: 검정 샘플 비중 40% 이하.
- `thumb`: B방 잡은 모두 `false` 유지.
