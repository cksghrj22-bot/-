# 🎥 B롤 자동스캔 시스템 (2026-07-18 이찬호: "B롤 자동스캔 찾는 시스템 만들기")

폰이 드라이브에 자동으로 쌓는 촬영본을 **코드방이 기억하고 골라 쓰는** 시스템.
매번 눈으로 폴더 뒤지지 않고, 같은 영상 두 번 안 쓰고(저품질 방지), 방이 리뉴얼돼도 기억이 남는다.

## 한 줄 요지
- 폰 → 드라이브(폰_자동업로드 폴더)는 **이미 자동**. 형님은 촬영만 하면 됨.
- 코드방이 그 폴더를 스캔 → **카탈로그**(`content/broll/카탈로그.json`)에 기억 → 안 쓴 원본 추천 → 렌더 → "썼다" 표시.
- 카탈로그는 git에 커밋된다 = **채팅 기억 0이어도 살아있는 기억.**

## 왜 코드가 스캔을 직접 안 하나 (스코프 경계)
- `shorts/gdrive.py`의 기기인증(drive.file)은 **"앱이 만든 파일"만** 본다 → 폰 자동업로드분을 못 본다.
- 그래서 **폴더 스캔은 코드방(MCP Google Drive 커넥터, 사용자 권한)** 이 한다. 승인 팝업 불필요(읽기).
- `shorts/broll_scan.py`는 네트워크를 안 탄다 — 코드방이 뽑아준 목록(JSON)을 받아 **병합·판정만** 한다.
  → 테스트가 오프라인 통과(`tests/test_broll_scan.py`).

## 시스템이 자동으로 걸러주는 것
- **0바이트 파일**(업로드 실패/진행중) → 제외
- **중복**(같은 id) → 한 번만
- **이미 쓴 원본** → 다시 추천 안 함 (shorts_config `source_video_policy`: 쇼츠 1편=고유 원본 1개, 복붙 금지)

## 소스 폴더 (드라이브)
- `174TFm5_cJyfi-U0X3HM_JKGN3gc3avYA` = **폰_자동업로드** (형님 폰이 자동으로 올림)
- `1MBvVanqFgvBjk7hS2wjOaYN6oiaoBtlO` = **코드방_인입** (수동 인입용, anyone-reader)

## 코드방이 매 렌더 앞에 도는 절차
1. **스캔**: MCP로 폰 폴더의 video 파일 목록을 뽑아 `listing.json`으로 저장
   (쿼리: `parentId = '174TFm5_cJyfi-U0X3HM_JKGN3gc3avYA' and mimeType contains 'video/'`)
2. **병합**: `python3 -m shorts.broll_scan merge listing.json`
3. **추천**: `python3 -m shorts.broll_scan pick -n 1` → 안 쓴 원본(오래된 순) id·이름·링크
4. **다운로드**: 그 id를 MCP `download_file_content` 또는 뷰링크로 받아 렌더
5. **표시**: `python3 -m shorts.broll_scan use <쇼츠이름> <id>` → 다신 추천 안 됨

## 그 밖의 명령
- `python3 -m shorts.broll_scan list` — 쓸 수 있는(안 쓴) 클립 전체
- `python3 -m shorts.broll_scan stats` — 총/쓸수있음/사용됨 요약

## 현재 상태 (2026-07-18 시드)
- 카탈로그 56개(폰_자동업로드, 0바이트·중복 제외). 전부 미사용.
- 다음 렌더부터 `pick`으로 고르고 `use`로 소진 기록 → 재사용 자동 차단.

## 확장 여지 (아직 안 함, 필요 시)
- 씬 태그(가위질/뒷모습/드라이 등)를 코드방이 프레임 보고 붙여 `tags`에 저장 → `pick --tag 가위질`.
  지금은 프레임 확인이 렌더 때 어차피 이뤄지므로 수동. 자동 태깅은 요청 오면 붙인다.
