#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
남겨.py — 내가 무엇을 했는지 한 줄 남긴다 (2026-08-11 신설)
  python3 ~/atnown-trunk/scripts/남겨.py B "시니어편 본진 렌더 완료 · 검사 13항목 통과"
쌓기만 한다. 지우지 않는다. 못 한 것도 남긴다.
"""
import os, sys, datetime

if len(sys.argv) < 3:
    raise SystemExit('쓰는 법: 남겨.py <방코드> "한 줄로 뭘 했는지"')

room = sys.argv[1].strip().upper()
text = " ".join(sys.argv[2:]).strip()
if len(text) > 200:
    raise SystemExit("한 줄로 써라. 200자를 넘겼다 (%d자)" % len(text))

P = os.path.expanduser("~/atnown-content-pipeline")
p = os.path.join(P, "_ROOMS_LOG.md")
now = datetime.datetime.now().strftime("%m-%d %H:%M")
line = "- `%s` **%s방** — %s\n" % (now, room, text)

head = "# 방 기록 — 쌓기만 한다\n\n> 일 끝나면 한 줄 남긴다. 못 한 것도 남긴다.\n> 읽을 때는 `읽어.py`\n\n"
if os.path.exists(p):
    s = open(p, encoding="utf-8").read()
    i = s.find("\n\n", s.find("읽어.py")) if "읽어.py" in s else -1
    s = (s[:i+2] + line + s[i+2:]) if i > 0 else (head + line + s)
else:
    s = head + line
open(p, "w", encoding="utf-8").write(s)
print("남겼다 · %s" % line.strip())
