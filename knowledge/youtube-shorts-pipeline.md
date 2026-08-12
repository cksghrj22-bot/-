# 유튜브 쇼츠 자동화 파이프라인 — 재건 계획

이전에 운영하던 자동화(차노쌤 채널): 영상에 자막(대사) 삽입 → BGM 합성 → 유튜브 업로드/예약까지 자동 처리.
이전 구현은 대화방에만 있어 유실됨. 이번에는 **모든 코드를 이 리포지토리에 보관**하고, 실행은 영상 파일이 있는 Mac Studio(코워크/로컬)에서 한다.

## 파이프라인 단계

1. **입력**: 지정 폴더(예: `~/Shorts/inbox`)에 원본 영상 + 대사 스크립트(txt/md)를 넣는다.
2. **자막 삽입**: ffmpeg + 자막 파일(ASS/SRT 생성)로 영상에 대사를 구움. 스타일(폰트, 노란 배경 강조 등)은 설정 파일로 관리.
3. **BGM 합성**: ffmpeg로 배경음악 트랙을 볼륨 조절해 믹싱 (원본 음성 유지).
4. **업로드**: YouTube Data API v3로 업로드. 제목/설명/태그는 스크립트 메타데이터에서, 공개 상태는 `비공개`/`예약됨` 지정 가능.
5. **기록**: 처리 결과(영상 ID, 업로드 시각)를 로그로 남기고 처리 완료 파일은 `done/` 폴더로 이동.

## 다시 만들 때 필요한 것

- [ ] Mac Studio에 ffmpeg 설치 확인 (`brew install ffmpeg`)
- [ ] Google Cloud 프로젝트에서 YouTube Data API v3 활성화 + OAuth 클라이언트 생성
  - 유의: API 기본 할당량은 하루 10,000 유닛, 업로드 1건당 1,600 유닛 (하루 약 6건)
- [ ] 자막 스타일 사양 (폰트, 크기, 위치, 강조색 — 기존 영상 캡처 참고)
- [ ] BGM 파일 및 볼륨 기준
- [ ] 업로드 기본값: 공개 상태, 예약 시각 규칙, 제목/설명 템플릿

## 실행 형태

- 평상시: Mac에서 `python -m shorts run` 한 번 실행하면 inbox의 새 영상을 전부 처리.
- 자동화: macOS launchd 또는 코워크 예약 작업으로 주기 실행.
  (업로드는 영상 파일이 Mac에 있으므로 클라우드가 아닌 로컬 실행이 맞다.)

## 사용법

```bash
# Mac Studio에서, 리포지토리 클론 후:
mkdir -p ~/Shorts/inbox
# 영상(a.mp4)과 대사 스크립트(a.txt)를 inbox에 넣고:
python3 -m shorts run --dry-run   # 업로드 없이 렌더링 확인
python3 -m shorts run             # 렌더링 + 업로드 + done/ 이동
```

대사 스크립트 형식 (`영상이름.txt`):

```
# 제목: 정착 미용실 찾는 법
# 설명: 설명 문구
# 태그: 미용실,헤어
00:00-00:03 첫 대사
00:03-00:07 둘째 대사
타이밍 생략하면 영상 길이에 맞춰 균등 배분
```

## API 키 세팅 (한 번만)

### 유튜브 — `secrets/youtube.json`

1. [Google Cloud Console](https://console.cloud.google.com) → 프로젝트 생성 → **YouTube Data API v3** 활성화
2. OAuth 동의 화면 설정 → 사용자 유형 "외부", 테스트 사용자에 본인 계정 추가
3. 사용자 인증 정보 → OAuth 클라이언트 ID 생성 (데스크톱 앱) → client_id / client_secret 확보
4. refresh_token 발급: [OAuth Playground](https://developers.google.com/oauthplayground)에서
   우측 설정 ⚙ → "Use your own OAuth credentials" 체크 → 위 client_id/secret 입력 →
   scope에 `https://www.googleapis.com/auth/youtube.upload` 선택 → 승인 → refresh token 복사
5. 리포지토리 루트에 `secrets/youtube.json` 생성:
   `{"client_id": "...", "client_secret": "...", "refresh_token": "..."}`
   (`secrets/`는 gitignore에 있어 커밋되지 않음 — 키는 절대 리포지토리에 올리지 않는다)

### 인스타그램 — `secrets/instagram.json` (선택)

1. 인스타그램 계정을 비즈니스/크리에이터로 전환하고 Facebook 페이지에 연결
2. [Meta for Developers](https://developers.facebook.com)에서 앱 생성 → Instagram Graph API 추가
3. 장기(60일) 액세스 토큰 + 인스타그램 비즈니스 계정 ID 확보
4. `secrets/instagram.json`: `{"access_token": "...", "ig_user_id": "..."}`
5. `shorts_config.json`에서 `"instagram": {"enabled": true}` 로 변경

## 상태

- [x] 계획 문서화 (이 파일)
- [x] `shorts/` 모듈 구현: 자막(ASS) 생성, ffmpeg 렌더링+BGM, 유튜브 재개형 업로드, 인스타 릴스 업로드
- [ ] Mac Studio에서 실전 테스트 (ffmpeg 렌더링 → dry-run → 비공개 업로드 1건)
- [ ] API 키 재발급 후 `secrets/`에 배치
