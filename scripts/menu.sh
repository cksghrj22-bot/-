#!/bin/zsh
# ─────────────────────────────────────────────
#  메뉴 — 폰에서 쓰는 상태/재시작/로그 메뉴
#  긴 명령을 폰 키보드로 치지 않기 위한 것.
#  「본진」은 차노 원본(cd+caffeinate claude). 이건 「메뉴」/「bj」로 부른다.
#  설치:  zsh ~/atnown-content-pipeline/scripts/setup_menu.sh
# ─────────────────────────────────────────────
ROOT="$HOME/atnown-content-pipeline"
cd "$ROOT" 2>/dev/null || { echo "⛔ $ROOT 없음"; exit 1; }

line() { echo "──────────────────────"; }

상태() {
  line; echo "🖥  데몬"
  for p in codex_dispatch cowork_multi remote_cmd blog_watcher; do
    if pgrep -f "$p" >/dev/null 2>&1; then echo "  ✅ $p"; else echo "  ⛔ $p"; fi
  done
  line; echo "📦 깃"
  echo "  미커밋 $(git status --short 2>/dev/null | wc -l | tr -d ' ')개"
  echo "  $(git log --oneline -1 2>/dev/null)"
  line; echo "📮 주문서"
  echo "  대기 $(ls _terminal_inbox/TASK_*.json 2>/dev/null | wc -l | tr -d ' ')  ·  실패 $(ls _terminal_inbox/_failed/*.json 2>/dev/null | wc -l | tr -d ' ')"
  line; echo "⚠️  알림"
  tail -3 _ALERT.md 2>/dev/null | sed 's/^/  /'
  line
}

재시작() {
  echo "무엇을? 1)디스패처 2)멀티워치 3)둘다"
  printf "> "; read t
  restart_one() {
    launchctl kickstart -k "gui/$(id -u)/com.atnown.$1" 2>/dev/null \
      || { pkill -f "$2"; sleep 1; (cd "$ROOT" && nohup python3 "scripts/$2" --daemon >> "logs/$1.out" 2>&1 &); }
    echo "  → $1 재시작"
  }
  case $t in
    1) restart_one codex-dispatch codex_dispatch.py ;;
    2) restart_one cowork-multi-watch cowork_multi_watch.py ;;
    3) restart_one codex-dispatch codex_dispatch.py; restart_one cowork-multi-watch cowork_multi_watch.py ;;
    *) echo "  취소"; return ;;
  esac
  sleep 3; line; pgrep -lf "codex_dispatch|cowork_multi" || echo "  ⛔ 안 떴음"
}

로그() {
  echo "1)디스패처 2)원격실행기 3)자동커밋 4)알림"
  printf "> "; read t
  case $t in
    1) f=logs/codex_dispatch.log ;;
    2) f=logs/remote_cmd.log ;;
    3) f=_logs/auto_commit.log ;;
    4) f=_ALERT.md ;;
    *) return ;;
  esac
  line; tail -25 "$f" 2>/dev/null || echo "  (파일 없음: $f)"; line
}

주문서() {
  line; echo "📥 대기"
  ls -t _terminal_inbox/TASK_*.json 2>/dev/null | head -5 | xargs -n1 basename 2>/dev/null | sed 's/^/  /' || echo "  (없음)"
  echo "⛔ 실패"
  ls -t _terminal_inbox/_failed/*.json 2>/dev/null | head -5 | xargs -n1 basename 2>/dev/null | sed 's/^/  /' || echo "  (없음)"
  line
}

커밋() {
  n=$(git status --short 2>/dev/null | wc -l | tr -d ' ')
  echo "  미커밋 ${n}개. 커밋할까요? (y/n)"
  printf "> "; read a
  [ "$a" != "y" ] && { echo "  취소"; return; }
  L="$ROOT/.git/index.lock"
  [ -f "$L" ] && { mkdir -p _to_delete/gitlock; mv "$L" "_to_delete/gitlock/index.lock.$(date +%s)"; echo "  (죽은 락 치움)"; }
  git add -A && git commit -m "폰에서 커밋 $(date '+%m-%d %H:%M')" | tail -2
  line; git log --oneline -1
}

클로드() { security unlock-keychain && claude; }

while true; do
  echo ""
  echo "═══════ 본진 ═══════"
  echo " 1  상태"
  echo " 2  데몬 재시작"
  echo " 3  로그"
  echo " 4  주문서"
  echo " 5  커밋"
  echo " 6  클로드 실행"
  echo " 0  나가기"
  printf "> "
  read c
  case $c in
    1) 상태 ;;
    2) 재시작 ;;
    3) 로그 ;;
    4) 주문서 ;;
    5) 커밋 ;;
    6) 클로드; break ;;
    0|q|"") echo "끝"; break ;;
    *) echo "  1~6 또는 0" ;;
  esac
done
