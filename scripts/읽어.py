#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
읽어.py — 다른 직군들이 뭘 했는지 한 화면에 (2026-08-11 신설)
이찬호: "연결된 모든 직군들이랑은 서로가 서로를 읽어야 한다"
  python3 ~/atnown-trunk/scripts/읽어.py
일을 시작하기 전에 이걸 친다. 찾아.py 와 한 쌍이다.
"""
import os, sys, glob, time, datetime

P = os.path.expanduser("~/atnown-content-pipeline")
T = os.path.expanduser("~/atnown-trunk")
W = 62

def rule(t=""):
    print("\n" + "─" * W)
    if t: print(t); print("─" * W)

def ago(ts):
    d = time.time() - ts
    if d < 3600:  return "%d분 전" % (d // 60)
    if d < 86400: return "%d시간 전" % (d // 3600)
    return "%d일 전" % (d // 86400)

print("═" * W); print("읽어 · 지금 다른 직군들이 무엇을 했나"); print("═" * W)

# 0) 멈춤 — 제일 먼저 본다
stop = os.path.join(P, "_jobs", "_PAUSE_PULLS.stop")
if os.path.exists(stop):
    print("\n⛔ 멈춤 파일이 켜져 있다 — 자동 배선이 조용히 죽어 있다")
    print("   %s  (%s)" % (stop, ago(os.path.getmtime(stop))))
    print("   인트레이 스캔 · 드라이브 풀 · 알림 · 노션 동기화가 전부 안 돈다")
else:
    print("\n자동 배선 멈춤 없음")

# 1) 방 현황
rule("방 현황")
p = os.path.join(P, "_ROOMS.md")
if os.path.exists(p):
    for ln in open(p, encoding="utf-8"):
        if ln.startswith("|") and "---" not in ln: print("  " + ln.rstrip())
else:
    print("  _ROOMS.md 없음")

# 2) 최근 기록
rule("최근 기록 (누가 무엇을 했나)")
p = os.path.join(P, "_ROOMS_LOG.md")
if os.path.exists(p):
    n = 0
    for ln in open(p, encoding="utf-8"):
        if ln.strip().startswith("-"):
            print("  " + ln.rstrip()); n += 1
            if n >= 12: break
    if n == 0: print("  아직 남긴 게 없다")
else:
    print("  _ROOMS_LOG.md 없음 — 남겨.py 를 한 번이라도 쓰면 생긴다")

# 3) 잠긴 주제
rule("잠긴 주제 (손대지 마라)")
lk = glob.glob(os.path.join(P, "_jobs", "_lock", "*"))
if lk:
    for f in lk:
        b = os.path.basename(f)
        print("  %-30s %s" % (b, ago(os.path.getmtime(f))))
else:
    print("  없음")

# 4) 본진이 마지막으로 만든 것
rule("본진이 마지막으로 만든 것")
mp4 = sorted(glob.glob(os.path.join(P, "_jobs", "_done", "*.mp4")),
             key=os.path.getmtime, reverse=True)[:5]
if mp4:
    for f in mp4:
        print("  %-34s %s" % (os.path.basename(f)[:34], ago(os.path.getmtime(f))))
else:
    print("  없음")

# 5) 대기 중인 잡
rule("대기 중인 잡")
jb = glob.glob(os.path.join(P, "_jobs", "*.json"))
if jb:
    for f in sorted(jb, key=os.path.getmtime, reverse=True)[:6]:
        print("  %-34s %s" % (os.path.basename(f)[:34], ago(os.path.getmtime(f))))
else:
    print("  없음 — 큐가 비어 있다")

# 6) 주간 숫자
rule("주간 피드백")
rp = sorted(glob.glob(os.path.join(P, "_reports", "weekly_*.md")), reverse=True)
if rp:
    print("  %s (%s)" % (os.path.basename(rp[0]), ago(os.path.getmtime(rp[0]))))
    for ln in open(rp[0], encoding="utf-8"):
        if "팔로워" in ln or "구독" in ln: print("  " + ln.strip())
else:
    print("  아직 없음")

print("\n" + "═" * W)
print("일 끝나면:  python3 ~/atnown-trunk/scripts/남겨.py <방코드> \"한 줄\"")
print("═" * W)
