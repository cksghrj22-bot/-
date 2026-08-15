# rooms/낙타방/ — 이 방 전용 줄기 코드 (2026-08-15 차노 확정)

> "너의 줄기코드는 커밋해 다만 **이 방에서만 적용해**"

`scripts/` 는 공유자원(전략실만 수정)이라 이 방 코드를 거기 두지 않는다.
**이 방 줄기(③ 에이엠톤)의 렌더러·게이트는 여기에 둔다. 다른 방은 참조하지 않는다.**

| 파일 | 무엇 |
|---|---|
| `amton_post.py` | 에이엠톤 좌하단 두 줄 렌더러 (매니페스트 구동 + 린트 + 게이트 자동호출) |
| `amton_gate.py` | 자동 게이트 A1~A7 |
| `film_grade.py` | 필름룩 적용 (값은 루트 `shorts_config.json > grades` 에서 읽음) |
| `manifest_kinds.py` | **매니페스트 스탬 구분기** — 모든 렌더러가 반드시 통과 (`매니페스트_구분표.md`) |
| `nakta_from_manifest.py` | ① 낙타형 자막바 매니페스트 렌더러 (그리기는 공유 `nakta_post.py`) |
| `fonts/` | 이 방 폰트 사본 — 공유 `scripts/cards/fonts/` 가 사라져도 이 방은 돈다 |

## 쓰는 법
```
python3 rooms/낙타방/film_grade.py _intray_헤어사진/ _tmp/헤어_E/ --grade warm_film --measure
python3 rooms/낙타방/amton_post.py content/amton/<매니페스트>.json     # 끝에서 게이트 자동 실행
```

## 경계
- **①낙타 자막바**는 공유 정본 `scripts/cards/nakta_post.py` 를 쓴다(전략실 소유). 여기로 복사하지 않는다.
- **②쇼츠·AI일기** 코드는 이 폴더에 절대 두지 않는다. 방2 것이다.
- 규격 정본은 `knowledge/` (공유). 코드만 여기.
