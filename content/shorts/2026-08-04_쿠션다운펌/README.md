# 쿠션다운펌 v5 산출물 인덱스

## 정본

- 매니페스트: `content/manifests/쿠션다운펌_실사중심_v5.json`
- 제작분석: `content/reports/2026-08-04_쿠션다운펌_v5_제작분석.md`
- 대본: `content/대본/2026-08-03_쿠션다운펌_쇼츠대본_초안.md`
- 구술: `content/구술/2026-08-03_쿠션다운펌_구술정본.md`

## 렌더 산출물

- QC 영상: `/Users/chano/Documents/Codex/2026-08-02/github-cli-gh-codex-6/outputs/쿠션다운펌_실사중심_v5_최종시안/쿠션다운펌_실사중심_v5_최종시안_QC.mp4`
- 프레임 QC: `/Users/chano/Documents/Codex/2026-08-02/github-cli-gh-codex-6/outputs/쿠션다운펌_실사중심_v5_최종시안/frame_qc_12.jpg`
- QC: PASS · 1080×1920 · 30fps · 40.0초 · H.264/AAC
- YouTube: https://youtu.be/95bM2fZRXkA · 2026-08-04 20:00 KST 예약공개

렌더 MP4와 작업 캐시는 Git 바이너리 비대화를 막기 위해 커밋하지 않는다. 매니페스트와 Drive file ID가 재생성의 정본이다.

## B롤 정본

| 원본 | Drive file ID | 재사용 구간 | 역할 |
|---|---|---|---|
| `video-1432_right_raw.mp4` | `18TCjf4c3PZN_Uw0i_RgnfNfXBtDZi_Ul` | 10초·55초·110초 부근 | 약 도포·압력·빗 방향·모발 붙이기 접사 |
| `video-1466_singular_display.mov` | `1EGl8Gv7RGwmR3rRvAI0cgNyfi0nOxEK6` | 60~75초 부근 | 완성 두상·공기감·자연스러운 움직임 |

## 재현

```bash
python3 -m shorts.make content/manifests/쿠션다운펌_실사중심_v5.json \
  --out out/쿠션다운펌_실사중심_v5.mp4 \
  --workdir _build/쿠션다운펌_실사중심_v5
```

후속 H9 「다운펌 vs 매직」은 위 B롤을 카탈로그에서 불러올 수 있다. 새 시안의 발행은 형 승인 후에만 진행한다.
