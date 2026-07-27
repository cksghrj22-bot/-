import json, subprocess, sys
CY="/tmp/claude-0/-home-user--/4c303924-cd2a-54ae-bace-87654ed6e323/scratchpad/cy2"
KYOBO="KyoboHandwriting2019"
GAP=1.1
def segs_of(w):
    PADA=0.12;PADB=0.10;out=[];s=w[0]['s']-PADB
    for i in range(len(w)-1):
        if w[i+1]['s']-w[i]['e']>GAP: out.append([max(0,s),w[i]['e']+PADA]);s=w[i+1]['s']-PADB
    out.append([max(0,s),w[-1]['e']+0.3])
    m=[out[0]]
    for a,b in out[1:]:
        if a-m[-1][1]<0.45: m[-1][1]=b
        else: m.append([a,b])
    return m
def mapt(t,segs):
    off=0.0
    for a,b in segs:
        if t<a: return off
        if t<=b: return off+(t-a)
        off+=b-a
    return off
def ts(x):
    h=int(x//3600);m=int(x%3600//60);s=x%60;return f"{h}:{m:02d}:{s:05.2f}"
def build(clip,A,B,h1,h2,outname,crop="1440:1080:240:0"):
    w=json.load(open(f"{CY}/diar_{clip}.json")); segs=segs_of(w)
    words=[(mapt(x['s'],segs)-A,x['t']) for x in w if A<=mapt(x['s'],segs)<=B]
    cues=[];cur=[]
    for lt,t in words:
        cur.append((lt,t)); j=' '.join(z[1] for z in cur)
        if len(j)>=15 or t.strip().endswith(('.','?','!','요','다','까','고','지','네','든','야')):
            cues.append((cur[0][0],cur[-1][0]+0.5,' '.join(z[1] for z in cur).strip()));cur=[]
    if cur: cues.append((cur[0][0],cur[-1][0]+0.6,' '.join(z[1] for z in cur).strip()))
    DUR=B-A
    head=f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: t1,{KYOBO},82,&H0000D7FF,&H00000000,&H00000000,-1,1,7,2,8,40,40,120,1
Style: t2,{KYOBO},82,&H00FFFFFF,&H00000000,&H00000000,-1,1,7,2,8,40,40,270,1
Style: cap,{KYOBO},86,&H00FFFFFF,&H00202020,&H00000000,-1,1,7,2,2,50,50,540,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,{ts(0)},{ts(DUR)},t1,,0,0,0,,{h1}
Dialogue: 0,{ts(0)},{ts(DUR)},t2,,0,0,0,,{h2}
"""
    body=""
    for s0,e0,txt in cues:
        if len(txt)>15:
            mid=len(txt)//2; sp=txt.rfind(' ',0,mid+3)
            if sp>3: txt=txt[:sp]+"\\N"+txt[sp+1:]
        body+=f"Dialogue: 0,{ts(s0)},{ts(e0)},cap,,0,0,0,,{txt}\n"
    ass=f"{CY}/_{outname}.ass"; open(ass,"w",encoding="utf-8").write(head+body)
    subprocess.run(["ffmpeg","-v","error","-y","-ss",str(A),"-t",str(DUR),"-i",f"{CY}/hq_{clip}.mp4",
        "-i","/home/user/-/shorts/assets/bgm_piano_long.mp3","-filter_complex",
        f"color=c=black:s=1080x1920:d={DUR}[bg];[0:v]crop={crop},scale=1080:810,setsar=1[v];[bg][v]overlay=0:640[b1];[b1]subtitles={ass}[vout];[1:a]volume=0.14,afade=t=out:st={DUR-1.5}:d=1.5[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=0[aout]",
        "-map","[vout]","-map","[aout]","-c:v","libx264","-preset","medium","-crf","19","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-r","30","-shortest",f"{CY}/{outname}.mp4"],check=True)
    d=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f"{CY}/{outname}.mp4"],capture_output=True,text=True).stdout.strip()
    print(f"{outname}: {d}s · {len(cues)}큐",flush=True)
if __name__=="__main__":
    # 2번: 무게감/디스커넥션
    build("9005",68.0,98.0,"머리 무게감 빼는 법","디스커넥션의 원리","창엽쇼츠_02_무게감")
