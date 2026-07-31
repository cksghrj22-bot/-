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
<div class="sub">정규교육 <b>8/10 ~ 12/6</b> (입봉시험 12/21 앞) · <b>기본 아침교육 {spec.MORNING}</b> · <b>모델작업은 {spec.EVENING}</b> · 월·토 휴무 · 맨즈(옴므) 별도</div></div>
<div class="legend">{legend}</div>
<div class="note">· <b>기본은 아침 교육 {spec.MORNING}</b>, <b>모델 작업은 {spec.EVENING}</b>.<br>· 특강 = 3째주 금 · 모델데이 = 2·4주 금 · 입봉시험 <b>12/21(월)</b> · 월·토 휴무.<br>· 칸 앞 <b>L1~L5</b>는 과목 레벨 표기.</div>
{months}
<div class="foot">A T &nbsp; N O W N &nbsp;·&nbsp; 8 ~ 12 월 교육 일정</div>
</div></body></html>'''


# ── 선생님별 담당(배포 요약용) ── 사실만: 트랙 성격 + 레벨 범위 ──
ROLES = [
    ('창엽', '커트 기초', 'L1·L2'), ('이호', '커트 디자인·시그니처', 'L3~L5'),
    ('신후', '열펌·룩북', 'L3~L5'), ('성희', '콜드펌', 'L1~L5'),
    ('보미', '업스타일·브레이드', 'L1~L5'), ('차노', '디자인 미감·방법', 'L1~L5'),
    ('와이', '맨즈(옴므) STAGE 0~7', '별도'),
]


def _cal_pieces(DATA):
    """캘린더의 범례·월표를 (legend_html, months_html)로 반환 — 통합본에서 재사용."""
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
    return legend, months


def _level_matrix(DATA):
    """월 × 레벨(L1~L5) 과목 개수 표 HTML — DATA에서 직접 집계(실제 배치와 항상 일치)."""
    import datetime
    from collections import defaultdict, Counter
    mx = defaultdict(Counter)          # month -> {level: count}
    for d, v in DATA.items():
        if not isinstance(d, datetime.date):
            continue
        for label, t, lvt in v:
            if t in ('모델', '특강', '시험') or not lvt:
                continue
            for x in lvt.replace('L', '').split('·'):
                if x != '0':           # 맨즈(L0) 제외
                    mx[d.month][int(x)] += 1
    months = [m for m in (8, 9, 10, 11, 12) if m in mx]
    head = '<tr><th>월</th>' + ''.join(f'<th>L{lv}</th>' for lv in range(1, 6)) + '<th class="sum">합계</th></tr>'
    rows = ''
    coltot = Counter(); grand = 0
    for m in months:
        r = mx[m]; rowsum = sum(r[lv] for lv in range(1, 6)); grand += rowsum
        cells = ''
        for lv in range(1, 6):
            n = r[lv]; coltot[lv] += n
            cells += f'<td class="{"z" if n == 0 else ""}">{n}</td>'
        rows += f'<tr><td class="mo">{m}월</td>{cells}<td class="sum">{rowsum}</td></tr>'
    foot = ('<tr class="tot"><td class="mo">합계</td>'
            + ''.join(f'<td>{coltot[lv]}</td>' for lv in range(1, 6))
            + f'<td class="sum">{grand}</td></tr>')
    return (f'<table class="lvmx"><thead>{head}</thead>'
            f'<tbody>{rows}</tbody><tfoot>{foot}</tfoot></table>')


def _month_total_matrix(DATA):
    """월별 총 수업 개수 종합(과목 실수 = 선생님 기준 합계) HTML."""
    import datetime
    from collections import Counter
    mt = Counter()
    for d, v in DATA.items():
        if not isinstance(d, datetime.date):
            continue
        for label, t, lvt in v:
            if t not in ('모델', '특강', '시험'):
                mt[d.month] += 1
    months = [8, 9, 10, 11, 12]
    head = '<tr><th>구분</th>' + ''.join(f'<th>{m}월</th>' for m in months) + '<th class="sum">합계</th></tr>'
    row = ('<tr><td class="mo">총 수업</td>'
           + ''.join(f'<td>{mt[m]}</td>' for m in months)
           + f'<td class="sum">{sum(mt.values())}</td></tr>')
    return f'<table class="lvmx"><thead>{head}</thead><tbody>{row}</tbody></table>'


def _teacher_month_matrix(DATA):
    """선생님 × 월 수업 개수 표 HTML — DATA에서 직접 집계."""
    import datetime
    from collections import defaultdict, Counter
    tm = defaultdict(Counter)
    for d, v in DATA.items():
        if not isinstance(d, datetime.date):
            continue
        for label, t, lvt in v:
            if t in ('모델', '특강', '시험'):
                continue
            tm[t][d.month] += 1
    months = [8, 9, 10, 11, 12]
    order = [t for t in spec.TEACHERS if t in tm]
    head = '<tr><th>선생님</th>' + ''.join(f'<th>{m}월</th>' for m in months) + '<th class="sum">합계</th></tr>'
    rows = ''; coltot = Counter(); grand = 0
    for t in order:
        r = tm[t]; rowsum = sum(r[m] for m in months); grand += rowsum
        cells = ''
        for m in months:
            n = r[m]; coltot[m] += n
            cells += f'<td class="{"z" if n == 0 else ""}">{n}</td>'
        rows += (f'<tr><td class="mo" style="color:{spec.COL[t]}">{t}</td>{cells}'
                 f'<td class="sum">{rowsum}</td></tr>')
    foot = ('<tr class="tot"><td class="mo">합계</td>'
            + ''.join(f'<td>{coltot[m]}</td>' for m in months)
            + f'<td class="sum">{grand}</td></tr>')
    return (f'<table class="lvmx"><thead>{head}</thead>'
            f'<tbody>{rows}</tbody><tfoot>{foot}</tfoot></table>')


def render_all(DATA):
    """배포용 통합본 — 시스템 요약 + 스케줄표 + 과목별 준비물 을 한 문서로."""
    lvmx = _level_matrix(DATA)
    tmmx = _teacher_month_matrix(DATA)
    mtmx = _month_total_matrix(DATA)
    def _mens_item(lab):
        rest = lab.replace('맨즈 STAGE', '').strip()      # "00 CS·마인드"
        num, _, name = rest.partition(' ')                # "00", "CS·마인드"
        return f'<span class="ms"><b>{_esc(num)}</b>{_esc(name)}</span>'
    mens_list = ''.join(_mens_item(lab) for lab, _ls in spec.TRACKS['와이'])
    mens_color = spec.COL['와이']
    roles = ''.join(
        f'<tr><td class="rt" style="color:{spec.COL[t]}">{t}</td><td>{_esc(role)}</td>'
        f'<td class="rl">{_esc(lv)}</td></tr>' for t, role, lv in ROLES)
    prep_total = sum(len(r) for _, _, _, r in TEACHERS) + len(MENS[3])
    prep_nav = ''.join(f'<span class="chip" style="--c:{c}">{_esc(n)}</span>'
                       for n, _, c, _ in list(TEACHERS) + [MENS])
    prep_body = ''.join(_prep_block(*t) for t in TEACHERS) + _prep_block(*MENS)
    return f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>앳나운 2026 하반기 교육 — 전체 안내 (배포용)</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
:root{{--cream:#F7F5F1;--ink:#1c1a17;--gold:#A8895E;--gray:#6a655c;--line:#E4DFD6;}}
body{{background:#efece6;color:var(--ink);font-family:-apple-system,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;line-height:1.5;padding:24px 14px 70px;}}
.wrap{{max-width:1000px;margin:0 auto;}}
.cover{{background:var(--ink);color:var(--cream);border-radius:16px;padding:34px 30px;margin-bottom:16px;}}
.cover .t{{font-size:12px;letter-spacing:.24em;color:var(--gold);font-weight:800;}}
.cover h1{{font-size:29px;font-weight:900;margin:9px 0 8px;line-height:1.2;}}
.cover p{{font-size:14px;color:#d7d1c6;}}
.toc{{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 26px;}}
.toc a{{background:#fff;border:1px solid var(--line);border-radius:22px;padding:7px 15px;font-size:13.5px;font-weight:800;color:var(--ink);text-decoration:none;}}
.sec{{margin:30px 0;}}
.sh{{font-size:13px;letter-spacing:.14em;color:var(--gold);font-weight:800;margin-bottom:4px;}}
.st{{font-size:22px;font-weight:900;margin-bottom:14px;border-bottom:2px solid var(--ink);padding-bottom:8px;}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:12px;}}
.card{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px 18px;}}
.card h3{{font-size:14px;font-weight:900;margin-bottom:9px;color:var(--gold);}}
.card ul{{list-style:none;font-size:13.5px;}} .card li{{padding:3px 0 3px 14px;position:relative;}}
.card li:before{{content:"·";position:absolute;left:2px;color:var(--gold);font-weight:900;}}
table.roles{{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);border-radius:12px;overflow:hidden;}}
table.roles td{{padding:10px 14px;border-top:1px solid var(--line);font-size:13.5px;}}
table.roles tr:first-child td{{border-top:0;}}
.roles .rt{{font-weight:900;width:78px;}} .roles .rl{{text-align:right;color:var(--gray);font-weight:800;width:90px;}}
table.lvmx{{border-collapse:collapse;background:#fff;border:1px solid var(--line);border-radius:10px;overflow:hidden;width:100%;max-width:520px;}}
.lvmx th,.lvmx td{{padding:9px 10px;text-align:center;font-size:13.5px;border:1px solid var(--line);}}
.lvmx thead th{{background:var(--ink);color:var(--cream);font-weight:800;border-color:#333;}}
.lvmx .mo{{font-weight:900;background:var(--cream);}}
.lvmx .sum{{font-weight:900;background:#f3efe7;}}
.lvmx td.z{{color:#c25b5b;font-weight:800;}}
.lvmx tfoot .tot td{{font-weight:900;background:#efeae1;border-top:2px solid var(--ink);}}
.mens{{display:flex;flex-wrap:wrap;gap:8px;}}
.mens .ms{{background:#fff;border:1px solid var(--line);border-left:4px solid {mens_color};border-radius:8px;padding:7px 12px;font-size:13px;font-weight:700;}}
.mens .ms b{{display:inline-block;min-width:22px;color:{mens_color};font-weight:900;margin-right:5px;}}
.legend{{background:var(--cream);border:1px solid var(--line);border-radius:10px;padding:13px 16px;margin-bottom:14px;display:flex;flex-wrap:wrap;gap:9px 15px;}}
.lg{{display:inline-flex;align-items:center;gap:7px;font-size:12px;font-weight:700;}}
.lg i{{width:14px;height:14px;border-radius:4px;display:inline-block;}}
.note{{font-size:12.5px;color:#555;background:var(--cream);border:1px solid var(--line);border-radius:10px;padding:12px 16px;line-height:1.7;margin-bottom:16px;}}
.warn{{background:#fff7e8;border:1px solid #e8d9b0;border-radius:11px;padding:12px 15px;font-size:12.5px;color:#7a6a3c;font-weight:600;margin-bottom:16px;}}
.mcal{{background:var(--cream);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin-bottom:12px;}}
.mtitle{{font-size:18px;font-weight:800;margin-bottom:10px;}}
.mc{{width:100%;border-collapse:collapse;table-layout:fixed;}}
.mc th{{font-size:11px;font-weight:800;color:var(--gray);padding:6px 0;border-bottom:2px solid var(--ink);}}
.mc th.sun{{color:#c25b5b;}} .mc th.sat{{color:#5b7ac2;}}
.mc td{{border:1px solid var(--line);vertical-align:top;height:74px;padding:5px 6px;background:#fff;}}
.mc td.pad{{background:transparent;border:none;}} .mc td.off{{background:#f0ede7;}}
.dn{{font-size:11px;font-weight:800;color:#9b958c;margin-bottom:3px;}}
.ev{{display:block;font-size:9.5px;font-weight:800;border-radius:3px;padding:2px 5px;margin-top:3px;line-height:1.25;}}
.ev .lvb{{background:rgba(255,255,255,.28);border-radius:3px;padding:0 3px;margin-right:3px;font-size:8.5px;}}
.chip{{background:#fff;border:1.5px solid var(--c);color:var(--c);border-radius:20px;padding:5px 13px;font-size:13px;font-weight:800;}}
.nav{{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:18px;}}
.tsec{{margin-bottom:20px;}}
.thead{{background:#fff;border:1px solid var(--line);border-radius:12px 12px 0 0;padding:14px 18px;}}
.tname{{font-size:18px;font-weight:900;display:flex;align-items:center;gap:10px;}}
.tname .cnt{{font-size:11.5px;font-weight:800;color:#fff;background:var(--gray);border-radius:11px;padding:2px 9px;}}
.tsub{{font-size:12.5px;color:var(--gray);font-weight:600;margin-top:3px;}}
.rows{{background:#fff;border:1px solid var(--line);border-top:0;border-radius:0 0 12px 12px;overflow:hidden;}}
.row{{display:flex;gap:12px;padding:13px 16px;border-top:1px solid var(--line);}}
.row:first-child{{border-top:0;}}
.rnum{{flex-shrink:0;width:30px;height:30px;border-radius:8px;color:#fff;font-weight:900;font-size:13px;display:flex;align-items:center;justify-content:center;}}
.rbody{{flex:1;min-width:0;}}
.rtitle{{font-size:15px;font-weight:900;margin-bottom:7px;}}
.rgrid{{display:flex;flex-direction:column;gap:5px;}}
.cell{{display:flex;gap:8px;align-items:flex-start;}}
.lab{{flex-shrink:0;font-size:11px;font-weight:800;border-radius:6px;padding:2px 8px;color:#fff;min-width:46px;text-align:center;}}
.lab-p{{background:#3F6F5F;}} .lab-h{{background:#B5793A;}} .lab-w{{background:#B5563F;}}
.txt{{font-size:13px;color:#3a362f;}}
.foot{{text-align:center;font-size:11px;letter-spacing:.28em;color:#b7b1a6;font-weight:700;margin:26px 0 4px;}}
@media(max-width:720px){{.grid2{{grid-template-columns:1fr;}}.mc td{{height:auto;}}.ev{{font-size:9px;}}}}
</style></head>
<body><div class="wrap">
<div class="cover"><div class="t">AT NOWN · 2026 EDUCATION</div>
<h1>2026 하반기 교육 — 전체 안내</h1>
<p>교육 시스템 · 일정 스케줄표 · 과목별 준비물 (한 문서 배포용)</p></div>
<div class="toc"><a href="#sys">① 교육 시스템</a><a href="#prep">② 과목별 준비물</a></div>
<div class="note" style="margin-bottom:0">📅 <b>일정 스케줄표(8~12월 캘린더)는 가시성을 위해 별도 문서</b>로 제공합니다 — 「교육일정_캘린더_2026」 파일 참고.</div>

<div class="sec" id="sys"><div class="sh">SYSTEM</div><div class="st">① 교육 시스템</div>
<div class="grid2">
<div class="card"><h3>기간 · 시간</h3><ul>
<li>정규교육 <b>8/10 ~ 12/6</b> · 입봉시험 <b>12/21(월)</b></li>
<li>기본 <b>아침 교육 {spec.MORNING}</b></li>
<li>모델 작업은 <b>{spec.EVENING}</b></li>
<li>휴무 <b>월 · 토</b> (전원)</li>
</ul></div>
<div class="card"><h3>이벤트</h3><ul>
<li>특강 = 매월 <b>3째주 금</b></li>
<li>모델데이 = 매월 <b>2·4째주 금</b></li>
<li>입봉시험 = <b>12/21(월)</b></li>
</ul></div>
</div>
<div style="height:12px"></div>
<table class="roles"><tr><td class="rt">선생님</td><td>담당</td><td class="rl">레벨</td></tr>{roles}</table>
<div class="note" style="margin-top:14px">· 레벨은 과목마다 <b>L1~L5</b>로 표기 · 맨즈(옴므)는 별도 트랙(공간이 달라 병행).</div>
<div style="height:16px"></div>
<h3 style="font-size:15px;font-weight:900;margin-bottom:8px">맨즈(옴므) STAGE 과목 — 와이 원장</h3>
<div class="mens">{mens_list}</div>
<div class="note" style="margin-top:10px">· 앳나운 옴므 별도 줄기 · <b>STAGE 00 → 07</b> 순서 진행 · 수·목·금 진행 · 공간이 달라 시즈 교육과 병행.</div>
<div style="height:16px"></div>
<h3 style="font-size:15px;font-weight:900;margin-bottom:8px">월별 총 수업 개수</h3>
{mtmx}
<div style="height:16px"></div>
<h3 style="font-size:15px;font-weight:900;margin-bottom:8px">월 × 레벨 교육 개수</h3>
{lvmx}
<div class="note" style="margin-top:10px">· 표의 숫자 = 그 달에 열리는 <b>해당 레벨 과목 수</b> (맨즈 별도 · 특강·모델데이·시험 제외).<br>· 12월은 12/6에 정규가 끝나 첫 주(약 1주)만 있어 개수가 적습니다.</div>
<div style="height:16px"></div>
<h3 style="font-size:15px;font-weight:900;margin-bottom:8px">선생님별 · 월 수업 개수</h3>
{tmmx}
<div class="note" style="margin-top:10px">· 한 선생님이 특정 달에 몰리지 않게 <b>8~11월은 고르게</b> 폈습니다. 12월은 수업일(약 1주)이 적어 자연히 적습니다.</div>
</div>

<div class="sec" id="prep"><div class="sh">MATERIALS</div><div class="st">② 과목별 준비물 · 과제 · 주의 <span style="font-size:13px;color:var(--gray);font-weight:700">(총 {prep_total}과목)</span></div>
<div class="warn">⚠️ 준비물·과제·주의 내용은 현장 표준 기준 <b>초안</b>입니다 — 각 선생님이 실제 수업 기준으로 검수·확정 후 최종 배포.</div>
<div class="nav">{prep_nav}</div>
{prep_body}
</div>

<div class="foot">A T &nbsp; N O W N &nbsp;·&nbsp; 2 0 2 6 &nbsp; 하 반 기 &nbsp; 교 육</div>
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
