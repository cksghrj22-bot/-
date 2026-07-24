# Creator OS ↔ Claude 연동 끊김 진단 (2026-07-24, 이찬호 "너랑 크리에이터OS랑 같이 일 안 해")

> 로그 3종(launcher / postgres / skills-mcp-stderr)을 형이 채팅으로 올려 진단.
> 본진(맥스튜디오) 시스템이라 클라우드 코드방에선 직접 수정 불가 → 진단+처방을 형이 맥에서 실행.

## 🔴 근본 원인 = Claude(Anthropic) 인증 만료

로그가 두 갈래로 같은 뿌리를 가리킴:

**1) OAuth 토큰 무효 — 30분마다 반복(04시~18시 지속):**
```
creator-os.oauth_usage_fetcher: HTTP 401 Unauthorized
"authentication_error: Invalid authentication credentials" (error_visibility: user_facing)
```
request_id 붙은 진짜 API 401 = Anthropic OAuth 토큰이 죽음.

**2) Claude CLI 호출 실패 — 초 단위 폭주(13:52~):**
```
creator-os.backlog_completion: 종결 판정 LLM 실패:
  Claude CLI timeout(30s)   ← 초기(토큰 반쯤 살아 대기하다 타임아웃)
  → Claude CLI exit code 1  ← 현재(토큰 완전 만료 → 즉시 거절, stderr 빈 값)
```
Creator OS가 판정/생성 때 Claude CLI를 부르는데 인증이 죽어 전부 실패 → fallback.
= **"너랑 Creator OS가 같이 일 안 해"의 정체.** "업데이트되고" = Claude Code 업데이트 때 로그인 세션 풀림.

## 🟡 부수 증상 (같은 뿌리 or 재시작으로 해소)
- `invoke_agent.skills_mcp_drop_suspected` — skills MCP 끊김 의심 + skills 서버 반복 spawn(재시작 루프).
- `Discord 봇 크래시 exit code -9` — SIGKILL(메모리 OOM 추정).
- `restart_bot launchctl 실패: Could not find service "com.creator-os.agent"` — 봇 재시작 서비스 미등록.
- backlog_completion **3초마다 무한 재시도 폭주** — CPU·API 낭비. 인증 고치면 멈춤.

## ✅ DB는 정상
postgres 07-24 에러 0건. 과거(07-08~07-13) "column X does not exist / relation creator_os_frame_analysis does not exist"는 스키마 마이그레이션 이슈였으나 **이미 해결됨**. 지금 문제 아님.

## 🛠 처방 (본진 맥스튜디오 터미널)
1. **Claude 재로그인** (401·exit1 동시 해결):
   - `claude` 실행 → `/login` → 브라우저 재인증
2. **Creator OS 완전 재시작** (봇·skills MCP·backlog 폭주 리셋):
   - 앱 종료→재실행, 또는 `launchctl kickstart -k gui/$(id -u)/com.creator-os.agent`
3. 확인: oauth_usage 401이 사라지고 backlog_completion 폭주가 멈추면 복구 완료.

## 교훈 (박제)
- Claude Code **업데이트 후엔 Creator OS의 Claude 로그인 세션이 풀릴 수 있다** → 업데이트 시 재로그인 체크.
- 증상이 "Creator OS가 나랑 협업 안 함"으로 보이면 **먼저 oauth 401 / Claude CLI exit1**을 의심(인증). DB·MCP·봇 크래시는 대개 후속 증상.
