#!/usr/bin/env python3
"""별칭 충돌 정리 (2026-08-17 전략실)

사고: 차노가 예전부터 쓰던  alias 본진='cd ~/... && caffeinate claude'  가 있었는데,
      전략실이 같은 이름으로 메뉴 별칭을 덧붙였다. zsh 는 뒤엣것이 이기므로
      차노의 「본진 = 클로드 코드 띄우기」가 조용히 바뀌어 버렸다.
      방 규약: 「형이 준 이름이 정본」 → 본진은 원래 뜻으로 되돌리고, 메뉴는 다른 이름으로.
"""
import re, shutil, time
from pathlib import Path

HOME = Path.home()
rc = HOME / ".zshrc"
MENU = HOME / "atnown-content-pipeline" / "scripts" / "menu.sh"
ORIG = "cd ~/atnown-content-pipeline && caffeinate claude"

txt = rc.read_text(errors="ignore")
shutil.copy2(rc, rc.with_name(f".zshrc.bak.{int(time.time())}"))

drop = re.compile(r"^\s*alias\s+(본진|bj|메뉴)\s*=")
mark = re.compile(r"^\s*#\s*(>>>|<<<)\s*본진 메뉴")
kept, removed = [], []
for l in txt.splitlines():
    if drop.match(l) or mark.match(l):
        removed.append(l.strip())
    else:
        kept.append(l)

block = (
    "\n# >>> 본진 별칭 (전략기획및개인업무 방 · 2026-08-17 정리)\n"
    f"alias 본진='{ORIG}'          # 차노 원본 — 클로드 코드 띄우기\n"
    f"alias 메뉴='zsh {MENU}'      # 상태·재시작·로그 메뉴\n"
    f"alias bj='zsh {MENU}'        # 메뉴 영문판 (폰에서 자판 안 바꾸려고)\n"
    "# <<< 본진 별칭\n"
)
rc.write_text("\n".join(kept).rstrip("\n") + "\n" + block)

print("지운 줄:")
for r in removed:
    print("  -", r)
print("\n지금 상태:")
print("  본진  → 클로드 코드 (차노 원본 복구)")
print("  메뉴  → 상태·재시작·로그")
print("  bj    → 메뉴와 같음")
print(f"\n백업: {rc.name}.bak.*")
