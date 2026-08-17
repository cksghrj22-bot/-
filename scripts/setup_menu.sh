#!/bin/zsh
# 본진 메뉴 등록 — 한 번만 실행
# ~/.zshrc 에 넣으므로 맥 터미널·폰 SSH 양쪽에서 똑같이 먹는다.
# ⚠️ 「본진」은 차노 원본 alias — 건드리지 않는다. 메뉴는 「메뉴」/「bj」로만.
RC="$HOME/.zshrc"
TARGET="$HOME/atnown-content-pipeline/scripts/menu.sh"
MARK="# >>> 본진 별칭"

[ -f "$TARGET" ] || { echo "⛔ menu.sh 없음: $TARGET"; exit 1; }
touch "$RC"

if grep -q "scripts/menu.sh" "$RC" 2>/dev/null; then
  echo "✅ 이미 등록돼 있습니다."
else
  {
    printf '\n%s (전략기획및개인업무 방 · %s 정리)\n' "$MARK" "$(date +%Y-%m-%d)"
    printf "alias 본진='cd ~/atnown-content-pipeline && caffeinate claude'          # 차노 원본 — 클로드 코드 띄우기\n"
    printf "alias 메뉴='zsh %s'      # 상태·재시작·로그 메뉴\n" "$TARGET"
    printf "alias bj='zsh %s'        # 메뉴 영문판 (폰에서 자판 안 바꾸려고)\n" "$TARGET"
    printf '# <<< 본진 별칭\n'
  } >> "$RC"
  echo "✅ 등록 완료 → $RC"
fi

echo ""
echo "───────────────────────────"
echo " 지금 바로 쓰려면 한 줄:"
echo ""
echo "   source ~/.zshrc"
echo ""
echo " 그 다음부터 언제든:"
echo "   본진   → 클로드 코드 (차노 원본)"
echo "   메뉴   → 상태/재시작/로그 메뉴"
echo "   bj     → 메뉴 영문판"
echo ""
echo " 맥 터미널·폰 SSH 둘 다 됩니다."
echo "───────────────────────────"
