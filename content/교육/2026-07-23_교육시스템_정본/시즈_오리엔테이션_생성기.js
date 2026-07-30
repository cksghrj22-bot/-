const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE";           // 13.33 x 7.5"
const W = 13.33, H = 7.5;

// ── ATNOWN 팔레트 ──
const CREAM = "F7F5F1", INK = "1A1815", GOLD = "A8895E", GRAY = "8F887C", LINE = "E4DFD6";
const CARDBG = "FFFFFF";
const SERIF = "Cambria";            // 프리미엄 세리프(오피스 기본 탑재)
const SANS = "Calibri";

const TCOL = { "창엽":"3B7A57","이호":"2E6E8E","차노":"A8895E","신후":"C0673A","성희":"B0567F","보미":"6D5BA6" };

// 공통: 좌상단 브랜드 마크 + 우측 세로 라벨
function brand(s, label, dark) {
  const fg = dark ? CREAM : INK, mut = dark ? "C9C3B7" : GRAY;
  s.addText("AN", { x:0.55, y:0.42, w:0.5, h:0.42, fontFace:SERIF, bold:true, fontSize:15,
    color:fg, align:"center", valign:"middle", line:{color:fg,width:1}, });
  s.addText("ATNOWN ACADEMY", { x:1.12, y:0.42, w:4, h:0.42, fontFace:SANS, bold:true,
    fontSize:10, color:mut, charSpacing:3, valign:"middle" });
  if (label) s.addText(label, { x:W-2.4, y:0.44, w:1.9, h:0.34, fontFace:SANS, bold:true,
    fontSize:10, color:mut, charSpacing:3, align:"right", valign:"middle" });
}
function kicker(s, t) {
  s.addText(t, { x:0.6, y:1.35, w:10, h:0.3, fontFace:SANS, bold:true, fontSize:11.5,
    color:GOLD, charSpacing:3 });
}
function title(s, t, y) {
  s.addText(t, { x:0.58, y:y||1.7, w:11.5, h:0.9, fontFace:SERIF, fontSize:40, color:INK, bold:false });
}
function goldDot(s, x, y) { s.addShape(p.ShapeType.rect, {x,y,w:0.72,h:0.02,fill:{color:GOLD}}); }

// ══════════ 1. COVER (dark) ══════════
let s = p.addSlide(); s.background = { color: INK };
brand(s, "ORIENTATION", true);
s.addText("2026", { x:0.7, y:2.0, w:11, h:1.1, fontFace:SERIF, fontSize:66, color:CREAM, bold:false });
s.addText([
  { text:"EDUCATION", options:{ color:GOLD } },
  { text:" SYSTEM", options:{ color:CREAM } },
], { x:0.66, y:3.0, w:12, h:1.1, fontFace:SERIF, fontSize:66, bold:false });
s.addText("시즈 오리엔테이션 — 우리가 어떻게 디자이너가 되는가", { x:0.72, y:4.25, w:11, h:0.5,
  fontFace:SANS, fontSize:18, color:"E6E1D7" });
s.addText("FOUNDATION → FIGHTER → SNS → DESIGNER", { x:0.72, y:4.8, w:11, h:0.35,
  fontFace:SANS, bold:true, fontSize:11, color:GOLD, charSpacing:3 });
s.addText("AT NOWN · 2026 하반기 · 8월 2째주 → 12월", { x:0.72, y:6.5, w:11, h:0.35,
  fontFace:SANS, fontSize:11, color:GRAY, charSpacing:2 });
s.addNotes("환영 인사. 오늘 발표: 교육 큰 그림 → 코스 → 커리큘럼 → 일정 → 준비물 → 디자이너 조건 → SNS → Q&A. 편하게 질문받겠다고 안내.");

// ══════════ 1B. 개념 도식 — 이상향과 디딤돌 (내레이션용 · beat마다 슬라이드) ══════════
// beat ① 질문 (dark)
s = p.addSlide(); s.background = { color: INK };
brand(s, "THINK", true);
s.addText("당신은", { x:1, y:2.1, w:11.3, h:0.7, fontFace:SANS, fontSize:24, color:"C9C3B7", align:"center" });
s.addText("어떤 디자이너가\n되고 싶어요?", { x:1, y:2.8, w:11.33, h:2.4, fontFace:SERIF, fontSize:60, color:GOLD, align:"center", lineSpacingMultiple:1.08 });
s.addNotes("질문 던지기. 각자 머릿속에 '되고 싶은 디자이너(이상향)'를 그려보게 한다. 답은 뒤 워드월/대화로.");

// beat ② 현재 → (강) → 이상향
s = p.addSlide(); s.background = { color: CREAM };
brand(s, "NOW vs DREAM");
kicker(s, "지금의 나 · 그리고 되고 싶은 나");
(function(){
  const ny=3.5, r=2.0;
  s.addShape(p.ShapeType.ellipse, { x:0.9, y:ny, w:r, h:r, fill:{color:CARDBG}, line:{color:INK,width:2} });
  s.addText("지금의 나\n(초급)", { x:0.9, y:ny, w:r, h:r, fontFace:SANS, bold:true, fontSize:16, color:INK, align:"center", valign:"middle" });
  s.addShape(p.ShapeType.ellipse, { x:W-0.9-r, y:ny, w:r, h:r, fill:{color:GOLD} });
  s.addText("되고 싶은\n디자이너\n(이상향)", { x:W-0.9-r, y:ny, w:r, h:r, fontFace:SERIF, bold:true, fontSize:18, color:"FFFFFF", align:"center", valign:"middle" });
  // 사이의 '강'
  s.addShape(p.ShapeType.rect, { x:0.9+r+0.2, y:ny+0.35, w:(W-0.9-r)-(0.9+r+0.2)-0.2, h:r-0.7, fill:{color:"E9E3D8"} });
  s.addText("고객이 나를 찾아오게 만들어야\n건널 수 있는 강", { x:0.9+r+0.2, y:ny+0.35, w:(W-0.9-r)-(0.9+r+0.2)-0.2, h:r-0.7, fontFace:SANS, bold:true, fontSize:16, color:"8a7f66", align:"center", valign:"middle" });
})();
s.addText("이상향과 지금 사이엔 '강'이 있다 — 손님이 나를 찾아오게 만드는 것.", { x:0.6, y:6.2, w:12, h:0.4, fontFace:SANS, fontSize:13.5, color:"555555", align:"center" });
s.addNotes("현재와 이상향 사이의 간극 = '고객이 나를 찾아오게 만드는 것'. 이 강을 어떻게 건널까?");

// beat ③ 디딤돌 (한 번에 못 건넌다)
s = p.addSlide(); s.background = { color: CREAM };
brand(s, "STEPPING STONES");
kicker(s, "한 번에 못 건넌다 · 디딤돌을 하나씩");
(function(){
  const ny=3.5, r=2.0, cy=ny+r/2;
  s.addShape(p.ShapeType.ellipse, { x:0.6, y:ny, w:r, h:r, fill:{color:CARDBG}, line:{color:INK,width:2} });
  s.addText("지금의 나", { x:0.6, y:ny, w:r, h:r, fontFace:SANS, bold:true, fontSize:15, color:INK, align:"center", valign:"middle" });
  s.addShape(p.ShapeType.ellipse, { x:W-0.6-r, y:ny, w:r, h:r, fill:{color:GOLD} });
  s.addText("이상향", { x:W-0.6-r, y:ny, w:r, h:r, fontFace:SERIF, bold:true, fontSize:20, color:"FFFFFF", align:"center", valign:"middle" });
  const stones=["초디","역경","과정","성장","도약"];
  const x0=0.6+r+0.35, x1=W-0.6-r-0.35, sw=0.95;
  stones.forEach((t,i)=>{
    const x = x0 + (x1-x0-sw) * (i/(stones.length-1));
    const dip = (i%2? 0.5 : -0.2);
    s.addShape(p.ShapeType.ellipse, { x, y:cy-sw/2+dip, w:sw, h:sw, fill:{color:"D8C9A8"}, line:{color:GOLD,width:1.5} });
    s.addText(t, { x, y:cy-sw/2+dip, w:sw, h:sw, fontFace:SANS, bold:true, fontSize:12, color:"5a4c2e", align:"center", valign:"middle" });
  });
})();
s.addText("이상향은 한 걸음에 못 간다 — 초디부터 디딤돌(역경·과정)을 하나씩 밟아 건넌다.", { x:0.6, y:6.2, w:12, h:0.4, fontFace:SANS, fontSize:13.5, color:"555555", align:"center" });
s.addNotes("이상향은 한 번에 도달 불가. 초디부터 디딤돌(역경)을 하나씩 밟는 '과정'이 곧 성장. 이게 플레이어의 길.");

// beat ④ 두 갈래 (반성)
s = p.addSlide(); s.background = { color: CREAM };
brand(s, "TWO PATHS");
kicker(s, "두 갈래 길");
title(s, "디딤돌이냐, 타협이냐", 1.6);
(function(){
  // 윗길 ✓
  s.addShape(p.ShapeType.roundRect, { x:0.6, y:2.7, w:12.13, h:1.55, rectRadius:0.12, fill:{color:"F3EEE3"}, line:{color:GOLD,width:1.5} });
  s.addText("○", { x:0.85, y:2.7, w:0.6, h:1.55, fontFace:SERIF, bold:true, fontSize:26, color:GOLD, align:"center", valign:"middle" });
  s.addText([{text:"디딤돌을 하나씩 밟는다  ",options:{bold:true,color:INK}},{text:"→ 역경·과정을 지난다 → ",options:{color:"555555"}},{text:"이상향에 닿는다",options:{bold:true,color:GOLD}}],
    { x:1.5, y:2.9, w:11, h:0.5, fontFace:SANS, fontSize:16, valign:"middle" });
  s.addText("느려 보여도, 결국 원하는 디자이너가 되는 유일한 길", { x:1.5, y:3.5, w:11, h:0.5, fontFace:SANS, fontSize:13, color:"6a655c", valign:"middle" });
  // 아랫길 ✗
  s.addShape(p.ShapeType.roundRect, { x:0.6, y:4.5, w:12.13, h:1.75, rectRadius:0.12, fill:{color:"EFEEEC"}, line:{color:"C9C3B7",width:1.25} });
  s.addText("✕", { x:0.85, y:4.5, w:0.6, h:1.75, fontFace:SANS, bold:true, fontSize:24, color:"9a948a", align:"center", valign:"middle" });
  s.addText([{text:"이상향만 높이 잡는다  ",options:{bold:true,color:"555555"}},{text:"→ 디딤돌을 건너뛴다 → 안 된다 → ",options:{color:"8a847a"}},{text:"타협",options:{bold:true,color:"8a5a5a"}}],
    { x:1.5, y:4.7, w:11, h:0.5, fontFace:SANS, fontSize:16, valign:"middle" });
  s.addText("→ '미용은 그냥 생계수단' → 평범하게 먹고사는 데서 멈춘다", { x:1.5, y:5.35, w:11, h:0.5, fontFace:SANS, fontSize:14, bold:true, color:"8a5a5a", valign:"middle" });
  s.addText("요즘 디딤돌을 생각하는 사람이 드물다 — 우리가 돌아봐야 할 지점", { x:1.5, y:5.8, w:11, h:0.4, fontFace:SANS, fontSize:12.5, color:"6a655c", valign:"middle" });
})();
s.addNotes("두 갈래. 윗길: 디딤돌→과정→도달. 아랫길: 이상향만 높이→건너뜀→좌절→타협→'미용=생계수단' 평범. 요즘 디딤돌을 잊고 이상향만 높다가 타협하는 걸 우리가 돌아보자는 취지. (여기서 대표님이 직접 풀어 설명)");

// beat ⑤ 마무리 문구 (dark)
s = p.addSlide(); s.background = { color: INK };
goldDot(s, W/2-0.36, 2.7);
s.addText("이상향보다,\n오늘의 디딤돌.", { x:1, y:3.0, w:11.33, h:2.0, fontFace:SERIF, fontSize:52, color:CREAM, align:"center", lineSpacingMultiple:1.1 });
s.addText("— 초디의 한 걸음이 곧 그 길이다", { x:1, y:5.1, w:11.33, h:0.5, fontFace:SANS, fontSize:16, color:GOLD, align:"center" });
s.addNotes("마무리 한 줄. 이상향은 방향, 디딤돌은 오늘 할 일. 여기서 시스템 설명으로 자연스럽게 넘어간다.");

// ══════════ 2. THE JOURNEY ══════════
s = p.addSlide(); s.background = { color: CREAM };
brand(s, "THE JOURNEY");
kicker(s, "큰 그림 · 이 순서대로 큰다");
title(s, "Level 1 → 5");
s.addText("손이랑 마음부터 → 혼자 서는 디자이너까지", { x:0.6, y:2.55, w:11, h:0.35,
  fontFace:SANS, italic:true, fontSize:14, color:"666666" });
const journey = [
  ["01","LV 1·2","완전 기초","가위 잡는 것부터. \"왜 이 일을 하는지\" 먼저 심고 기본기를 몸에 붙인다."],
  ["02","LV 3","실전 전투원","진짜 손님 앞에. 배운 걸로 현장에서 부딪히며 실력을 굳힌다."],
  ["03","LV 4","SNS 소통","실력 + 나를 보여주는 힘. SNS로 손님이 나를 찾아오게 만든다."],
  ["04","LV 5","디자이너","손님을 오게 하고 끝까지 케어. 여기까지 오면 승급!"],
];
const jw = 2.85, jgap = 0.24, jx0 = 0.6, jy = 3.3;
journey.forEach((j,i)=>{
  const x = jx0 + i*(jw+jgap);
  s.addShape(p.ShapeType.rect, { x, y:jy, w:jw, h:3.1, fill:{color:CARDBG}, line:{color:LINE,width:1} });
  s.addShape(p.ShapeType.ellipse, { x:x+0.28, y:jy+0.3, w:0.7, h:0.7, fill:{color:INK} });
  s.addText(j[0], { x:x+0.28, y:jy+0.3, w:0.7, h:0.7, fontFace:SERIF, bold:true, fontSize:19,
    color:GOLD, align:"center", valign:"middle" });
  s.addText(j[1], { x:x+0.28, y:jy+1.15, w:jw-0.5, h:0.3, fontFace:SANS, bold:true, fontSize:12, color:GOLD, charSpacing:1 });
  s.addText(j[2], { x:x+0.28, y:jy+1.45, w:jw-0.5, h:0.4, fontFace:SERIF, bold:true, fontSize:20, color:INK });
  s.addText(j[3], { x:x+0.28, y:jy+1.95, w:jw-0.52, h:1.0, fontFace:SANS, fontSize:12, color:"555555", lineSpacingMultiple:1.15 });
});
s.addNotes("1·2레벨은 기초와 마인드. 3레벨부터 현장 실전. 4레벨은 SNS로 나를 알리는 능력. 5레벨이 디자이너 승급.");

// ══════════ 3. COURSES ══════════
s = p.addSlide(); s.background = { color: CREAM };
brand(s, "COURSES");
kicker(s, "어느 코스로 가느냐 · 기간만 다르다");
title(s, "옴므 · 한남 · 청담");
const courses = [
  ["옴므","2년","남자 전문 (맨즈)","와이 원장 STAGE 0~7"],
  ["한남","2년 6개월","업스타일 빼고 다","디자이너 후 마지막 레벨 이수"],
  ["청담","3년","업스타일까지 전부","풀 커리큘럼"],
];
const cw=3.7, cgap=0.35, cx0=0.75, cy=3.15;
courses.forEach((c,i)=>{
  const x = cx0 + i*(cw+cgap);
  s.addShape(p.ShapeType.rect, { x, y:cy, w:cw, h:2.9, fill:{color:CARDBG}, line:{color:LINE,width:1} });
  s.addText(c[0], { x, y:cy+0.4, w:cw, h:0.6, fontFace:SERIF, bold:true, fontSize:30, color:INK, align:"center" });
  s.addText(c[1], { x, y:cy+1.15, w:cw, h:0.45, fontFace:SANS, bold:true, fontSize:19, color:GOLD, align:"center" });
  s.addText(c[2], { x:x+0.3, y:cy+1.8, w:cw-0.6, h:0.35, fontFace:SANS, bold:true, fontSize:14, color:INK, align:"center" });
  s.addText(c[3], { x:x+0.3, y:cy+2.15, w:cw-0.6, h:0.5, fontFace:SANS, fontSize:12.5, color:"666666", align:"center", lineSpacingMultiple:1.15 });
});
s.addText("※ 한남은 청담보다 6개월 짧다 — 디자이너가 된 뒤 마지막 레벨 수업을 업스타일만 빼고 이수",
  { x:0.75, y:6.35, w:11.8, h:0.35, fontFace:SANS, fontSize:12, color:GRAY });
s.addNotes("코스는 커리큘럼이 다른 게 아니라 기간·범위가 다르다. 업스타일 포함 여부가 한남/청담 차이.");

// ══════════ 4. CURRICULUM ══════════
s = p.addSlide(); s.background = { color: CREAM };
brand(s, "CURRICULUM");
kicker(s, "누가 무엇을 가르치나 · 정규 70과목");
title(s, "6 Teachers · 5 Lines");
const rows = [
  ["커트","기초(L1·2) → 디자인·시그니처(L3~5)","창엽 · 이호"],
  ["열펌 · 룩북","남성 열펌·설계 → 여성 디자인 → 룩북","신후"],
  ["콜드펌","이론 → 와인딩 → 기법 → 디자인 → 트렌드","성희"],
  ["업스타일","드라이·브레이드 → 업스타일 → 방송헤어","보미"],
  ["디자인 방법","열펌 기초 → 질감 → 형용사 → 이미지·구조","차노"],
];
let ry = 2.95; const rh = 0.72;
rows.forEach((r,i)=>{
  const y = ry + i*rh;
  s.addText(r[0], { x:0.6, y, w:2.3, h:rh, fontFace:SERIF, bold:true, fontSize:17, color:INK, valign:"middle" });
  s.addText(r[1], { x:3.0, y, w:7.0, h:rh, fontFace:SANS, fontSize:13.5, color:"444444", valign:"middle" });
  s.addText(r[2], { x:10.1, y, w:2.6, h:rh, fontFace:SANS, bold:true, fontSize:12.5, color:GOLD, align:"right", valign:"middle" });
  s.addShape(p.ShapeType.line, { x:0.6, y:y+rh-0.02, w:12.1, h:0, line:{color:LINE,width:1} });
});
s.addText("맨즈(옴므)는 와이 원장 STAGE 0~7 별도 줄기 · 특강(연교·재아·승현) 매월 3째주 금",
  { x:0.6, y:6.75, w:12, h:0.35, fontFace:SANS, fontSize:11.5, color:GRAY });
s.addNotes("정규 5개 라인, 선생님 6명. 각자 자기 라인을 레벨 순서로 진행. 총 70과목.");

// ══════════ 5. SCHEDULE ══════════
s = p.addSlide(); s.background = { color: CREAM };
brand(s, "SCHEDULE");
kicker(s, "2026 하반기 · 언제 어떻게");
title(s, "8/10 → 12/6");
const sched = [
  ["정규교육 8월 2째주 ~ 12월 첫주","화·수·목·금·일에 배분 (월·토 휴무), 아침 07:30~09:30"],
  ["레벨이 다르면 같은 날 병행","내 레벨(캘린더 L태그) 과목만 들으면 됨"],
  ["모델데이 — 매월 2·4째주 금","모델 2명 이상일 때 시행 · 저녁 작업"],
  ["특강 — 매월 3째주 금","와이 · 연교 · 신후 · 재아 · 승현"],
  ["입봉시험 — 12/21 (월)","교육 종료 후 2주 여유"],
];
let sy = 2.95;
sched.forEach((r,i)=>{
  const y = sy + i*0.82;
  s.addShape(p.ShapeType.ellipse, { x:0.62, y:y+0.05, w:0.5, h:0.5, fill:{color:INK} });
  s.addText(String(i+1), { x:0.62, y:y+0.05, w:0.5, h:0.5, fontFace:SERIF, bold:true, fontSize:16, color:GOLD, align:"center", valign:"middle" });
  s.addText(r[0], { x:1.35, y:y-0.05, w:11, h:0.4, fontFace:SANS, bold:true, fontSize:15.5, color:INK });
  s.addText(r[1], { x:1.35, y:y+0.33, w:11, h:0.35, fontFace:SANS, fontSize:12.5, color:"666666" });
});
s.addNotes("교육은 8월 둘째 주부터 12월 첫 주까지. 요일은 골고루 흩어 배분. 시험은 12월 21일.");

// ══════════ 6. PREPARE (따뜻한 카드 그리드) ══════════
s = p.addSlide(); s.background = { color: CREAM };
brand(s, "HOW TO PREPARE");
kicker(s, "시즈가 지킬 것 · 준비물 · 과제");
title(s, "Come Ready");
const prep = [
  ["준비물은 전날까지","도구·마네킹·약제를 미리 챙겨 온다"],
  ["과제는 다음 수업 전","촬영본·리포트로 제출"],
  ["가발·모델모는 신중히","준비부터가 시험 시작"],
  ["모르면 바로 물어보기","과목별 상세는 배포 문서에"],
];
const CW=5.95, CH=1.5, CGX=0.25, CGY=0.22, CX0=0.6, CY0=2.9;
const WARM="FBF8F3";
prep.forEach((r,i)=>{
  const col=i%2, row=Math.floor(i/2);
  const x=CX0+col*(CW+CGX), y=CY0+row*(CH+CGY);
  s.addShape(p.ShapeType.roundRect, { x, y, w:CW, h:CH, rectRadius:0.12, fill:{color:WARM},
    line:{color:LINE,width:0.75}, shadow:{type:"outer", color:"C9BFA8", blur:7, offset:2, angle:90, opacity:0.28} });
  s.addShape(p.ShapeType.ellipse, { x:x+0.4, y:y+0.42, w:0.18, h:0.18, fill:{color:GOLD} });
  s.addText(r[0], { x:x+0.72, y:y+0.3, w:CW-1.0, h:0.45, fontFace:SERIF, bold:true, fontSize:21, color:INK, valign:"middle" });
  s.addText(r[1], { x:x+0.4, y:y+0.88, w:CW-0.8, h:0.4, fontFace:SANS, fontSize:13, color:"6A655C", valign:"middle" });
});
// 하단 배너 = 따뜻한 문구(딱딱함 해소)
{
  const y=CY0+2*(CH+CGY);
  s.addShape(p.ShapeType.roundRect, { x:CX0, y, w:CW*2+CGX, h:0.9, rectRadius:0.1, fill:{color:INK},
    shadow:{type:"outer", color:"C9BFA8", blur:7, offset:2, angle:90, opacity:0.3} });
  s.addText([
    { text:"준비된 손이  ", options:{ color:CREAM } },
    { text:"디자인이 된다", options:{ color:GOLD } },
  ], { x:CX0, y, w:CW*2+CGX, h:0.9, fontFace:SERIF, bold:true, fontSize:24, align:"center", valign:"middle" });
}
s.addNotes("준비물은 전날, 과제는 다음 수업 전. 가발·모델모는 되돌릴 수 없으니 신중히 — 준비부터가 이미 시험의 시작. 모르면 바로 선생님께.");

// ══════════ 7. 헤어디자이너 쇼 기준 ══════════
s = p.addSlide(); s.background = { color: CREAM };
brand(s, "SIGNATURE SHOW");
kicker(s, "헤어디자이너 쇼 기준 · 승급");
title(s, "헤어디자이너 쇼 기준");
// 시그니처 쇼 설명 카드 (컴팩트)
s.addShape(p.ShapeType.roundRect, { x:0.6, y:2.5, w:12.13, h:0.95, rectRadius:0.1, fill:{color:INK},
  shadow:{type:"outer", color:"C9BFA8", blur:7, offset:2, angle:90, opacity:0.3} });
s.addText([
  { text:"시그니처 쇼", options:{ color:GOLD, bold:true } },
  { text:"   인스타 헤어쇼 · 디렉터 입회 · 기획력·PPT력·노출력으로 증명", options:{ color:"D7D1C6" } },
], { x:1.0, y:2.5, w:11.4, h:0.95, fontFace:SERIF, fontSize:18, valign:"middle" });
// 통과 기준
s.addText([
  { text:"쇼 기준 성립 — ", options:{color:"555555"} },
  { text:"4레벨", options:{bold:true} }, { text:" 정량기준 ", options:{} },
  { text:"50%", options:{bold:true, color:GOLD} },
  { text:"   ·   ", options:{color:GRAY} },
  { text:"5레벨", options:{bold:true} }, { text:" ", options:{} },
  { text:"80% 통과 시", options:{bold:true, color:GOLD} },
], { x:0.62, y:3.62, w:12, h:0.35, fontFace:SANS, fontSize:14, color:INK });
// 기존 정량 기준 chips (아웃라인)
s.addText("기존 정량 기준", { x:0.62, y:4.05, w:12, h:0.28, fontFace:SANS, bold:true, fontSize:11.5, color:GRAY, charSpacing:2 });
const crit = ["포트폴리오 30","인스타 3개월","매출 300~400만","리뷰 월 10","모델 50명"];
const kw=2.36, kgap=0.075, kx0=0.62;
crit.forEach((k,i)=>{
  const x = kx0 + i*(kw+kgap);
  s.addShape(p.ShapeType.roundRect, { x, y:4.35, w:kw, h:0.62, rectRadius:0.12, fill:{color:CARDBG}, line:{color:GOLD,width:1.25} });
  s.addText(k, { x:x+0.05, y:4.35, w:kw-0.1, h:0.62, fontFace:SANS, bold:true, fontSize:12.5, color:INK, align:"center", valign:"middle" });
});
// ★ 무조건 디자이너 KPI — 최종 조건 (골드 채움)
s.addText([
  { text:"★ 무조건 디자이너 되는 KPI", options:{bold:true, color:INK} },
  { text:"  — 최종 조건 달성 시 쇼·정량 기준과 무관하게 승급", options:{color:"6A655C"} },
], { x:0.62, y:5.2, w:12, h:0.3, fontFace:SANS, fontSize:11.5, charSpacing:1 });
const kpi = ["모델 100명","매출 500","시그니처 60","리뷰 70","조회수 10만"];
kpi.forEach((k,i)=>{
  const x = kx0 + i*(kw+kgap);
  s.addShape(p.ShapeType.roundRect, { x, y:5.55, w:kw, h:0.62, rectRadius:0.12, fill:{color:GOLD} });
  s.addText(k, { x:x+0.05, y:5.55, w:kw-0.1, h:0.62, fontFace:SANS, bold:true, fontSize:13, color:"FFFFFF", align:"center", valign:"middle" });
});
s.addText("SNS — 1·2레벨 주 1개 / 3·4레벨 주 2개 (나의 생각·연습)로 나를 알리는 힘까지",
  { x:0.62, y:6.5, w:12, h:0.35, fontFace:SANS, fontSize:12, color:"6A655C" });
s.addNotes("승급은 시그니처 쇼(인스타 헤어쇼)로 증명 — 4레벨 정량기준 50%, 5레벨 80% 통과 시. 정량기준: 포트폴리오30·인스타3개월·매출300~400만·리뷰월10·모델50명. 그리고 최종 KPI(모델100·매출500·시그니처60·리뷰70·조회수10만) 달성 시엔 무조건 디자이너 승급.");

// ══════════ 7B. 시험점수 채점 기준표 ══════════
s = p.addSlide(); s.background = { color: CREAM };
brand(s, "SCORING");
kicker(s, "직급(레벨) 승급심사 · 점수 계산표 · 만점 100");
title(s, "직급 승급, 이렇게 채점", 1.6);
(function(){
  const cols=[
    { head:"시즈 1~3", pass:"합격 75점↑", rows:[["실기","45","3과목 × 15"],["연습","15","월 16회↑ 3점·매일 40분↑"],["SNS","10","월 10회↑ 10점"],["팀교육","10","매달 1회·총 5회 (확인 후 카톡 보고)"],["교육과제","10","기간 내 이행"],["PPT","10","발표"]] },
    { head:"시즈 4~5", pass:"합격 80점↑", rows:[["실기","30","두 과목(각 15)·준비물 감점"],["SNS","30","시그니처 5개월 30개"],["PPT","10","발표"],["교육과제","10","기간 내 이행"],["태도","10","지각 회당 -1"],["연습","10","연습 횟수"]] },
  ];
  const cw=5.95, x0=0.6, gap=0.33, y0=2.75;
  cols.forEach((c,ci)=>{
    const x=x0+ci*(cw+gap);
    s.addShape(p.ShapeType.rect, { x, y:y0, w:cw, h:0.52, fill:{color:INK} });
    s.addText(c.head, { x:x+0.2, y:y0, w:cw*0.5, h:0.52, fontFace:SANS, bold:true, fontSize:15, color:"FFFFFF", valign:"middle" });
    s.addText(c.pass, { x:x+cw*0.4, y:y0, w:cw*0.6-0.2, h:0.52, fontFace:SANS, bold:true, fontSize:13, color:GOLD, align:"right", valign:"middle" });
    c.rows.forEach((r,ri)=>{
      const ry=y0+0.52+ri*0.56;
      if(ri%2) s.addShape(p.ShapeType.rect,{x,y:ry,w:cw,h:0.56,fill:{color:"F1ECE2"}});
      s.addText(r[0], { x:x+0.2, y:ry, w:1.5, h:0.56, fontFace:SANS, bold:true, fontSize:13, color:INK, valign:"middle" });
      s.addText(r[1], { x:x+1.5, y:ry, w:0.7, h:0.56, fontFace:SERIF, bold:true, fontSize:16, color:GOLD, align:"center", valign:"middle" });
      s.addText(r[2], { x:x+2.3, y:ry, w:cw-2.5, h:0.56, fontFace:SANS, fontSize:11.5, color:"555555", valign:"middle" });
    });
  });
})();
s.addText("※ 이건 직급(레벨) 승급 채점표 · 디자이너 승급(헤어쇼 기준·무조건 KPI)은 앞장 참고 — 둘은 다릅니다.", { x:0.6, y:6.75, w:12, h:0.35, fontFace:SANS, fontSize:11.5, color:GRAY, align:"center" });
s.addNotes("이건 '직급(레벨) 승급심사' 점수표(점수_계산표.html 정본). 시즈1~3 합격75↑, 시즈4~5 합격80↑. ↔ 디자이너 승급은 별개(헤어쇼 정량기준+무조건 KPI, 앞장). 두 개를 섞지 말 것.");

// ══════════ 8. Q&A (dark) ══════════
s = p.addSlide(); s.background = { color: INK };
brand(s, "ASK ANYTHING", true);
goldDot(s, 0.6, 2.1);
s.addText("Q & A", { x:0.55, y:2.3, w:8, h:1.3, fontFace:SERIF, bold:false, fontSize:64, color:CREAM });
const qa = [
  ["내 레벨 수업만 들으면 되나요?","네 — 캘린더의 내 레벨(L태그) 과목만."],
  ["준비물은 어디서 봐요?","「과목별 준비물·과제·주의」 문서 (선생님별)."],
  ["디자이너는 어떻게 되나요?","시그니처 쇼 — 4레벨 50%·5레벨 80% 통과 시."],
  ["모델데이·특강은 언제?","매월 2·4주 금(모델) · 3주 금(특강)."],
];
let qy = 4.0;
qa.forEach((q,i)=>{
  const y = qy + i*0.72;
  s.addText("Q", { x:0.6, y, w:0.4, h:0.5, fontFace:SERIF, bold:true, fontSize:20, color:GOLD, valign:"middle" });
  s.addText([
    { text:q[0]+"  ", options:{ color:CREAM, bold:true } },
    { text:q[1], options:{ color:"C9C3B7" } },
  ], { x:1.05, y, w:11.6, h:0.5, fontFace:SANS, fontSize:13.5, valign:"middle" });
});
s.addNotes("자유롭게 질문받기. 위 4개는 자주 나오는 질문 예시.");

// ══════════ 9. CLOSING (dark) ══════════
s = p.addSlide(); s.background = { color: INK };
goldDot(s, W/2-0.36, 2.5);
s.addText("손이랑 마음부터\n혼자 서는 디자이너까지", { x:1, y:2.9, w:11.33, h:1.8,
  fontFace:SERIF, fontSize:42, color:CREAM, align:"center", lineSpacingMultiple:1.1 });
s.addText("AT NOWN · 2026 EDUCATION", { x:1, y:4.9, w:11.33, h:0.4,
  fontFace:SANS, bold:true, fontSize:13, color:GOLD, align:"center", charSpacing:4 });
s.addNotes("마무리. 앞으로의 성장 응원.");

p.writeFile({ fileName: "/tmp/claude-0/-home-user--/fa133f5d-499e-5f85-bdd2-2dc05cb93ceb/scratchpad/시즈_오리엔테이션.pptx" })
  .then(f => console.log("saved:", f));
