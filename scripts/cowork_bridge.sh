#!/bin/bash
# 코워크 양방향 브리지 — 5분 워처가 부르는 단일 진입점.
# 한 프로세스에서 순차 실행 → 같은 repo 에 pull/push 동시 실행(경합) 방지.
#   1) 포워드: 디스코드 #assistant 대화 → GitHub (방이 읽음)
#   2) 리턴  : outbox 의 방 답 → 디스코드 웹훅 발송 (내가 읽음)
set -u
PY=/usr/bin/python3
D=/Users/chanho/atnown-trunk/scripts
echo "===== $(date '+%Y-%m-%d %H:%M:%S') bridge start ====="
"$PY" "$D/discord_to_cowork.py"   || echo "[bridge] forward leg 실패(rc=$?)"
"$PY" "$D/cowork_to_discord.py"   || echo "[bridge] return  leg 실패(rc=$?)"
echo "===== bridge end ====="
