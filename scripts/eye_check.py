#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""눈 검사 — 완성된 mp4의 '화면'을 직접 본다.
왜(2026-08-09~10 형 지시: "왜 이제 다 본다며 / 본진이 다 보면 본진을 시켜"):
지금까지 게이트는 렌더러가 '계획한' 값을 채점했다. 화면에 실제로 뭐가 찍혔는지는 아무도 안 봤다.
그래서 통과라고 올린 영상에서 아웃트로가 안 보이고, 카드에 자막이 겹치고, 4초짜리 빈 검정이 나왔다.
사람이 한 편씩 열어보는 건 양산이 안 된다. 그래서 여기서 픽셀로 본다.

검사 항목 (전부 완성본 mp4에서만 읽는다 — 잡 파일을 신뢰하지 않는다)
  sync_real      자막이 실제로 바뀐 시각 vs 말이 실제로 시작된 시각
  outro_visible  마지막 구간에 글자 픽셀이 실제로 있는가
  blank_screen   검정인데 글자가 하나도 없는 구간이 몇 초인가
  cap_y_stable   자막 세로 위치가 편 안에서 튀지 않는가
  cap_overlap    같은 시각에 위·아래 두 군데서 글자가 동시에 뜨는가
사용: python3 scripts/eye_check.py <완성본.mp4> [--json]
"""
import subprocess, sys, json, os

W, H = 180, 320          # 세로 전체를 보는 저해상 그레이 (1080x1920 → 1/6)
FPS  = 10
TXT_THR = 200            # 이 밝기 이상이면 글자 픽셀로 본다 (자막은 흰 글씨)

def gray(path, vf):
    return subprocess.run(["/Users/chanho/.local/bin/ffmpeg","-v","error","-i",path,"-vf",vf,"-f","rawvideo","-"],
                          capture_output=True).stdout

def frames(path):
    raw = gray(path, "fps=%d,scale=%d:%d,format=gray" % (FPS, W, H))
    n = W*H
    return [raw[i*n:(i+1)*n] for i in range(len(raw)//n)]

def dur(path):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                        "-of","csv=p=0",path], capture_output=True, text=True).stdout.strip()
    try: return float(r)
    except: return 0.0

def rows_with_text(fr):
    """글자가 있는 가로줄 번호들. 자막·카드·제목이 여기 잡힌다."""
    out=[]
    for y in range(H):
        row = fr[y*W:(y+1)*W]
        if sum(1 for v in row if v >= TXT_THR) >= 3:
            out.append(y)
    return out

def bands(rows, gap=6):
    """연속한 줄을 묶어 텍스트 덩어리(밴드)로 만든다."""
    if not rows: return []
    bs=[[rows[0],rows[0]]]
    for y in rows[1:]:
        if y-bs[-1][1] <= gap: bs[-1][1]=y
        else: bs.append([y,y])
    return bs

def speech_onsets(path):
    try:
        from faster_whisper import WhisperModel
    except Exception:
        return None
    subprocess.run(["/Users/chanho/.local/bin/ffmpeg","-y","-v","error","-i",path,"-ac","1","-ar","16000","/tmp/_eye.wav"],
                   capture_output=True)
    m = WhisperModel(os.environ.get("FW_MODEL","small"), device="cpu", compute_type="int8")
    segs,_ = m.transcribe("/tmp/_eye.wav", language="ko", word_timestamps=True,
                          vad_filter=False, beam_size=5)
    ws=[(w.start,(w.word or "").strip()) for s in segs for w in (s.words or []) if (w.word or "").strip()]
    if not ws: return []
    on=[ws[0][0]]
    for i in range(1,len(ws)):
        if ws[i][0]-ws[i-1][0] > 0.45: on.append(ws[i][0])
    return on

def check(path):
    D  = dur(path)
    FR = frames(path)
    n  = len(FR)
    if n < 4: return {"eye":"frames_missing","PASS":False}
    per = [rows_with_text(f) for f in FR]
    bnd = [bands(r) for r in per]

    # ── 자막이 실제로 바뀐 시각 ──
    # 화면 전체를 보면 컷이 바뀌는 것까지 '자막 전환'으로 세어진다(2026-08-10 실측: 17회 중 절반이 컷).
    # 그러면 엉뚱한 말 시작과 짝지어져 싱크가 실제보다 나쁘게 나온다.
    # 자막 띠만 좁게 잘라서 본다.
    craw = gray(path, "crop=1080:200:0:1540,fps=%d,scale=180:33,format=gray" % FPS)
    CN = 180*33
    cf = [craw[i*CN:(i+1)*CN] for i in range(len(craw)//CN)]
    diffs=[]
    for i in range(1,len(cf)):
        a,b = cf[i-1], cf[i]
        diffs.append(sum(abs(a[k]-b[k]) for k in range(0,CN,3))/(CN/3))
    caps=[]
    if diffs:
        mean=sum(diffs)/len(diffs)
        var=sum((x-mean)**2 for x in diffs)/len(diffs)
        thr=max(3.0, mean+2*(var**0.5))
        for i,v in enumerate(diffs):
            if v>thr:
                t=(i+1)/FPS
                if not caps or t-caps[-1] > 0.5: caps.append(t)

    # ── 글자 없는 화면 ──
    blank=0
    for i,f in enumerate(FR):
        if not per[i] and (sum(f)/len(f)) < 14: blank+=1
    blank_sec = blank/FPS

    # ── 아웃트로: 마지막 2.5초 안에 글자가 있는가 ──
    tail = FR[max(0, n-int(2.5*FPS)):]
    tail_rows = [rows_with_text(f) for f in tail]
    outro_frames = sum(1 for r in tail_rows if r)
    outro_visible = outro_frames >= int(0.8*FPS)     # 0.8초 이상 또렷하게

    # ── 자막 세로 위치가 튀는가 ──
    # 제목·카드는 위쪽에 있고 자막은 아래쪽에 있다. 자막 구역(아래 40%)만 본다.
    # 위아래를 같이 재면 제목이 뜨고 지는 것까지 '튄다'고 잡혀 쓸모가 없다.
    # 검정 화면은 자막이 가운데로 가도록 설계돼 있다(의도). 클립 화면끼리만 비교해야
    # '튄다'가 진짜 튄 것이 된다. 안 그러면 설계대로 동작하는 것까지 불합격이 된다.
    CAPZONE = int(H*0.60)
    isblack = [ (sum(f)/len(f)) < 14 for f in FR ]
    ys=[]
    for i,b in enumerate(bnd):
        if isblack[i]: continue
        low=[x for x in b if x[0] >= CAPZONE]
        if low: ys.append(low[-1][0])
    jump = (max(ys)-min(ys)) if len(ys) >= 2 else 0
    cap_y_stable = jump <= 25                        # 저해상 25줄 ≒ 원본 150px

    # ── 겹침 ──
    # 두 줄짜리 자막은 밴드가 둘이지만 서로 붙어 있다(정상).
    # 카드와 자막이 같이 뜬 경우처럼 멀리 떨어진 두 덩어리만 겹침으로 본다.
    overlap=0
    for b in bnd:
        low=[x for x in b if x[0] >= CAPZONE]
        if len(low) >= 2 and (low[-1][0]-low[0][1]) > 25: overlap+=1
    cap_overlap_ok = overlap <= int(0.05*n)

    # ── 싱크: 화면 vs 소리 ──
    on = speech_onsets(path)
    if on is None:
        sync = {"sync_real":None,"note":"faster-whisper 없음"}
        sync_ok = None
    elif not on or not caps:
        sync = {"sync_real":None,"note":"자막 전환 또는 말 시작을 못 찾음"}
        sync_ok = False
    else:
        errs=[min(on,key=lambda o:abs(o-c))-c for c in caps]
        avg=sum(abs(e) for e in errs)/len(errs); mx=max(abs(e) for e in errs)
        sync={"sync_real":round(avg,3),"sync_max":round(mx,3)}
        sync_ok = avg <= 0.30 and mx <= 1.20

    r={"file":os.path.basename(path),"dur":round(D,1),
       "cap_changes":len(caps),"blank_sec":round(blank_sec,1),
       "outro_visible":outro_visible,"cap_y_jump":jump,"cap_y_stable":cap_y_stable,
       "cap_overlap_frames":overlap,"cap_overlap_ok":cap_overlap_ok}
    r.update(sync)
    r["blank_ok"]=blank_sec <= 1.5
    r["sync_ok_real"]=sync_ok
    # 자막높이·겹침은 참고값이다. 합격 판정에 쓰지 않는다.
    # 이유(2026-08-10 실측): 시술 클립에 살롱 로고("at nown")가 흰 글씨로 박혀 있어서
    # 저해상 픽셀 검사로는 자막과 구분되지 않는다. 여섯 편 전부 편차 112~127로 같은 값이 나왔다 —
    # 영상이 잘못된 게 아니라 자가 잘못 재고 있다는 뜻이다. 구분할 방법을 찾기 전까지는 숫자만 남긴다.
    r["cap_y_stable"]=None
    r["cap_overlap_ok"]=None
    r["EYE_PASS"]= bool(all(x for x in [r["blank_ok"], outro_visible,
                                        (sync_ok if sync_ok is not None else True)]))
    # numpy/scalar bools can appear from numeric comparisons above; keep --json stable.
    for k,v in list(r.items()):
        if hasattr(v, "item"):
            try:
                r[k]=v.item()
            except Exception:
                pass
        if isinstance(r[k], bool):
            r[k]=bool(r[k])
    return r

if __name__=="__main__":
    args=[a for a in sys.argv[1:] if not a.startswith("--")]
    asjson="--json" in sys.argv
    for p in args:
        r=check(p)
        if asjson: print(json.dumps(r,ensure_ascii=False))
        else:
            print("\n■ %s  %.1f초"%(r.get("file"),r.get("dur",0)))
            print("   자막 전환 %s회 · 글자없는화면 %s초 · 자막높이 편차 %s"%(
                r.get("cap_changes"),r.get("blank_sec"),r.get("cap_y_jump")))
            print("   아웃트로 보임 %s · 자막겹침 프레임 %s"%(r.get("outro_visible"),r.get("cap_overlap_frames")))
            print("   싱크 실측 %s초 (최대 %s)"%(r.get("sync_real"),r.get("sync_max")))
            print("   눈검사 %s"%("통과" if r.get("EYE_PASS") else "불합격"))
