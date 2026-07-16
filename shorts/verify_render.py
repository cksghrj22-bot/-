"""쇼츠 mind 렌더 전수 검사 — 7개 스펙을 한 번에. 하나라도 실패면 FAIL.
사용: python3 verify_shorts.py <mp4> <ass>"""
import sys, subprocess, re, json

mp4, ass = sys.argv[1], sys.argv[2]
fails = []

def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stderr + subprocess.run(cmd, capture_output=True, text=True).stdout

info = subprocess.run(["ffmpeg","-hide_banner","-i",mp4], capture_output=True, text=True).stderr
# 1) 해상도 1080x1920
if "1080x1920" not in info:
    m=re.search(r"(\d{3,4}x\d{3,4})", info); fails.append(f"해상도 {m.group(1) if m else '?'} (1080x1920 아님)")
# 길이
dm=re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", info)
dur=int(dm[1])*3600+int(dm[2])*60+float(dm[3]) if dm else 0

# 2) 흑백: 25% 지점 프레임 중앙 500x500 채도(SATAVG) 낮아야
t=dur*0.25
sat=subprocess.run(["ffmpeg","-hide_banner","-ss",f"{t:.1f}","-i",mp4,"-vframes","1",
  "-vf","crop=500:500:(iw-500)/2:(ih-500)/2,signalstats,metadata=print:key=lavfi.signalstats.SATAVG",
  "-f","null","-"], capture_output=True, text=True).stderr
sm=re.search(r"SATAVG=([\d.]+)", sat)
satv=float(sm[1]) if sm else 999
if satv > 18: fails.append(f"흑백 아님 (중앙 채도 SATAVG={satv:.1f} > 18)")

# 3) BGM: 마지막 1.2초(나레이션 뒤) RMS 무음 아님
tail=subprocess.run(["ffmpeg","-hide_banner","-ss",f"{max(0,dur-1.2):.1f}","-i",mp4,
  "-af","astats=metadata=1:reset=0","-f","null","-"], capture_output=True, text=True).stderr
rm=re.findall(r"RMS level dB:\s*(-?[\d.]+|-inf)", tail)
rms=[x for x in rm if x!='-inf']
if not rms: fails.append("BGM 없음 (아웃트로 구간 완전 무음)")
elif min(float(x) for x in rms) < -70: fails.append(f"BGM 의심 (tail RMS {min(float(x) for x in rms):.0f}dB)")

# ASS 기반 검사
a=open(ass,encoding="utf-8").read()
styles={ln.split(",")[0].replace("Style: ",""):ln for ln in a.splitlines() if ln.startswith("Style:")}
dialog=[ln for ln in a.splitlines() if ln.startswith("Dialogue:")]

# 4) 폰트 NanumSquareRound (Kyobo/Apple 아님)
for nm in ("Default","Title"):
    if nm in styles and "NanumSquareRound" not in styles[nm]:
        f=styles[nm].split(",")[1]; fails.append(f"{nm} 폰트 {f} (NanumSquareRound 아님)")
# 5) 자막 블랙박스: Default BorderStyle=4
if "Default" in styles and styles["Default"].split(",")[7].strip()!="4":
    fails.append("자막 블랙박스 아님 (BorderStyle≠4)")
# 6) 아웃트로 위치 중앙(alignment 5) + 잘림 없음(끝<=길이)
outro=[d for d in dialog if ",Outro," in d]
if not outro: fails.append("아웃트로 없음")
else:
    al=styles.get("Outro","").split(",")
    if len(al)>=11 and al[10].strip()!="5": fails.append(f"아웃트로 위치 alignment={al[10].strip()} (중앙5 아님)")
    em=re.search(r",(\d+):(\d+):([\d.]+),Outro", outro[-1])
    oend=int(em[1])*3600+int(em[2])*60+float(em[3]) if em else 999
    if oend > dur+0.05: fails.append(f"아웃트로 잘림 (끝 {oend:.1f}s > 영상 {dur:.1f}s)")
# 7) CTA 없음
for w in ("저장","좋아요","구독","팔로우"):
    if w in a: fails.append(f"CTA '{w}' 발견")

print(f"{'❌ FAIL' if fails else '✅ PASS'} {mp4.split('/')[-1][:20]} (길이 {dur:.1f}s, 채도 {satv:.1f})")
for f in fails: print("   -", f)
sys.exit(1 if fails else 0)
