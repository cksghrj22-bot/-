#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""브리지 자동 수리 — 기계적으로 확실한 것만 고친다.
① 클립 중복 → 같은 계열(접두어) 미사용 클립으로 교체
② 검정 연속 → 뒤쪽 검정을 클립 비트로 전환
사람 판단이 필요한 것(대본 쪼개기·AI말투·클립 부족)은 건드리지 않고 보고만 한다.
"""
import json, os, re, glob, sys, shutil

MAC="/Users/chanho/atnown-content-pipeline"
HERE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def real(p): return p.replace(MAC,HERE) if p else p
def fam(n): 
    m=re.match(r"([a-zA-Z_]+)", n or ""); return m.group(1) if m else ""

def fix(path, apply=True):
    j=json.load(open(path,encoding="utf-8")); tag=os.path.basename(path)
    beats=j.get("beats",[]); log=[]
    d=real(j.get("clips_dir","")); 
    pool=sorted(os.path.basename(x) for x in glob.glob(d+"/*.mov")) if os.path.isdir(d) else []
    used=[b.get("clip") for b in beats if b.get("clip")]

    def pick(prefer_fam):
        cand=[c for c in pool if c not in used]
        same=[c for c in cand if fam(c)==prefer_fam]
        return (same or cand or [None])[0]

    # ① 중복 클립 교체 (뒤쪽 것을 바꾼다 — 앞이 원래 자리)
    seen=set()
    for i,b in enumerate(beats):
        c=b.get("clip")
        if not c: continue
        if c in seen:
            nc=pick(fam(c))
            if nc:
                b["clip"]=nc; used.append(nc)
                log.append("비트%d 중복 %s → %s"%(i,c,nc))
            else:
                log.append("비트%d 중복 %s — 교체할 클립이 풀에 없음 ★사람 필요"%(i,c))
        else:
            seen.add(c)

    # ② 연속 검정 끊기 (뒤쪽 검정을 클립으로)
    for i in range(len(beats)-1):
        if beats[i].get("black") and beats[i+1].get("black"):
            nc=pick("")
            if nc:
                beats[i+1]["black"]=False; beats[i+1]["clip"]=nc; used.append(nc)
                log.append("비트%d 연속검정 끊음 → 클립 %s"%(i+1,nc))
            else:
                log.append("비트%d 연속검정 — 쓸 클립 없음 ★사람 필요"%(i+1))

    if log and apply:
        if not os.path.exists(path+".bak_bridge"): shutil.copy2(path, path+".bak_bridge")
        json.dump(j, open(path,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
    return tag, log

if __name__=="__main__":
    pats=sys.argv[1:] or [HERE+"/_jobs/_processing/JOB-*OK.json"]
    for pat in pats:
        for p in sorted(glob.glob(pat)):
            tag,log=fix(p)
            if log:
                print("["+tag+"]")
                for l in log: print("   "+l)
