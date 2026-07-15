# 🌳 본진 맥 ↔ 코드방 연결 (같은 코드, 두 곳에서 돎)

> 목적: **"연결이 안된 느낌"을 없앤다.** 코드방(클라우드)에서 만든 코드가
> **본진 맥에서도 똑같이 돌게** 하고, 양쪽이 자동으로 맞춰지게 한다.
> 형님은 git·깃허브 안 만진다 — 명령 한 줄 / 본진 클로드가 대신 돌린다.

## 두 개의 다리 (이미 있는 구조)

| 다리 | 무엇이 오가나 | 방향 |
|------|--------------|------|
| **깃허브** (이 리포지토리) | 코드(pipeline·shorts·프롬프트·knowledge) | 코드방 ↔ 본진 자동 |
| **구글드라이브** (앳나운_영상) | 영상·BGM·큰 파일 | 코드방 ↔ 본진 |

코드는 깃허브로, 무거운 영상/BGM은 드라이브로. 이 둘이 벽을 없앤다.

## 처음 한 번 (본진 맥에서)

터미널에 이거 한 줄 — 코드를 `~/chano-code`로 받고 바로 세팅한다:

```bash
git clone https://github.com/cksghrj22-bot/-.git ~/chano-code && bash ~/chano-code/본진/세팅.sh
```

- 파이썬 표준기능만 써서 **pip 설치 없음**. `ffmpeg`만 있으면 되고, 없으면 스크립트가 `brew install ffmpeg`로 깐다.
- 비공개 리포라 로그인 물으면: `gh auth login` 한 번(또는 맥에 이미 깃허브 로그인돼 있으면 그대로).
- `secrets/`는 깃허브에 안 올라간다(안전). 렌더/업로드까지 하려면 노션 「📱 코드방 상태판」 키를 `~/chano-code/secrets/`에 복원.

## 다음부터 (최신화·동기화)

```bash
bash ~/chano-code/본진/세팅.sh          # 최신 코드 받고 진단
bash ~/chano-code/본진/동기화.sh both    # 내려받고 + 본진 변경분 올리기
```

- **코드방이 코드 바꾸면** → 본진에서 `세팅.sh`(또는 `동기화.sh pull`) → 본진도 최신.
- **본진에서 코드 바꾸면** → `동기화.sh push` → 코드방도 최신.

## 뭐가 돌아가나 (본진에서)

```bash
cd ~/chano-code
python3 -m pipeline check                # 연동 진단(연동이 제일 먼저)
python3 -m pipeline search "숱치기"       # 지식 검색 (형님 자산 안 잊게)
python3 -m shorts.proof <대본폴더> --out <출력> --broll <클립폴더> --bgm <BGM폴더> --preset style_preset_mind
```

본진은 영상·CreatorOS BGM·폰트가 다 로컬에 있으니 **여기서 렌더가 제일 매끄럽다.**
코드방은 같은 코드의 백업 + 원격작업용. 둘이 깃허브·드라이브로 늘 같은 상태.

## 환경변수(선택)

- `CHANO_DIR` 받을 위치(기본 `~/chano-code`)
- `CHANO_BRANCH` 추적 브랜치(기본 `main`)
