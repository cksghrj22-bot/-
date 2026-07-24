# 제출 전 자가검사 게이트 — 통과 못 하면 형께 절대 안 보냄. (2026-07-24 이찬호 "필터링 2회 안 거치고 실수 반복")
import subprocess, sys, json
from pathlib import Path

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

def probe_dur(f):
    return float(run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f]).stdout.strip() or 0)

def mean_vol(f, ss=None, t=None):
    cmd = ["ffmpeg","-hide_banner"]
    if ss is not None: cmd += ["-ss",str(ss)]
    if t is not None: cmd += ["-t",str(t)]
    cmd += ["-i",f,"-af","volumedetect","-f","null","-"]
    out = run(cmd).stderr
    for line in out.splitlines():
        if "mean_volume" in line:
            return float(line.split("mean_volume:")[1].split("dB")[0])
    return -99.0

def qc(f, exp_dur=None):
    fails = []
    # 1. 디코드 무결성
    err = run(["ffmpeg","-v","error","-i",f,"-f","null","-"]).stderr.strip()
    if err: fails.append(f"디코드에러: {err[:120]}")
    dur = probe_dur(f)
    # 2. 길이
    if exp_dur and abs(dur-exp_dur) > 1.0: fails.append(f"길이 {dur:.1f}≠기대 {exp_dur:.1f}")
    # 2b. ⭐비디오 프레임수 = 길이와 일치(중간 잘림/프리즈 방지). fps30 기준 frames ≥ dur*29
    nf = run(["ffprobe","-v","error","-count_frames","-select_streams","v","-show_entries","stream=nb_read_frames","-of","csv=p=0",f]).stdout.strip()
    try: nf = int(nf)
    except: nf = 0
    if nf < dur*29 - 5: fails.append(f"⚠️영상 잘림: 프레임 {nf}개 = {nf/30:.1f}초뿐(길이 {dur:.1f}초) — 중간 프리즈")
    # 3. 나레이션 레벨(전체 mean) ≥ -20
    m = mean_vol(f)
    if m < -20: fails.append(f"소리 작음 mean {m:.1f}dB(<-20)")
    # 4. BGM 존재: 끝 1.5초(아웃트로=BGM only) 무음 아님(≥ -34dB)
    tail = mean_vol(f, ss=max(0,dur-1.5), t=1.4)
    if tail < -34: fails.append(f"BGM 안 들림/무음 꼬리 tail {tail:.1f}dB(<-34)")
    ok = not fails
    print(f"{'✅PASS' if ok else '❌FAIL'} {Path(f).name} dur={dur:.1f} mean={m:.1f} tail(BGM)={tail:.1f}")
    for x in fails: print("   -", x)
    return ok, {"dur":dur,"mean":m,"tail":tail,"fails":fails}

if __name__ == "__main__":
    allok = True
    for f in sys.argv[1:]:
        ok,_ = qc(f)
        allok = allok and ok
    print("=== ALL PASS ===" if allok else "=== 실패 있음 — 제출 금지 ===")
    sys.exit(0 if allok else 1)
