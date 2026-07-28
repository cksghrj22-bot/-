# 🎬 매니페스트 라이브러리 — 대본 1개 → 완성본 1개 (엔진: `shorts.make`)

> 2026-07-28 이찬호 지시로 확립. **엔진은 하나(`shorts/make.py`), 매니페스트(루트)는 여럿.**
> 창의는 형 몫(생각·메시지·스토리). 이 라이브러리는 그 생각이 **안 깨지고** 나오게 하는 기계다.

## 원칙 (형 확정)
- **새 표현 = 새 매니페스트.** 새 스타일·포맷이 필요하면 이 폴더에 `.json`을 하나 더 만든다. 기존 걸 지우지 않는다.
- **검증된 좋은 요소 = 기존 매니페스트에 껴넣기.** 잘 먹힌 연출(애니·오버레이·톤)은 관련 루트 매니페스트에 흡수시켜 개선한다.
- **영상 메시지에 따라 가장 맞는 루트를 골라 쓴다.** 매번 새로 짜지 않는다 = 안 깨진다(그룹으로 뭉쳐 있으니).
- 매니페스트는 **자기완결 그룹**이다 — 대본(phrases)·footage(segments)·애니(overlays)·아웃트로가 한 파일에.

## 쓰는 법
```
python3 -m shorts.make content/manifests/<루트>.json --out 완성본.mp4 --workdir <작업폴더>
```
→ TTS(타임스탬프 싱크)·footage 스트리밍 추출·애니 오버레이·자막·BGM·아웃트로까지 한 번에. (발행/업로드는 형 검수 후 별도)

## 루트 목록 (계속 늘어남)
| 루트 파일 | 언제 쓰나(메시지 성격) | 특징 |
|---|---|---|
| `메타안경_산_후기.json` | **실사 언박싱/제품 + 데이터 논증**(콘텐츠=자산 류) | 검은훅카드 → 실사 언박싱(개봉·리빌·착용) → 가치격차 데이터애니(진한 스크림) → 상담 실사 인서트 → 엔딩 질문카드 → SNS일기 아웃트로 |

> 새 루트를 추가하면 이 표에 한 줄 넣는다. 좋은 요소가 나오면 해당 루트 json에 반영한다.

## 매니페스트 스키마 (요약 — 상세는 `shorts/make.py` 최상단 docstring)
```jsonc
{
  "title": "...",
  "voice": {"stability":0.42,"style":0.15,"speed":1.05},   // 생략 시 자연 기본톤
  "bgm": "<mp3>", "outro": "SNS에 일기를 쓰고 있어요",
  "phrases": [["raw(합성/정렬)","disp(자막·\\N줄바꿈)","en|null", false], ...],
  "segments": [                                             // 시간축 순서(빈틈없이 total 채움)
    {"black": true, "untilLine": 0},                        // 훅 검은카드
    {"src":"<DriveFileId>","ss":6,"hflip":true,"frame":"landscape","untilLine":3},  // 실사 beat
    {"black": true, "untilLine": 13, "tail": 3.4}           // 엔딩 + 아웃트로 여유
  ],
  "overlays": [ {"type":"value_gap","fromLine":2,"toLine":4} ]  // 데이터 애니(선택)
}
```
- 숫자("9억 9,900만")는 **자동으로 한글 읽기 변환**(`tts.koreanize_numbers`) → 말깨짐 없음. 손철자 불필요.
- 훅/엔딩(검은 segment에 걸린 자막)은 **자동 중앙정렬**.
- footage는 통다운 없이 **스트리밍 추출**(`drive_stream`) — 디스크·moov 문제 없음.

## 코드 게이트(안 틀리는 규칙 — 글 아니라 함수)
- `shorts/preflight.py` — 착수 전 **중복 자동차단**(예전 거 재탕 방지).
- `shorts/drive_stream.py` — 대용량 footage 스트리밍 추출.
- `shorts/tts.py` `koreanize_numbers` — 숫자 말깨짐 방지.
- `shorts/syncbuild.py` — 자막 타임스탬프 싱크. `shorts/shortstyle.py` — 교보/POP·프레이밍·아웃트로 정본.
