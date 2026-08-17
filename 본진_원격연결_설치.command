#!/bin/zsh
# ─────────────────────────────────────────────────────────────
#  본진 원격 연결 설치 — 딱 한 번만 실행하면 됩니다
#  (전략기획및개인업무 방 · 2026-08-17)
#
#  이걸 돌리면:
#   1) 원격 명령 실행기가 상주 → 코워크에서 맥 명령 실행 가능
#   2) 디스패처·멀티워치가 LaunchAgent 로 등록 → 죽어도 자동 부활
#  더블클릭하거나  zsh 본진_원격연결_설치.command  로 실행
# ─────────────────────────────────────────────────────────────
set -u
ROOT="$HOME/atnown-content-pipeline"
AGENTS="$HOME/Library/LaunchAgents"
UID_N=$(id -u)
LABELS=(com.atnown.remote-cmd com.atnown.codex-dispatch com.atnown.cowork-multi-watch)

cd "$ROOT" || { echo "⛔ $ROOT 없음"; exit 1; }
mkdir -p "$AGENTS" logs

echo "▶ 1/5  기존 수동 데몬 정리"
pkill -f remote_cmd_watch.py  2>/dev/null
pkill -f codex_dispatch.py    2>/dev/null
pkill -f cowork_multi_watch.py 2>/dev/null
sleep 1

echo "▶ 2/5  실행기 자가검증"
python3 scripts/remote_cmd_watch.py --selftest || { echo "⛔ 자가검증 실패 — 설치 중단"; exit 1; }

echo "▶ 3/5  LaunchAgent 등록"
for L in "${LABELS[@]}"; do
  cp "$ROOT/scripts/launchd/$L.plist" "$AGENTS/$L.plist"
  launchctl bootout "gui/$UID_N/$L" 2>/dev/null
  if ! launchctl bootstrap "gui/$UID_N" "$AGENTS/$L.plist" 2>/dev/null; then
    launchctl load -w "$AGENTS/$L.plist" 2>/dev/null
  fi
  launchctl enable "gui/$UID_N/$L" 2>/dev/null
  echo "   등록: $L"
done

echo "▶ 4/5  기동 대기"
sleep 5

echo "▶ 5/5  확인"
echo "--- launchctl ---"
launchctl list | grep atnown || echo "   (없음)"
echo "--- 프로세스 ---"
pgrep -lf "remote_cmd_watch|codex_dispatch|cowork_multi" || echo "   ⛔ 아무것도 안 뜸"

echo
echo "══════════════════════════════════════════"
if pgrep -f remote_cmd_watch.py >/dev/null; then
  echo "✅ 원격 연결 열렸습니다."
  echo "   이제 코워크 전략실이 맥에서 명령을 돌릴 수 있습니다."
  echo "   허용 명령: python3 scripts/remote_cmd_watch.py --list"
  echo "   기록:      logs/remote_cmd.log"
  echo "   끄려면:    launchctl bootout gui/$UID_N/com.atnown.remote-cmd"
else
  echo "⛔ 실행기가 안 떴습니다. logs/remote-cmd.err 를 보내주세요."
fi
echo "══════════════════════════════════════════"
