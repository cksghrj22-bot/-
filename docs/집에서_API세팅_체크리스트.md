# 🏠 집에서 (컴퓨터로) API 세팅 체크리스트 — 2026-07-21

> 이찬호가 집 컴퓨터에서 몰아서 끝낼 목록. 발급한 값은 채팅에 붙여넣으면 코드방이 `secrets/`에 저장(gitignore·비밀·절대 커밋 안 함).

## ✅ 이미 다 돼 있음 (건드릴 필요 없음)
| 항목 | 상태 |
|---|---|
| 유튜브 조회수 API | ✅ 작동 |
| 유튜브 업로드 OAuth | ✅ 작동 |
| 일레븐랩스 TTS(보이스) | ✅ 작동 |
| **구글드라이브(파이프라인 업로드)** | ✅ 작동·자동갱신(재인증 불필요) |

## ❌ 집에서 발급할 것 — 딱 2개 (둘 다 같은 Meta 앱에서)
> 둘 다 developers.facebook.com 앱 「앳나운 콘텐츠」 하나에서 나옵니다.

### 0. (처음이면) 개발자 계정 + 앱
1. `developers.facebook.com/apps` → 로그인 → (계정 없으면 폰 인증 — 컴퓨터가 더 쉬움)
2. **앱 만들기** → 유형 「비즈니스」 → 이름 「앳나운 콘텐츠」

### 1. 스레드 토큰 → `secrets/threads.json`
1. 앱 → 제품 추가 → **Threads API** (또는 "Threads 사용" 사용 사례)
2. 권한: **threads_basic**, **threads_content_publish**
3. **액세스 토큰 생성**(장기) → 토큰 문자열 복사
4. → 채팅에 `{"access_token":"..."}` 붙여넣기
5. 효과: **예약 8편 자동발행 즉시 시작** (지금 밀린 3편부터)

### 2. 인스타그램 토큰 → `secrets/instagram.json`
1. 같은 앱 → 제품 추가 → **Instagram Graph API** (Instagram 비즈니스/크리에이터 계정 + 페이스북 페이지 연결 필요)
2. 권한: **instagram_basic**, **instagram_content_publish**, (pages_show_list, business_management)
3. **액세스 토큰 생성**(장기) → 복사
4. → 채팅에 `{"access_token":"...","ig_user_id":"..."}` 붙여넣기 (ig_user_id 없으면 내가 조회)
5. 효과: 인스타 자동발행 가능

## 📤 구글드라이브 자동화 (컴퓨터 아니라 폰에서 · 5분)
> 파이프라인 Drive는 이미 됨. 남은 건 "폰→Drive 자동업로드"뿐 = **PhotoSync 앱**(API 아님).
- 폰 App Store 「PhotoSync」 설치 → Google Drive 연결 → 대상 **「코드방_B롤_인트레이」**(ID `1MBvVanqFgvBjk7hS2wjOaYN6oiaoBtlO` — 코드 `shorts/intake_scan.py`가 읽는 정본 폴더) → Autotransfer ON
  - ⚠️ 구 폴더 「쇼츠_배경클립_넣는곳」 아님. 파이프라인은 「코드방_B롤_인트레이」를 스캔한다(2026-07-23 실측: PhotoSync가 여기로 정상 업로드 중).
- 상세: `docs/드라이브_업로드_자동화_계획.md`

## 🔑 값 넘기는 법 (안전)
- 토큰·JSON을 **채팅에 붙여넣으면** 내가 `secrets/`에 저장.
- 🔒 `secrets/`는 gitignore라 **절대 커밋·출력 안 함.** (비밀 취급)

## ✅ 완료 기준
- `python3 -m pipeline check` 돌렸을 때 스레드·인스타가 ✅로 바뀜
- 스레드 예약 8편이 자동으로 올라가기 시작
- PhotoSync로 영상 찍어 올리면 Drive 「코드방_B롤_인트레이」에 뜸 (파이프라인이 읽는 폴더)

---
**요약: 집에서 = Meta 앱에서 스레드·인스타 토큰 2개. 나머지(유튜브·TTS·드라이브)는 이미 끝. 폰에선 PhotoSync 5분.**
