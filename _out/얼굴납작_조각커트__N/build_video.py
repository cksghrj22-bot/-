# -*- coding: utf-8 -*-
"""단발매니펌 낙타 5장 — 영상 슬라이드.
자막은 nakta_post.build_overlay 가 그린다(스틸과 같은 코드). 무음. 속도 조작 없음."""
import subprocess, sys, pathlib, json
sys.path.insert(0, "scripts/cards")
import nakta_post as NP

SRC = pathlib.Path("_clips_pool/단발매니펌")
OUT = pathlib.Path("_out/얼굴납작_조각커트__N")
TMP = pathlib.Path("_tmp/_danbal_ov"); TMP.mkdir(parents=True, exist_ok=True)
W, H = 1080, 1350

# (클립, 시작초, 길이초, 크롭중심, top, 문안)   길이 None = 원본 그대로
PLAN = [
 ("IMG_2721.MOV", 0.60, 4.0, 0.42, 0.06,
   [("설정","거울 봤을 때, 머리가 혹은 얼굴이 납작해 보이지 않나요?"),
    ("결론","커트 문제일 확률이 높습니다.")]),
 ("IMG_2720.MOV", 0.00, None, 0.45, 0.62,   # 차노 「그냥 쭈욱 길게」 → 13.08초 원본 전체
   [("설정","동양인의 두상은 대부분 납작하기때문에"),
    ("결론","이점에 유의하여 커트하면 충분히 보완 할 수 있습니다.")]),
 ("IMG_2724.MOV", 0.00, None, 0.34, 0.05,
   [("설정","그래서 두상, 헤어를 조각함으로써"),
    ("시안","얼굴의 단점은 가리고 장점은 커버합니다.")]),
 ("IMG_2725.MOV", 0.00, None, 0.42, 0.05,
   [("설정","똑같은 단발이라도"),
    ("결론","이부분을 고려한 단발과 아닌 단발은 움직일때 다릅니다.")]),
 ("quality_restoration_20260816133521220.mp4", 0.00, None, 0.45, 0.66,
   [("시안","사진으로는 안 보입니다."),
    ("결론","움직여야 보이거든요.")]),
]

def dur(p):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                        "-of","default=nw=1:nk=1",str(p)],capture_output=True,text=True)
    return float(r.stdout.strip())

for i,(clip,ss,ln,center,top,lines) in enumerate(PLAN,1):
    src = SRC/clip
    ov_path = TMP/f"ov{i}.png"
    ov, meta = NP.build_overlay((W,H), lines, top=top)
    ov.save(ov_path)
    (OUT/f"slide_{i}.mp4.meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")

    # 4:5 크롭 → 1080x1350 → 자막 오버레이
    vf = (f"crop=iw:iw/0.8:0:max(0\\,min(ih-iw/0.8\\,ih*{center}-iw/1.6)),"
          f"scale={W}:{H}:flags=lanczos,fps=30")
    cmd = ["ffmpeg","-v","error","-ss",str(ss),"-i",str(src),"-i",str(ov_path),
           "-filter_complex",f"[0:v]{vf}[v];[v][1:v]overlay=0:0[o]",
           "-map","[o]","-an"]
    if ln: cmd += ["-t", str(ln)]          # 출력 옵션이어야 한다. 입력 쪽에 붙으면 안 잘린다
    cmd += ["-c:v","libx264","-preset","medium","-crf","18",
            "-pix_fmt","yuv420p","-y",str(OUT/f"slide_{i}.mp4")]
    subprocess.run(cmd,check=True)
    print(f"  {i}. {clip:<44} {dur(OUT/f'slide_{i}.mp4'):.2f}초")

# 이어보기
lst = TMP/"list.txt"
lst.write_text("".join(f"file '{(OUT/f'slide_{i}.mp4').resolve()}'\n" for i in range(1,6)))
subprocess.run(["ffmpeg","-v","error","-f","concat","-safe","0","-i",str(lst),
                "-c","copy","-y",str(OUT/"_이어보기.mp4")],check=True)
print(f"  이어보기 {dur(OUT/'_이어보기.mp4'):.2f}초")
