#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""필름룩 그레이딩 — 사진/영상 공용.
확정값은 shorts_config.json > grades / defaults_grade 에서만 읽는다. 여기 하드코딩 금지.

  python3 scripts/film_grade.py IN [OUT] [--grade warm_film|clean|faded|bw] [--measure]
  python3 scripts/film_grade.py _intray_헤어사진/ _out/필름/ --grade warm_film
"""
import argparse, json, os, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
CFG  = json.load(open(ROOT/"shorts_config.json", encoding="utf-8"))
GRADES = CFG["grades"]; DEF = CFG["defaults_grade"]
IMG = {".jpg",".jpeg",".png",".webp"}; VID = {".mp4",".mov",".m4v"}

def default_grade(p):
    return DEF["photo"] if pathlib.Path(p).suffix.lower() in IMG else DEF["video"]

def measure(p):
    from PIL import Image; import numpy as np
    a = np.asarray(Image.open(p).convert("RGB")).astype(float)
    r,g,b = a[...,0],a[...,1],a[...,2]
    mx,mn = a.max(2), a.min(2)
    sat = (np.where(mx>0,(mx-mn)/np.maximum(mx,1),0)*100).mean()
    lum = 0.299*r+0.587*g+0.114*b
    bp = np.percentile(lum,5)
    return dict(sat=sat, black=bp, contrast=np.percentile(lum,95)-bp, rb=(r-b).mean())

def grade_one(src, dst, name):
    vf = GRADES[name]["vf"]
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg","-y","-v","error","-i",str(src),"-vf",vf]
    if src.suffix.lower() in IMG: cmd += ["-q:v","2"]
    else: cmd += ["-c:v","libx264","-crf","18","-preset","medium","-c:a","copy"]
    subprocess.run(cmd+[str(dst)], check=True)
    return dst

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("dst", nargs="?")
    ap.add_argument("--grade"); ap.add_argument("--measure", action="store_true")
    a = ap.parse_args()
    src = pathlib.Path(a.src)
    srcs = sorted(f for f in src.iterdir() if f.suffix.lower() in IMG|VID) if src.is_dir() else [src]
    if not srcs: sys.exit("소스 없음: %s" % src)
    for s in srcs:
        name = a.grade or default_grade(s)
        if name not in GRADES: sys.exit("모르는 grade: %s (%s)" % (name, list(GRADES)))
        if a.dst: d = pathlib.Path(a.dst)/(s.stem+"_"+name+s.suffix) if src.is_dir() or pathlib.Path(a.dst).is_dir() else pathlib.Path(a.dst)
        else:     d = s.with_name(s.stem+"_"+name+s.suffix)
        grade_one(s, d, name)
        line = "%s  ->  %s   [%s]" % (s.name, d.name, GRADES[name]["label"])
        if a.measure and d.suffix.lower() in IMG:
            m = measure(d)
            line += "\n    채도 %.1f · 블랙 %.1f · 대비 %.0f · RB %+.1f" % (m["sat"],m["black"],m["contrast"],m["rb"])
        print(line)

if __name__ == "__main__":
    main()
