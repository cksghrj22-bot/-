# -*- coding: utf-8 -*-
"""HTML 렌더 — 스케줄(캘린더)과 준비물 문서를 순수 문자열로 만든다."""
import calendar, datetime
from . import spec
from .prep_data import TEACHERS, MENS


def _esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


# ── 캘린더 ────────────────────────────────────────────
def render_calendar(DATA):
    def month_html(y, m):
        cal = calendar.Calendar(firstweekday=6); rows = ''
        for wk in cal.monthdatescalendar(y, m):
            cells = ''
            for d in wk:
                if d.month != m:
                    cells += '<td class="pad"></td>'; continue
                cls = 'day off' if d.weekday() in (0, 5) else 'day'
                inner = f'<div class="dn">{d.day}</div>'
                for label, key, lvt in DATA.get(d, []):
                    bd = f'<b class="lvb">{lvt}</b>' if lvt else ''
                    inner += f'<span class="ev" style="background:{spec.COL[key]};color:#fff;">{bd}{_esc(label)}</span>'
                cells += f'<td class="{cls}">{inner}</td>'
            rows += f'<tr>{cells}</tr>'
        return (f'<div class="mcal"><div class="mtitle">2026 · {m}월</div>'
                '<table class="mc"><thead><tr><th class="sun">일</th><th>월</th><th>화</th>'
                '<th>수</th><th>목</th><th>금</th><th class="sat">토</th></tr></thead>'
                f'<tbody>{rows}</tbody></table></div>')

    months = ''.join(month_html(2026, m) for m in (8, 9, 10, 11, 12))
    legend = ''.join(f'<span class="lg"><i style="background:{c}"></i>{n}</span>' for n, c in
        [('창엽 (커트 L1·2)', spec.COL['창엽']), ('이호 (커트 L3~5)', spec.COL['이호']),
         ('차노 (미감·디자인방법)', spec.COL['차노']), ('신후 (열펌·룩북)', spec.COL['신후']),
         ('성희 (콜드펌)', spec.COL['성희']), ('보미 (업스타일)', spec.COL['보미']),
         ('와이 (맨즈 STAGE)', spec.COL['와이']),
         ('모델데이', spec.COL['모델']), ('특강 (3째주 금)', spec.COL['특강']), ('입봉시험', spec.COL['시험'])])
    return f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>앳나운 교육 일정 캘린더 2026 (8~12월)</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
:root{{--cream:#F7F5F1;--ink:#141414;--gold:#A8895E;--gray:#8f887c;--line:#E4DFD6;}}
body{{background:#e8e5df;color:var(--ink);font-family:-apple-system,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;padding:24px 14px;}}
.wrap{{max-width:1180px;margin:0 auto;}}
.head{{background:var(--ink);color:var(--cream);border-radius:3px;padding:22px 28px;margin-bottom:12px;}}
.head .eye{{font-size:11px;letter-spacing:.24em;color:var(--gold);font-weight:700;}}
.head h1{{font-size:23px;font-weight:800;margin:6px 0 4px;}}
.head .sub{{font-size:12.5px;color:#c9c3b7;}}
.legend{{background:var(--cream);border:1px solid var(--line);border-radius:3px;padding:13px 18px;margin-bottom:14px;display:flex;flex-wrap:wrap;gap:10px 16px;}}
.lg{{display:inline-flex;align-items:center;gap:7px;font-size:12px;font-weight:700;}}
.lg i{{width:15px;height:15px;border-radius:4px;display:inline-block;}}
.mcal{{background:var(--cream);border:1px solid var(--line);border-radius:3px;padding:16px 18px;margin-bottom:14px;}}
.mtitle{{font-size:19px;font-weight:800;margin-bottom:11px;}}
.mc{{width:100%;border-collapse:collapse;table-layout:fixed;}}
.mc th{{font-size:11px;font-weight:800;color:var(--gray);padding:6px 0;border-bottom:2px solid var(--ink);}}
.mc th.sun{{color:#c25b5b;}} .mc th.sat{{color:#5b7ac2;}}
.mc td{{border:1px solid var(--line);vertical-align:top;height:78px;padding:5px 6px;background:#fff;}}
.mc td.pad{{background:transparent;border:none;}}
.mc td.off{{background:#f0ede7;}}
.dn{{font-size:11px;font-weight:800;color:#9b958c;margin-bottom:3px;}}
.ev{{display:block;font-size:9.5px;font-weight:800;border-radius:3px;padding:2px 5px;margin-top:3px;line-height:1.25;}}
.ev .lvb{{background:rgba(255,255,255,.28);border-radius:3px;padding:0 3px;margin-right:3px;font-size:8.5px;}}
.note{{font-size:12px;color:#555;background:var(--cream);border:1px solid var(--line);border-radius:3px;padding:12px 16px;line-height:1.7;margin-bottom:14px;}}
.foot{{text-align:center;font-size:10px;letter-spacing:.3em;color:#b7b1a6;font-weight:700;margin:18px 0 4px;}}
@media(max-width:820px){{.mc td{{height:auto;}}.ev{{font-size:9px;}}}}
</style></head>
<body><div class="wrap">
<div class="head"><div class="eye">AT NOWN · EDUCATION SCHEDULE 2026</div>
<h1>교육 일정 캘린더 — 8월 2째주 ~ 12월</h1>
<div class="sub">정규교육 <b>8/10 ~ 12/6</b> (입봉시험 12/21 앞) · 아침 {spec.MORNING} · 월·토 휴무 · 맨즈(옴므) 별도</div></div>
<div class="legend">{legend}</div>
<div class="note">· <b>선생님별로 전 구간(8월~12월 첫주)에 넓게 펼침</b> — 한 사람이 특정 달·요일에 몰리지 않게 로또식 배분.<br>· <b>레벨이 다르면 같은 날 중복 가능</b> — 과목마다 레벨(L1~L5) 태그. 같은 레벨은 같은 날 겹치지 않게, 다른 레벨은 병행. 칸 앞 작은 L태그가 레벨.<br>· <b>저녁 모델작업은 실제 있는 날만</b> — 모델데이(2·4주 금). 특강은 3째주 금. 이벤트 금요일엔 정규수업 미편성.</div>
{months}
<div class="foot">A T &nbsp; N O W N &nbsp;·&nbsp; 8 ~ 12 월 교육 일정</div>
</div></body></html>'''


# ── 준비물·과제·주의 (시즈 배포용) ────────────────────
def _prep_block(name, sub, color, rows):
    h = (f'<section class="tsec"><div class="thead" style="border-left:6px solid {color}">'
         f'<div class="tname" style="color:{color}">{_esc(name)}<span class="cnt">{len(rows)}과목</span></div>'
         f'<div class="tsub">{_esc(sub)}</div></div><div class="rows">')
    for i, (g, prep, hw, warn) in enumerate(rows, 1):
        h += (f'<div class="row"><div class="rnum" style="background:{color}">{i:02d}</div>'
              f'<div class="rbody"><div class="rtitle">{_esc(g)}</div><div class="rgrid">'
              f'<div class="cell"><span class="lab lab-p">준비물</span><span class="txt">{_esc(prep)}</span></div>'
              f'<div class="cell"><span class="lab lab-h">과제</span><span class="txt">{_esc(hw)}</span></div>'
              f'<div class="cell"><span class="lab lab-w">주의</span><span class="txt">{_esc(warn)}</span></div>'
              f'</div></div></div>')
    return h + '</div></section>'


def render_prep():
    total = sum(len(r) for _, _, _, r in TEACHERS) + len(MENS[3])
    body = ''.join(_prep_block(*t) for t in TEACHERS) + _prep_block(*MENS)
    nav = ''.join(f'<span class="chip" style="--c:{c}">{_esc(n)}</span>'
                  for n, _, c, _ in list(TEACHERS) + [MENS])
    return f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>과목별 준비물·과제·주의사항 (선생님별 · 시즈 배포용)</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
:root{{--cream:#F7F5F1;--ink:#1c1a17;--gold:#A8895E;--line:#E4DFD6;--gray:#6a655c;}}
body{{background:#efece6;color:var(--ink);font-family:-apple-system,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;line-height:1.5;padding:24px 14px 60px;}}
.wrap{{max-width:920px;margin:0 auto;}}
.head{{background:var(--ink);color:var(--cream);border-radius:14px;padding:26px 28px;margin-bottom:16px;}}
.head .t{{font-size:11.5px;letter-spacing:.22em;color:var(--gold);font-weight:800;}}
.head h1{{font-size:25px;font-weight:900;margin:7px 0 6px;line-height:1.22;}}
.head p{{font-size:13.5px;color:#d7d1c6;}}
.note{{background:#fff7e8;border:1px solid #e8d9b0;border-radius:11px;padding:12px 15px;font-size:12.5px;color:#7a6a3c;font-weight:600;margin-bottom:16px;}}
.nav{{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:18px;}}
.chip{{background:#fff;border:1.5px solid var(--c);color:var(--c);border-radius:20px;padding:5px 13px;font-size:13px;font-weight:800;}}
.tsec{{margin-bottom:22px;}}
.thead{{background:#fff;border:1px solid var(--line);border-radius:12px 12px 0 0;padding:14px 18px;}}
.tname{{font-size:19px;font-weight:900;display:flex;align-items:center;gap:10px;}}
.tname .cnt{{font-size:11.5px;font-weight:800;color:#fff;background:var(--gray);border-radius:11px;padding:2px 9px;}}
.tsub{{font-size:12.5px;color:var(--gray);font-weight:600;margin-top:3px;}}
.rows{{background:#fff;border:1px solid var(--line);border-top:0;border-radius:0 0 12px 12px;overflow:hidden;}}
.row{{display:flex;gap:12px;padding:13px 16px;border-top:1px solid var(--line);}}
.row:first-child{{border-top:0;}}
.rnum{{flex-shrink:0;width:30px;height:30px;border-radius:8px;color:#fff;font-weight:900;font-size:13px;display:flex;align-items:center;justify-content:center;}}
.rbody{{flex:1;min-width:0;}}
.rtitle{{font-size:15.5px;font-weight:900;margin-bottom:7px;}}
.rgrid{{display:flex;flex-direction:column;gap:5px;}}
.cell{{display:flex;gap:8px;align-items:flex-start;}}
.lab{{flex-shrink:0;font-size:11px;font-weight:800;border-radius:6px;padding:2px 8px;color:#fff;min-width:46px;text-align:center;}}
.lab-p{{background:#3F6F5F;}} .lab-h{{background:#B5793A;}} .lab-w{{background:#B5563F;}}
.txt{{font-size:13px;color:#3a362f;}}
.foot{{text-align:center;font-size:11.5px;color:#8f887c;font-weight:700;margin-top:22px;letter-spacing:.04em;}}
@media(max-width:600px){{.rtitle{{font-size:14.5px;}}.txt{{font-size:12.5px;}}}}
</style></head>
<body><div class="wrap">
<div class="head"><div class="t">AT NOWN · 2026 EDUCATION</div>
<h1>과목별 준비물 · 과제 · 주의사항</h1>
<p>선생님별 정리 · 시즈(인턴) 배포용 · 총 {total}과목</p></div>
<div class="note">⚠️ <b>시안(초안)</b> — 과목명은 교육 캘린더와 100% 일치하지만, 준비물·과제·주의 내용은 현장 표준 기준으로 짠 초안입니다. <b>각 선생님이 실제 수업 기준으로 검수·확정</b>한 뒤 배포하세요.</div>
<div class="nav">{nav}</div>
{body}
<div class="foot">A T &nbsp; N O W N &nbsp;·&nbsp; 준비물은 수업 <b>전날</b>까지 · 과제는 다음 수업 <b>시작 전</b> 제출</div>
</div></body></html>'''
