const pptxgen = require('pptxgenjs');
const fs = require('fs');
const path = require('path');

const INK="111111", CREAM="F7F5F1", GOLD="A8895E", GRAY="9B958C", LINE="E4DFD6", WHITE="FFFFFF";
const SERIF="Cambria", SANS="Calibri";
const IMG = (f)=> {
  const p = path.join(__dirname,'img',f);
  return fs.existsSync(p) ? p : null;
};

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';           // 13.3 x 7.5
pres.author = 'AT NOWN ACADEMY';
pres.title  = 'L5 일본 이미지분류체계';
const W=13.3, H=7.5;

// ── 공통 조각 ─────────────────────────────────────
function mono(s, dark){
  const c = dark ? CREAM : INK;
  s.addText("AN", {x:0.55,y:0.38,w:0.34,h:0.34,fontFace:SERIF,fontSize:13,bold:true,color:c,align:'center',valign:'middle',margin:0,
    line:{color:c,width:1}, shape:pres.ShapeType.roundRect, rectRadius:0.04});
  s.addText("ATNOWN ACADEMY · L5", {x:1.0,y:0.38,w:4,h:0.34,fontFace:SANS,fontSize:8.5,bold:true,color:dark?GRAY:GRAY,charSpacing:2.6,valign:'middle',margin:0});
}
function tag(s, t){
  s.addText(t, {x:W-1.75,y:0.38,w:1.2,h:0.34,fontFace:SANS,fontSize:8.5,bold:true,color:CREAM,align:'center',valign:'middle',margin:0,
    fill:{color:INK}, shape:pres.ShapeType.roundRect, rectRadius:0.17});
}
function kicker(s, t){
  s.addText(t, {x:0.55,y:0.95,w:9,h:0.28,fontFace:SANS,fontSize:9.5,bold:true,color:GOLD,charSpacing:2.4,margin:0,valign:'middle'});
}
function title(s, runs, y){
  s.addText(runs, {x:0.55,y:y||1.35,w:11.5,h:1.1,fontFace:SERIF,fontSize:38,bold:true,color:INK,margin:0,valign:'top',lineSpacing:44});
}
function cross(s, cx, cy, r, col){   // 좌표 모티프
  s.addShape(pres.ShapeType.line,{x:cx-r,y:cy,w:r*2,h:0,line:{color:col||LINE,width:0.75}});
  s.addShape(pres.ShapeType.line,{x:cx,y:cy-r,w:0,h:r*2,line:{color:col||LINE,width:0.75}});
}

// ── 1. 표지 ───────────────────────────────────────
{
  const s = pres.addSlide(); s.background = {color:INK};
  mono(s,true);
  const cov=IMG('nb_cover.png');
  if(cov){
    s.addImage({path:cov,x:8.75,y:1.05,w:4.05,h:5.4,transparency:12});
  } else {
    cross(s, 10.9, 3.6, 1.9, "3A342C");
    s.addShape(pres.ShapeType.ellipse,{x:10.15,y:2.85,w:1.5,h:1.5,line:{color:GOLD,width:1},fill:{color:INK}});
    s.addText("YOU", {x:10.15,y:2.85,w:1.5,h:1.5,fontFace:SANS,fontSize:9,bold:true,color:GOLD,align:'center',valign:'middle',charSpacing:2,margin:0});
  }
  s.addText([
    {text:"일본 ", options:{color:CREAM}},
    {text:"이미지분류", options:{color:GOLD}},
    {text:"체계", options:{color:CREAM}},
  ], {x:0.85,y:2.45,w:8.6,h:1.9,fontFace:SERIF,fontSize:54,bold:true,margin:0,valign:'middle',lineSpacing:60});
  s.addText("손님의 말을 시술로 옮기는 번역기", {x:0.85,y:4.35,w:8,h:0.4,fontFace:SANS,fontSize:16,color:CREAM,margin:0});
  s.addText("WARM · COOL · SOFT · HARD   |   CHILD · ADULT · CURVE · STRAIGHT",
    {x:0.85,y:4.9,w:9,h:0.32,fontFace:SANS,fontSize:9.5,bold:true,color:GRAY,charSpacing:1.8,margin:0});
  s.addText("2026. 08. 19 (수)  07:30 – 09:30   ·   L5   ·   차노", {x:0.85,y:6.35,w:9,h:0.35,fontFace:SANS,fontSize:11,color:GRAY,margin:0});
  s.addNotes("워드월 10분으로 연다. 구글폼 2문항: ①이미지란 ______다 ②손님 이미지를 잘못 읽어 어긋났던 경험. 오늘의 주인공은 질문 화면이다.");
}

// ── 2. WHY ────────────────────────────────────────
{
  const s = pres.addSlide(); s.background={color:CREAM};
  mono(s); tag(s,"WHY"); kicker(s,"오늘 이걸 배우는 이유");
  title(s,[{text:'"청순하게 해주세요"는\n',options:{color:INK}},{text:"주문서가 아니다.",options:{color:GOLD}}]);
  s.addText("그 말은 좌표다. 좌표로 옮기기 전까지 정해진 건 아무것도 없다.\n같은 단어를 손님과 내가 다른 그림으로 상상하는 순간, 그 시술은 이미 어긋나 있다.",
    {x:0.55,y:3.05,w:7.1,h:0.9,fontFace:SANS,fontSize:13,color:"555555",margin:0,lineSpacing:22});
  const rows=[
    ["감각을 말로 주고받기 위해","일본이 이미지를 나눈 이유는 취향 놀이가 아니다"],
    ["좌표가 없으면 상담은 매번 운","좌표가 있으면 결과가 재현된다"],
    ["L5 시험 기준 = 상담력","좌표를 말로 설명하는 게 곧 상담력이다"],
  ];
  rows.forEach((r,i)=>{
    const y=4.2+i*0.92;
    s.addShape(pres.ShapeType.ellipse,{x:0.55,y:y+0.06,w:0.44,h:0.44,fill:{color:GOLD}});
    s.addText(String(i+1),{x:0.55,y:y+0.06,w:0.44,h:0.44,fontFace:SERIF,fontSize:13,bold:true,color:CREAM,align:'center',valign:'middle',margin:0});
    s.addText(r[0],{x:1.2,y:y,w:5.2,h:0.32,fontFace:SANS,fontSize:14,bold:true,color:INK,margin:0,valign:'middle'});
    s.addText(r[1],{x:1.2,y:y+0.33,w:6.6,h:0.3,fontFace:SANS,fontSize:11,color:GRAY,margin:0,valign:'middle'});
  });
  s.addText("01",{x:11.2,y:5.7,w:1.6,h:1.3,fontFace:SERIF,fontSize:84,bold:true,color:"E8E1D5",align:'right',margin:0});
  s.addNotes("메인 예상 질문. 한 줄 답 → 실제 사례 → 원리 한 장 순서로 답한다. '연예인 누구요?' 한 마디가 좌표를 확정시킨다는 것까지.");
}

// ── 3. A축 ────────────────────────────────────────
{
  const s = pres.addSlide(); s.background={color:CREAM};
  mono(s); tag(s,"AXIS A"); kicker(s,"언어 이미지 스케일 · NCD");
  title(s,[{text:"손님이 ",options:{color:INK}},{text:"원하는 것",options:{color:GOLD}}]);
  s.addText("일본컬러디자인연구소가 만든 색·형용사 좌표.\n가로 WARM ↔ COOL, 세로 SOFT ↔ HARD.\n보조축으로 CLEAR ↔ GRAYISH(맑음↔탁함)가 있다.\n\n형용사도 색도 질감도 전부 이 판 위에 얹힌다.",
    {x:0.55,y:2.5,w:4.0,h:2.0,fontFace:SANS,fontSize:12.5,color:"444444",margin:0,lineSpacing:21});
  s.addText([
    {text:"외울 것은 축뿐이다.\n",options:{bold:true,color:INK,fontSize:13}},
    {text:"위는 밝고 가볍고 여리다 · 아래는 어둡고 무겁고 세다\n왼쪽은 따뜻해 사람 냄새가 난다 · 오른쪽은 차갑고 정돈돼 있다",options:{fontSize:11,color:"555555"}},
  ],{x:0.55,y:4.85,w:4.05,h:1.5,fontFace:SANS,margin:0.14,lineSpacing:18,valign:'middle',fill:{color:WHITE},line:{color:GOLD,width:0.75}});
  const a=IMG('map_a.png'); if(a) s.addImage({path:a,x:5.62,y:1.62,w:7.1,h:5.4});
  s.addNotes("16칸 이름을 순서대로 읊게 하지 말 것. 그 순간 암기 과목이 된다. 축만 잡아주고 애들 손님 케이스를 즉석에서 올려본다.");
}

// ── 4. B축 ────────────────────────────────────────
{
  const s = pres.addSlide(); s.background={color:CREAM};
  mono(s); tag(s,"AXIS B"); kicker(s,"얼굴타입 8분류");
  title(s,[{text:"손님이 ",options:{color:INK}},{text:"이미 가진 것",options:{color:GOLD}}]);
  const b=IMG('map_b.png'); if(b) s.addImage({path:b,x:0.5,y:2.45,w:6.05,h:4.6});
  s.addText("일본 미용에서 상담에 쓰는 얼굴 인상 좌표.\n세로 아이 ↔ 어른, 가로 곡선 ↔ 직선.",
    {x:7.7,y:2.45,w:5.1,h:0.7,fontFace:SANS,fontSize:12.5,color:"444444",margin:0,lineSpacing:21});
  s.addText([
    {text:"얼굴형이 아니라 얼굴 인상이다.\n",options:{bold:true,color:INK,fontSize:13}},
    {text:"계란형·사각형 이야기가 아니다. 우리가 읽는 건 윤곽이 아니라 그 사람이 주는 인상이다.",options:{fontSize:11,color:"555555"}},
  ],{x:7.7,y:3.35,w:5.1,h:1.25,fontFace:SANS,margin:0.14,lineSpacing:18,valign:'middle',fill:{color:WHITE},line:{color:GOLD,width:0.75}});
  s.addText([
    {text:"손님이 자기 얼굴을 잘못 알고 있으면?\n",options:{bold:true,color:GOLD,fontSize:12}},
    {text:'"지금까지 제일 마음에 들었던 머리 사진 있으세요?"\n과거 좌표가 미래 좌표보다 정확하다.',options:{fontSize:11.5,color:"444444"}},
  ],{x:7.7,y:4.95,w:5.1,h:1.3,fontFace:SANS,margin:0,lineSpacing:19,valign:'top'});
  s.addNotes("얼굴형(윤곽)과 얼굴타입(인상)의 차이를 반드시 짚는다. 애들이 제일 많이 헷갈리는 지점.");
}

// ── 5. 8타입 표 ───────────────────────────────────
{
  const s = pres.addSlide(); s.background={color:CREAM};
  mono(s); tag(s,"AXIS B"); kicker(s,"8타입 · 안전한 실루엣");
  title(s,[{text:"어울림은 ",options:{color:INK}},{text:"안전선",options:{color:GOLD}},{text:"이다",options:{color:INK}}]);
  const head=["타입","인상","안전한 실루엣","기본 컬러 방향"];
  const body=[
    ["큐트 · 아이×곡선","동글고 친근함","숏~세미 · 안말음 · 컬 앞머리","핑크 · 베이지"],
    ["액티브 큐트 · 아이×곡선강","발랄·개성","숏~세미 · 뚜렷한 라인 · 일자뱅","오렌지 · 체리 · 블랙"],
    ["프레시 · 아이×직선","산뜻·중성","숏~세미 · 스트레이트 / 겉말음","애쉬 · 베이지"],
    ["쿨 캐주얼 · 아이×직선강","보이시·시크","울프 · 러프한 결","한색 · 올리브"],
    ["페미닌 · 어른×곡선","화사·여성","세미~롱 · 웨이브 · 컬 앞머리","베이지 · 로즈브라운"],
    ["소프트 엘레강트 · 어른×중간","단정·부드러움","숏보브~세미 · 굵은 원컬","내추럴 · 애쉬"],
    ["엘레강트 · 어른×직선약","또렷·세련","롱 · 큰 웨이브 · 앞머리 없음","브라운 계열"],
    ["쿨 · 어른×직선","샤프·도회적","세미~롱 스트레이트","그레이 · 라벤더 그레이지"],
  ];
  const rows=[head.map(t=>({text:t,options:{bold:true,color:GOLD,fontSize:9.5,charSpacing:1.4}}))]
    .concat(body.map(r=>r.map((t,i)=>({text:t,options:{bold:i===0,color:i===3?GOLD:(i===0?INK:"444444"),fontSize:11}}))));
  s.addTable(rows,{x:0.55,y:2.5,w:12.2,colW:[3.3,2.0,4.0,2.9],border:{type:'solid',color:LINE,pt:0.5},
    fontFace:SANS,rowH:0.44,valign:'middle',margin:0.08,fill:{color:CREAM}});
  s.addText("안전을 알아야 의도적으로 어길 수 있다.",{x:0.55,y:6.72,w:9,h:0.35,fontFace:SANS,fontSize:12,bold:true,color:INK,margin:0});
  s.addNotes("이 표를 외우게 하지 말 것. '안전선'이라는 개념만 남기면 된다. 어기는 판단이 L5의 일이라는 걸 다음 장에서 잇는다.");
}

// ── 6. 다리 (다크) ────────────────────────────────
{
  const s = pres.addSlide(); s.background={color:INK};
  mono(s,true);
  s.addText("THE BRIDGE",{x:0,y:1.7,w:W,h:0.3,fontFace:SANS,fontSize:9.5,bold:true,color:GOLD,charSpacing:2.6,align:'center',margin:0});
  s.addText([{text:"두 판은 ",options:{color:CREAM}},{text:"같은 단어",options:{color:GOLD}},{text:"를 쓴다",options:{color:CREAM}}],
    {x:0,y:2.25,w:W,h:0.9,fontFace:SERIF,fontSize:42,bold:true,align:'center',margin:0});
  s.addText("엘레강트 · 캐주얼 · 쿨 — 겹치는 단어가 두 판을 잇는 다리다.",
    {x:0,y:3.3,w:W,h:0.35,fontFace:SANS,fontSize:13,color:GRAY,align:'center',margin:0});
  const cards=[["A 판","원하는 것","손님의 동경 · 무드"],["B 판","가진 것","얼굴이 이미 말하는 것"]];
  cards.forEach((c,i)=>{
    const x=3.55+i*3.3;
    s.addShape(pres.ShapeType.rect,{x:x,y:4.05,w:2.9,h:1.35,fill:{color:"1C1A17"},line:{color:"3A342C",width:0.75}});
    s.addText(c[0],{x:x,y:4.2,w:2.9,h:0.24,fontFace:SANS,fontSize:9,bold:true,color:GOLD,charSpacing:2,align:'center',margin:0});
    s.addText(c[1],{x:x,y:4.5,w:2.9,h:0.4,fontFace:SANS,fontSize:17,bold:true,color:CREAM,align:'center',margin:0});
    s.addText(c[2],{x:x,y:4.95,w:2.9,h:0.3,fontFace:SANS,fontSize:10.5,color:GRAY,align:'center',margin:0});
  });
  s.addText("↔",{x:6.45,y:4.5,w:0.4,h:0.4,fontFace:SANS,fontSize:18,bold:true,color:GOLD,align:'center',valign:'middle',margin:0});
  s.addText([{text:"디자인이란, 그 ",options:{color:CREAM}},{text:"거리",options:{color:GOLD}},{text:"를 다루는 일이다.",options:{color:CREAM}}],
    {x:0,y:5.85,w:W,h:0.6,fontFace:SERIF,fontSize:26,bold:true,align:'center',margin:0});
  s.addNotes("좁히면 어울리고, 벌리면 개성이 된다. 벌리는 건 L5의 영역 — 손님이 감당할 수 있을 때만.");
}

// ── 7. 방법 5단계 ─────────────────────────────────
{
  const s = pres.addSlide(); s.background={color:CREAM};
  mono(s); tag(s,"METHOD"); kicker(s,"오늘의 전부");
  title(s,[{text:"말 → 좌표 → 거리 → ",options:{color:INK}},{text:"변수",options:{color:GOLD}},{text:" → 확인",options:{color:INK}}]);
  const st=[["01","말","손님 단어를 그대로 받아적는다.\n내 말로 바꾸지 않는다"],
            ["02","좌표","A판에 찍는다.\n애매하면 \"연예인 누구요?\""],
            ["03","거리","B판(얼굴)과 얼마나 먼가.\n좁힐지 벌릴지 판단한다"],
            ["04","변수","길이 · 질감 · 컬 · 컬러 · 앞머리\n다섯 개로 번역한다"],
            ["05","확인","변수 5개를 말로 되읽어 준다.\n그게 계약이다"]];
  st.forEach((c,i)=>{
    const x=0.55+i*2.47;
    s.addShape(pres.ShapeType.ellipse,{x:x,y:2.75,w:0.62,h:0.62,fill:{color:i===3?GOLD:CREAM},line:{color:GOLD,width:1}});
    s.addText(c[0],{x:x,y:2.75,w:0.62,h:0.62,fontFace:SERIF,fontSize:14,bold:true,color:i===3?CREAM:GOLD,align:'center',valign:'middle',margin:0});
    s.addText(c[1],{x:x,y:3.55,w:2.2,h:0.4,fontFace:SANS,fontSize:17,bold:true,color:INK,margin:0});
    s.addText(c[2],{x:x,y:4.02,w:2.2,h:1.0,fontFace:SANS,fontSize:10.5,color:"666666",margin:0,lineSpacing:16});
  });
  s.addText([
    {text:"시안의 함정  ",options:{bold:true,color:GOLD,fontSize:12,charSpacing:1.4}},
    {text:"시안에는 결과만 있고 변수가 없다. 시안을 받았으면 거기서 변수 5개를 뽑아 말로 확인해야 계약이 된다. \"이거요\" 하고 끄덕이는 건 계약이 아니다.",options:{fontSize:12,color:"444444"}},
  ],{x:0.55,y:5.55,w:12.2,h:0.95,fontFace:SANS,margin:0.16,lineSpacing:20,valign:'middle',fill:{color:WHITE},line:{color:GOLD,width:0.75}});
  s.addNotes("이 다섯 칸이 오늘 수업의 전부다. 나머지는 이걸 굴리는 연습.");
}

// ── 8. 케이스 3 ───────────────────────────────────
{
  const s = pres.addSlide(); s.background={color:CREAM};
  mono(s); tag(s,"CASE"); kicker(s,"예시 3 · 과제와 같은 포맷");
  title(s,[{text:"실제로 ",options:{color:INK}},{text:"이렇게",options:{color:GOLD}},{text:" 굴린다",options:{color:INK}}]);
  const cs=[
    ['"청순하게요"',"WARM–SOFT · CLEAR","큐트 (아이×곡선)","가깝다 → 좁힌다",
     "세미롱 · 결 매끈 · 끝 원컬 안말음 · 베이지 · 시스루뱅",
     "'청순'이 \"어려 보이게\"인지 \"정돈되게\"인지 갈린다. 되물어야 좌표가 확정된다"],
    ['"시크하게요"',"COOL–HARD · GRAYISH","쿨 (어른×직선)","가깝다 → 5% 남긴다",
     "세미~롱 · 매끈 · 스트레이트 · 그레이지 · 앞머리 없음",
     "100% 맞추면 차가워 보인다. 끝에 살짝 C컬 하나만 남겨 사람 온도를 만든다"],
    ['"센 언니처럼요"',"WARM–HARD · 다이나믹","큐트 (아이×곡선)","멀다 → 일부러 벌린다",
     "단발 · 질감 거칠게 · 끝 꺾임 · 어두운 애쉬 · 일자뱅",
     "부조화가 개성이 되려면 손님이 감당해야 한다. 직업·나이·아침 관리시간을 먼저 묻는다"],
  ];
  cs.forEach((c,i)=>{
    const x=0.55+i*4.1, w=3.85;
    s.addShape(pres.ShapeType.rect,{x:x,y:2.5,w:w,h:4.1,fill:{color:WHITE},line:{color:LINE,width:0.75}});
    s.addText(c[0],{x:x+0.22,y:2.72,w:w-0.44,h:0.4,fontFace:SANS,fontSize:16,bold:true,color:INK,margin:0});
    s.addText([{text:"A 좌표  ",options:{color:GOLD,bold:true,fontSize:8.5,charSpacing:1.2}},{text:c[1],options:{color:"444444",fontSize:11}}],
      {x:x+0.22,y:3.2,w:w-0.44,h:0.34,fontFace:SANS,margin:0,valign:'middle'});
    s.addText([{text:"B 얼굴  ",options:{color:GOLD,bold:true,fontSize:8.5,charSpacing:1.2}},{text:c[2],options:{color:"444444",fontSize:11}}],
      {x:x+0.22,y:3.56,w:w-0.44,h:0.34,fontFace:SANS,margin:0,valign:'middle'});
    s.addText(c[3],{x:x+0.22,y:3.98,w:w-0.44,h:0.34,fontFace:SANS,fontSize:12,bold:true,color:i===2?GOLD:INK,margin:0,valign:'middle'});
    s.addText("변수 5",{x:x+0.22,y:4.42,w:w-0.44,h:0.22,fontFace:SANS,fontSize:8.5,bold:true,color:GOLD,charSpacing:1.2,margin:0});
    s.addText(c[4],{x:x+0.22,y:4.66,w:w-0.44,h:0.8,fontFace:SANS,fontSize:10.5,color:"444444",margin:0,lineSpacing:16});
    s.addText([{text:"함정  ",options:{color:GOLD,bold:true,fontSize:8.5,charSpacing:1.2}},{text:c[5],options:{color:"666666",fontSize:10}}],
      {x:x+0.22,y:5.52,w:w-0.44,h:0.95,fontFace:SANS,margin:0,lineSpacing:15,valign:'top'});
  });
  s.addNotes("3번이 오늘의 핵심 케이스. 벌리는 판단 = 상담력 = L5 시험 기준. 여기서 시간을 제일 많이 쓴다.");
}

// ── 8-B. 세 사람, 세 좌표 (나노바나나 이미지가 있을 때만) ──
{
  const c1=IMG('nb_case1.png'), c2=IMG('nb_case2.png'), c3=IMG('nb_case3.png');
  if(c1&&c2&&c3){
    const s = pres.addSlide(); s.background={color:CREAM};
    mono(s); tag(s,"CASE"); kicker(s,"같은 다섯 변수, 다른 좌표");
    title(s,[{text:"세 사람, ",options:{color:INK}},{text:"세 좌표",options:{color:GOLD}}]);
    const cap=[
      ["청순","WARM–SOFT · CLEAR","좁힌 결과"],
      ["시크","COOL–HARD · GRAYISH","5% 남긴 결과"],
      ["센 언니","WARM–HARD · 다이나믹","일부러 벌린 결과"],
    ];
    [c1,c2,c3].forEach((img,i)=>{
      const x=0.55+i*4.1, w=3.85;
      s.addImage({path:img,x:x,y:2.45,w:w,h:3.3});
      s.addText(cap[i][0],{x:x,y:5.95,w:w,h:0.4,fontFace:SANS,fontSize:19,bold:true,color:INK,margin:0});
      s.addText(cap[i][1],{x:x,y:6.4,w:w,h:0.28,fontFace:SANS,fontSize:10,bold:true,color:GOLD,charSpacing:1.2,margin:0});
      s.addText(cap[i][2],{x:x,y:6.7,w:w,h:0.28,fontFace:SANS,fontSize:10.5,color:GRAY,margin:0});
    });
    s.addNotes("같은 다섯 변수(길이·질감·컬·컬러·앞머리)를 어떻게 돌리느냐로 좌표가 옮겨간다는 걸 눈으로 보여주는 장.");
  }
}

// ── 9. 우리 서사 ──────────────────────────────────
{
  const s = pres.addSlide(); s.background={color:CREAM};
  mono(s); tag(s,"AT NOWN"); kicker(s,"왜 하필 지금 이 수업인가");
  title(s,[{text:"오늘은 ",options:{color:INK}},{text:"바닥판",options:{color:GOLD}},{text:"이다",options:{color:INK}}]);
  const k=[["8/23 · L3","질감마스터 1","SOFT ↔ HARD 를 가위로 만드는 법"],
           ["8/27 · L4","형용사 이론","이 좌표 위에 말을 얹는 수업"],
           ["9/22 · L5","퍼스널컬러와 구조","이 좌표 위에 색을 얹는 수업. NCD는 원래 색 체계다"],
           ["11/6 · L5","골격과 구조커트","이 좌표 위에 몸을 얹는 수업"]];
  k.forEach((c,i)=>{
    const x=0.55+(i%2)*6.25, y=2.6+Math.floor(i/2)*1.75;
    s.addShape(pres.ShapeType.rect,{x:x,y:y,w:5.95,h:1.5,fill:{color:WHITE},line:{color:LINE,width:0.75}});
    s.addText(c[0],{x:x+0.28,y:y+0.2,w:5.4,h:0.24,fontFace:SANS,fontSize:9,bold:true,color:GOLD,charSpacing:1.6,margin:0});
    s.addText(c[1],{x:x+0.28,y:y+0.5,w:5.4,h:0.36,fontFace:SANS,fontSize:16,bold:true,color:INK,margin:0});
    s.addText(c[2],{x:x+0.28,y:y+0.92,w:5.4,h:0.42,fontFace:SANS,fontSize:11,color:"666666",margin:0,lineSpacing:15});
  });
  s.addText("Four classes, one map.",{x:0.55,y:6.35,w:8,h:0.45,fontFace:SERIF,fontSize:22,italic:true,color:GOLD,margin:0});
  s.addNotes("오늘이 따로 노는 수업이 아니라는 걸 반드시 붙인다. 애들이 '이거 왜 배워요'를 안 묻게 되는 지점.");
}

// ── 10. 공부법 + 과제 ─────────────────────────────
{
  const s = pres.addSlide(); s.background={color:CREAM};
  mono(s); tag(s,"HOMEWORK"); kicker(s,"공부하는 법 · 그리고 과제");
  title(s,[{text:"감이 아니라 ",options:{color:INK}},{text:"기록",options:{color:GOLD}},{text:"으로 는다",options:{color:INK}}]);
  const p=[["한 손님 = 한 좌표 기록","말 → 좌표 → 얼굴타입 → 거리 → 변수 5개 → 결과 사진. 여섯 칸"],
           ["인스타 100장 좌표 찍기","저장한 시안을 A판에 흩뿌려 봐라 — 몰린 곳이 내 한계이자 내 시그니처다"],
           ["질문하는 법","\"뭐 해드려요?\" 가 아니라 \"이렇게 좌표 찍었는데, 좁혀야 할까요 벌려야 할까요?\""]];
  p.forEach((r,i)=>{
    const y=2.55+i*0.88;
    s.addShape(pres.ShapeType.ellipse,{x:0.55,y:y+0.08,w:0.4,h:0.4,line:{color:GOLD,width:1},fill:{color:CREAM}});
    s.addText(String(i+1),{x:0.55,y:y+0.08,w:0.4,h:0.4,fontFace:SERIF,fontSize:12,bold:true,color:GOLD,align:'center',valign:'middle',margin:0});
    s.addText(r[0],{x:1.15,y:y,w:5.0,h:0.32,fontFace:SANS,fontSize:14,bold:true,color:INK,margin:0,valign:'middle'});
    s.addText(r[1],{x:1.15,y:y+0.33,w:11.5,h:0.34,fontFace:SANS,fontSize:11,color:"666666",margin:0,valign:'middle'});
  });
  s.addShape(pres.ShapeType.rect,{x:0.55,y:5.3,w:12.2,h:1.55,fill:{color:INK}});
  s.addText("과제 · 다음 수업까지",{x:0.85,y:5.5,w:6,h:0.28,fontFace:SANS,fontSize:9.5,bold:true,color:GOLD,charSpacing:2,margin:0});
  s.addText([
    {text:"① 분류체계 요약 1장 — 축 2개 + 칸 이름. 안 보고 그린다\n",options:{}},
    {text:"② 실제 손님 예시 3건 — 말 → 좌표 → 거리 → 변수 5개 → 결과",options:{}},
  ],{x:0.85,y:5.85,w:8.5,h:0.8,fontFace:SANS,fontSize:13,color:CREAM,margin:0,lineSpacing:22});
  s.addText("실패 케이스는 감점 없음.\n왜 어긋났는지 쓰면 오히려 가점.",{x:9.6,y:5.8,w:3.0,h:0.9,fontFace:SANS,fontSize:11,color:GOLD,margin:0,lineSpacing:17,align:'right'});
  s.addNotes("채점 기준을 미리 공개한다. 축이 맞나 / 말을 그대로 옮겼나 / 거리 판단에 이유가 있나 / 변수 5개가 다 찼나.");
}

// ── 11. 클로징 (다크) ─────────────────────────────
{
  const s = pres.addSlide(); s.background={color:INK};
  mono(s,true);
  cross(s, 6.65, 3.15, 1.5, "3A342C");
  s.addText("CLOSING",{x:0,y:1.55,w:W,h:0.3,fontFace:SANS,fontSize:9.5,bold:true,color:GOLD,charSpacing:2.6,align:'center',margin:0});
  s.addText([{text:"체계를 ",options:{color:CREAM}},{text:"외우지",options:{color:GOLD}},{text:" 마라",options:{color:CREAM}}],
    {x:0,y:2.65,w:W,h:0.95,fontFace:SERIF,fontSize:44,bold:true,align:'center',margin:0});
  s.addText("좌표는 손님 앞에서 꺼내는 자가 아니다. 내 머릿속 지도다.\n지도를 보여주는 사람은 길을 모르는 사람이다.",
    {x:0,y:3.8,w:W,h:0.8,fontFace:SANS,fontSize:13,color:GRAY,align:'center',margin:0,lineSpacing:24});
  s.addText([{text:"이미지 분류는 취향 놀이가 아니라,\n손님 말을 시술로 옮기는 ",options:{color:CREAM}},{text:"번역기",options:{color:GOLD}},{text:"다.",options:{color:CREAM}}],
    {x:0,y:5.0,w:W,h:1.1,fontFace:SERIF,fontSize:27,bold:true,align:'center',margin:0,lineSpacing:38});
  s.addText("AT NOWN ACADEMY · L5 IMAGE CLASSIFICATION · 2026.08.19 · CHANO",
    {x:0,y:6.8,w:W,h:0.3,fontFace:SANS,fontSize:8.5,bold:true,color:"4A443B",charSpacing:2.4,align:'center',margin:0});
  s.addNotes("워드월로 돌아간다. '지금 다시 쓰면, 이미지란 ______다?' 시작 화면과 비교. 남은 질문은 8/27 형용사 이론 소재로 회수.");
}

pres.writeFile({fileName:'/tmp/edu819/L5_일본_이미지분류체계.pptx'}).then(f=>console.log("WROTE",f));
