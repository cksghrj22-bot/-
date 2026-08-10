#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""화면 붙잡기 — 짧은 컷이 연달아 나오면 앞 클립을 이어서 쓴다.
왜(2026-08-09 형 지시): "b롤이 너무 빨리빨리 넘어가서 시각적으로 정신없다."
자막은 문장마다 바뀌어도 된다. 화면까지 같이 바뀌면 눈이 못 쉰다.
글자수로 그 비트가 몇 초짜리인지 어림잡아, HOLD_MIN 초에 못 미치면 앞 화면을 유지한다.
덤: 필요한 클립 수가 줄어서 클립 부족(SEED1·SEED13)도 같이 풀린다.
"""
import json, glob, os, sys, shutil

HOLD_MIN = 2.8          # 한 화면이 최소 이만큼은 머문다
CPS      = 7.4          # 실측 낭독 속도(글자/초)

def est(say): return max(1.0, len(say or "")/CPS)

def hold(path, apply=True):
    j=json.load(open(path,encoding="utf-8")); beats=j.get("beats",[]); log=[]
    cur=None; acc=0.0
    for i,b in enumerate(beats):
        if b.get("black"):
            cur=None; acc=0.0; continue
        c=b.get("clip")
        if not c: continue
        if cur and acc < HOLD_MIN:
            if c != cur:
                log.append("비트%d %s → %s 유지 (앞 화면 %.1f초밖에 안 됐음)"%(i,c,cur,acc))
                b["clip"]=cur
            acc += est(b.get("say"))
        else:
            cur=c; acc=est(b.get("say"))
    if log and apply:
        if not os.path.exists(path+".bak_hold"): shutil.copy2(path,path+".bak_hold")
        json.dump(j,open(path,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    return os.path.basename(path), log

if __name__=="__main__":
    HERE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pats=sys.argv[1:] or [HERE+"/_jobs/_processing/JOB-*OK.json"]
    for pat in pats:
        for p in sorted(glob.glob(pat)):
            tag,log=hold(p)
            if log:
                print("["+tag+"]")
                for l in log: print("   "+l)
