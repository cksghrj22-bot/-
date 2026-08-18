/* 앳나운 아카데미 · L5 「일본 이미지분류체계」 학습자료 생성기
   성격: 정보 전달용 중립 자료. 주장·지시·단정 표현을 쓰지 않는다.
   이미지: img/ 안의 파일이 있으면 얹고, 없으면 그 자리를 비워 레이아웃이 그대로 성립한다. */
const pptxgen = require('pptxgenjs');
const fs = require('fs'), path = require('path');

const INK="111111", CREAM="F7F5F1", GOLD="A8895E", GRAY="9B958C",
      LINE="E4DFD6", WHITE="FFFFFF", BODY="444444", MUTE="666666";
const SERIF="Cambria", SANS="Calibri";
const IMG = f => { const p = path.join(__dirname,'img',f); return fs.existsSync(p) ? p : null; };

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';                 // 13.3 x 7.5
pres.author = 'AT NOWN ACADEMY';
pres.title  = '일본 이미지분류체계 — 학습자료';
pres.subject= 'L5 · 2026-08-19';
const W = 13.3;

/* ── 공통 요소 ─────────────────────────────── */
function mono(s, dark){
  const c = dark ? CREAM : INK;
  s.addText("AN",{x:0.55,y:0.38,w:0.34,h:0.34,fontFace:SERIF,fontSize:13,bold:true,color:c,
    align:'center',valign:'middle',margin:0,line:{color:c,width:1},
    shape:pres.ShapeType.roundRect,rectRadius:0.04});
  s.addText("ATNOWN ACADEMY · 학습자료",{x:1.0,y:0.38,w:5,h:0.34,fontFace:SANS,fontSize:8.5,
    bold:true,color:GRAY,charSpacing:2.4,valign:'middle',margin:0});
}
function pageNo(s,n,total){
  s.addText(`${n} / ${total}`,{x:W-1.7,y:0.38,w:1.15,h:0.34,fontFace:SANS,fontSize:9,
    color:GRAY,align:'right',valign:'middle',margin:0});
}
function kicker(s,t){
  s.addText(t,{x:0.55,y:0.95,w:9,h:0.28,fontFace:SANS,fontSize:9.5,bold:true,color:GOLD,
    charSpacing:2.2,margin:0,valign:'middle'});
}
function title(s,runs,y){
  s.addText(runs,{x:0.55,y:y||1.32,w:11.9,h:0.85,fontFace:SERIF,fontSize:33,bold:true,
    color:INK,margin:0,valign:'top',lineSpacing:40});
}
function lead(s,t,y,w){
  s.addText(t,{x:0.55,y:y,w:w||11.9,h:0.75,fontFace:SANS,fontSize:12.5,color:BODY,
    margin:0,lineSpacing:22});
}
function note(s,label,text,x,y,w,h){
  s.addText([{text:label+"\n",options:{bold:true,color:GOLD,fontSize:10.5,charSpacing:1.2}},
             {text:text,options:{fontSize:11.5,color:BODY}}],
    {x:x,y:y,w:w,h:h,fontFace:SANS,margin:0.15,lineSpacing:19,valign:'middle',
     fill:{color:WHITE},line:{color:LINE,width:0.75}});
}
const HAS_CASES = !!(IMG('nb_case1.png') && IMG('nb_case2.png') && IMG('nb_case3.png'));
const TOTAL = HAS_CASES ? 15 : 14;
let pg = 0;
function slide(dark){
  const s = pres.addSlide();
  s.background = {color: dark ? INK : CREAM};
  mono(s,dark); pg++;
  if(!dark) pageNo(s,pg,TOTAL);
  return s;
}

/* ── 1. 표지 ───────────────────────────────── */
{
  const s = slide(true);
  const cov = IMG('nb_cover.png') || IMG('fig_cover.png');
  if(cov) s.addImage({path:cov,x:8.7,y:0.95,w:4.1,h:5.55,transparency:8});
  s.addText([{text:"일본 ",options:{color:CREAM}},{text:"이미지분류체계",options:{color:GOLD}}],
    {x:0.85,y:2.35,w:7.6,h:1.0,fontFace:SERIF,fontSize:46,bold:true,margin:0,valign:'middle'});
  s.addText("이미지를 나타내는 말을 좌표로 정리하는 방법",
    {x:0.85,y:3.5,w:7.6,h:0.4,fontFace:SANS,fontSize:16,color:CREAM,margin:0});
  s.addText("일본에서 정리된 두 가지 분류 체계와, 그것이 헤어디자인 상담에서 어떻게 쓰이는지를 정리한 학습자료입니다.",
    {x:0.85,y:4.05,w:7.4,h:0.7,fontFace:SANS,fontSize:11.5,color:GRAY,margin:0,lineSpacing:20});
  s.addText("2026. 08. 19 (수)   ·   L5   ·   앳나운 아카데미",
    {x:0.85,y:6.3,w:8,h:0.35,fontFace:SANS,fontSize:11,color:GRAY,margin:0});
  s.addNotes("이 자료는 두 가지 분류 체계를 소개하는 정보 자료입니다. 각 체계의 출처와 구성, 그리고 헤어 요소와 연결되는 지점을 순서대로 다룹니다.");
}

/* ── 2. 목차 ───────────────────────────────── */
{
  const s = slide(); kicker(s,"이 자료에서 다루는 내용");
  title(s,[{text:"목차",options:{color:INK}}]);
  const toc=[
    ["01","이미지분류체계의 배경","어떤 필요에서 만들어졌고 어디에 쓰이는지"],
    ["02","언어 이미지 스케일 (NCD)","두 개의 축과 16개 이미지 카테고리"],
    ["03","얼굴타입 분류","두 개의 축과 8개 타입, 타입별 특징"],
    ["04","두 체계에서 겹치는 용어","같은 단어가 서로 다른 축 위에 놓이는 경우"],
    ["05","헤어 요소로 옮겨 볼 때의 항목","길이 · 질감 · 컬 · 컬러 · 앞머리"],
  ];
  toc.forEach((t,i)=>{
    const y = 2.5 + i*0.88;
    s.addText(t[0],{x:0.55,y:y,w:0.7,h:0.4,fontFace:SERIF,fontSize:18,bold:true,color:GOLD,margin:0,valign:'middle'});
    s.addText(t[1],{x:1.35,y:y,w:4.6,h:0.4,fontFace:SANS,fontSize:16,bold:true,color:INK,margin:0,valign:'middle'});
    s.addText(t[2],{x:6.1,y:y,w:6.6,h:0.4,fontFace:SANS,fontSize:12,color:MUTE,margin:0,valign:'middle'});
    if(i<toc.length-1) s.addShape(pres.ShapeType.line,{x:0.55,y:y+0.62,w:12.2,h:0,line:{color:LINE,width:0.75}});
  });
  s.addNotes("전체 흐름을 먼저 안내합니다. 02·03이 각 체계의 소개, 04·05가 두 체계를 함께 볼 때의 참고 항목입니다.");
}

/* ── 3. 배경 ───────────────────────────────── */
{
  const s = slide(); kicker(s,"01. 배경");
  title(s,[{text:"이미지분류체계는 ",options:{color:INK}},{text:"감각을 말로 옮기기 위한 정리 방식",options:{color:GOLD}},{text:"입니다",options:{color:INK}}]);
  lead(s,"「청순한」 「시크한」 「내추럴한」 같은 말은 사람마다 떠올리는 그림이 조금씩 다릅니다. 일본에서는 색채·디자인 분야를 중심으로 이런 이미지 형용사를 좌표 위에 배치해 정리하는 방식이 발전했고, 이후 미용·패션 상담에서도 참고 자료로 쓰이고 있습니다.",2.4);
  const cards=[
    ["쓰이는 곳","색채 계획 · 제품 디자인 · 인테리어 · 패션 · 미용 상담"],
    ["정리 방식","형용사를 두 개의 축 위에 배치해 서로의 거리를 눈으로 확인"],
    ["참고할 때","정답표가 아니라, 대화를 맞춰 보기 위한 공통 지도로 사용"],
  ];
  cards.forEach((c,i)=>{
    const x = 0.55 + i*4.1;
    s.addShape(pres.ShapeType.rect,{x:x,y:3.85,w:3.85,h:1.85,fill:{color:WHITE},line:{color:LINE,width:0.75}});
    s.addText(c[0],{x:x+0.25,y:4.1,w:3.35,h:0.32,fontFace:SANS,fontSize:13.5,bold:true,color:GOLD,margin:0});
    s.addText(c[1],{x:x+0.25,y:4.5,w:3.35,h:1.0,fontFace:SANS,fontSize:11.5,color:BODY,margin:0,lineSpacing:19});
  });
  note(s,"이 자료의 범위","여기서는 두 체계의 구성과 용어를 소개하는 데까지를 다룹니다. 실제 시술 판단은 모발 상태·생활 조건 등 다른 정보와 함께 종합적으로 검토하게 됩니다.",0.55,6.0,12.2,1.0);
  s.addNotes("체계의 목적이 '분류 자체'가 아니라 '대화를 맞추는 것'에 있다는 점을 소개합니다.");
}

/* ── 4. 두 체계 개요 ───────────────────────── */
{
  const s = slide(); kicker(s,"01. 배경");
  title(s,[{text:"이 자료에서는 ",options:{color:INK}},{text:"두 가지 체계",options:{color:GOLD}},{text:"를 함께 살펴봅니다",options:{color:INK}}]);
  const two=[
    ["A","언어 이미지 스케일","NCD (일본컬러디자인연구소)",
      "가로축 WARM ↔ COOL\n세로축 SOFT ↔ HARD\n보조축 CLEAR ↔ GRAYISH",
      "이미지 형용사 16개를 좌표에 배치합니다. 색·질감·분위기를 함께 놓고 볼 수 있어, 손님이 말한 표현이 어느 쪽 성격인지 가늠할 때 참고합니다."],
    ["B","얼굴타입 분류","일본 미용 상담에서 쓰이는 8분류",
      "세로축 아이 인상 ↔ 어른 인상\n가로축 곡선 ↔ 직선",
      "얼굴이 주는 인상을 8가지로 나눕니다. 윤곽(계란형·사각형 등)과는 다른 기준이며, 타입별로 자주 어울린다고 소개되는 실루엣이 정리되어 있습니다."],
  ];
  two.forEach((t,i)=>{
    const x = 0.55 + i*6.25;
    s.addShape(pres.ShapeType.rect,{x:x,y:2.45,w:5.95,h:4.25,fill:{color:WHITE},line:{color:LINE,width:0.75}});
    s.addShape(pres.ShapeType.ellipse,{x:x+0.28,y:2.7,w:0.5,h:0.5,fill:{color:GOLD}});
    s.addText(t[0],{x:x+0.28,y:2.7,w:0.5,h:0.5,fontFace:SERIF,fontSize:14,bold:true,color:CREAM,align:'center',valign:'middle',margin:0});
    s.addText(t[1],{x:x+0.95,y:2.7,w:4.7,h:0.32,fontFace:SANS,fontSize:17,bold:true,color:INK,margin:0,valign:'middle'});
    s.addText(t[2],{x:x+0.95,y:3.04,w:4.7,h:0.26,fontFace:SANS,fontSize:10.5,color:GRAY,margin:0,valign:'middle'});
    s.addText(t[3],{x:x+0.3,y:3.55,w:5.35,h:1.0,fontFace:SANS,fontSize:12,bold:true,color:GOLD,margin:0.12,lineSpacing:20,
      fill:{color:CREAM}});
    s.addText(t[4],{x:x+0.3,y:4.75,w:5.35,h:1.7,fontFace:SANS,fontSize:11.5,color:BODY,margin:0,lineSpacing:19});
  });
  s.addNotes("두 체계는 서로 다른 것을 봅니다. A는 이미지 표현 자체를, B는 얼굴이 주는 인상을 분류합니다.");
}

/* ── 5. A축 좌표판 ─────────────────────────── */
{
  const s = slide(); kicker(s,"02. 언어 이미지 스케일 (NCD)");
  title(s,[{text:"두 개의 축으로 ",options:{color:INK}},{text:"이미지 형용사",options:{color:GOLD}},{text:"를 배치합니다",options:{color:INK}}]);
  s.addText([
    {text:"가로축 · WARM ↔ COOL\n",options:{bold:true,fontSize:13,color:INK}},
    {text:"따뜻한 쪽과 차가운 쪽. 색온도뿐 아니라 분위기의 온도도 함께 봅니다.\n\n",options:{fontSize:11.5,color:BODY}},
    {text:"세로축 · SOFT ↔ HARD\n",options:{bold:true,fontSize:13,color:INK}},
    {text:"위쪽은 밝고 가벼운 느낌, 아래쪽은 어둡고 무게감 있는 느낌으로 정리됩니다.\n\n",options:{fontSize:11.5,color:BODY}},
    {text:"보조축 · CLEAR ↔ GRAYISH\n",options:{bold:true,fontSize:13,color:INK}},
    {text:"맑고 선명한 쪽과 탁하고 차분한 쪽을 구분합니다. 시크·엘레강트·클래식·댄디는 GRAYISH 쪽에 놓이는 것으로 소개됩니다.",options:{fontSize:11.5,color:BODY}},
  ],{x:0.55,y:2.4,w:4.5,h:3.3,fontFace:SANS,margin:0,lineSpacing:19,valign:'top'});
  note(s,"참고","축의 위치는 절대적인 값이 아니라 상대적인 배치입니다. 자료마다 좌표가 조금씩 다르게 소개되기도 합니다.",0.55,5.9,4.5,1.05);
  const a = IMG('map_a.png'); if(a) s.addImage({path:a,x:6.05,y:2.12,w:6.7,h:5.09});
  s.addNotes("16칸의 이름보다 두 축의 방향을 먼저 안내하면 이해가 빠릅니다.");
}

/* ── 6~7. A 카테고리 설명 ──────────────────── */
const CATS = [
  ["로맨틱","ROMANTIC","부드럽고 달콤한 느낌. 밝고 여린 색조와 가벼운 질감이 함께 놓입니다."],
  ["프리티","PRETTY","귀엽고 발랄한 느낌. 따뜻하고 선명한 색조가 중심입니다."],
  ["클리어","CLEAR","맑고 산뜻한 느낌. 투명감 있는 밝은 색조가 특징으로 소개됩니다."],
  ["내추럴","NATURAL","자연스럽고 편안한 느낌. 중간 밝기의 부드러운 색조가 놓입니다."],
  ["캐주얼","CASUAL","경쾌하고 활동적인 느낌. 따뜻하고 선명한 색조가 함께 쓰입니다."],
  ["쿨 캐주얼","COOL CASUAL","산뜻하면서 시원한 느낌. 차가운 계열의 밝은 색조가 중심입니다."],
  ["엘레강트","ELEGANT","우아하고 단정한 느낌. 중간 톤에 차분한 색조가 놓입니다."],
  ["시크","CHIC","절제되고 세련된 느낌. 탁하고 차분한 색조 쪽에 배치됩니다."],
  ["다이나믹","DYNAMIC","힘 있고 활동적인 느낌. 진하고 강한 색조가 함께 놓입니다."],
  ["와일드","WILD","거칠고 자연스러운 느낌. 어둡고 따뜻한 색조가 중심입니다."],
  ["고저스","GORGEOUS","화려하고 풍성한 느낌. 깊이 있는 진한 색조가 놓입니다."],
  ["에스닉","ETHNIC","토속적이고 개성 있는 느낌. 따뜻하고 어두운 색조가 특징입니다."],
  ["클래식","CLASSIC","전통적이고 안정된 느낌. 차분하고 어두운 색조가 놓입니다."],
  ["댄디","DANDY","정돈되고 단정한 느낌. 차가우면서 어두운 색조 쪽입니다."],
  ["모던","MODERN","간결하고 도시적인 느낌. 차갑고 명암 대비가 뚜렷한 쪽입니다."],
  ["포멀","FORMAL","격식 있고 단정한 느낌. 차갑고 어두운 색조에 배치됩니다."],
];
[[0,8,"위쪽 · SOFT 계열에서 중간까지"],[8,16,"아래쪽 · HARD 계열"]].forEach(([a,b,sub],idx)=>{
  const s = slide(); kicker(s,"02. 언어 이미지 스케일 (NCD)");
  title(s,[{text:"16개 이미지 카테고리 ",options:{color:INK}},{text:`(${idx+1}/2)`,options:{color:GOLD}}]);
  s.addText(sub,{x:0.55,y:2.15,w:8,h:0.3,fontFace:SANS,fontSize:11.5,color:GRAY,margin:0});
  CATS.slice(a,b).forEach((c,i)=>{
    const col = i % 2, row = Math.floor(i/2);
    const x = 0.55 + col*6.25, y = 2.6 + row*1.15;
    s.addShape(pres.ShapeType.rect,{x:x,y:y,w:5.95,h:0.98,fill:{color:WHITE},line:{color:LINE,width:0.75}});
    s.addText(c[0],{x:x+0.25,y:y+0.13,w:2.2,h:0.3,fontFace:SANS,fontSize:14,bold:true,color:INK,margin:0,valign:'middle'});
    s.addText(c[1],{x:x+2.4,y:y+0.16,w:3.3,h:0.26,fontFace:SANS,fontSize:9,bold:true,color:GOLD,charSpacing:1.3,margin:0,valign:'middle'});
    s.addText(c[2],{x:x+0.25,y:y+0.46,w:5.45,h:0.42,fontFace:SANS,fontSize:10.5,color:MUTE,margin:0,lineSpacing:15});
  });
  s.addNotes("카테고리 이름은 참고용입니다. 자료에 따라 번역어가 조금씩 다르게 쓰이기도 합니다.");
});

/* ── 8. B축 좌표판 ─────────────────────────── */
{
  const s = slide(); kicker(s,"03. 얼굴타입 분류");
  title(s,[{text:"얼굴이 주는 ",options:{color:INK}},{text:"인상",options:{color:GOLD}},{text:"을 두 축으로 나눕니다",options:{color:INK}}]);
  const b = IMG('map_b.png'); if(b) s.addImage({path:b,x:0.5,y:2.45,w:6.05,h:4.6});
  s.addText([
    {text:"세로축 · 아이 인상 ↔ 어른 인상\n",options:{bold:true,fontSize:13,color:INK}},
    {text:"이목구비의 배치와 얼굴의 세로 길이 등에서 받는 인상을 기준으로 나눕니다.\n\n",options:{fontSize:11.5,color:BODY}},
    {text:"가로축 · 곡선 ↔ 직선\n",options:{bold:true,fontSize:13,color:INK}},
    {text:"윤곽선과 이목구비의 형태가 둥근 쪽인지 각진 쪽인지를 기준으로 나눕니다.",options:{fontSize:11.5,color:BODY}},
  ],{x:7.0,y:2.5,w:5.75,h:2.1,fontFace:SANS,margin:0,lineSpacing:19,valign:'top'});
  note(s,"얼굴형과는 다른 기준입니다","계란형·사각형처럼 윤곽을 나누는 분류와는 다릅니다. 여기서는 윤곽보다 전체적으로 받는 인상을 기준으로 삼습니다.",7.0,4.75,5.75,1.15);
  note(s,"참고하면 좋은 질문","「지금까지 마음에 들었던 머리 사진이 있으신가요?」처럼 과거의 경험을 물어보면, 인상에 대한 서로의 기준을 맞추는 데 도움이 됩니다.",7.0,6.05,5.75,1.0);
  s.addNotes("얼굴형(윤곽)과 얼굴타입(인상)은 서로 다른 분류라는 점을 안내합니다.");
}

/* ── 9. B 8타입 표 ─────────────────────────── */
{
  const s = slide(); kicker(s,"03. 얼굴타입 분류");
  title(s,[{text:"8개 타입과 ",options:{color:INK}},{text:"자주 소개되는 실루엣",options:{color:GOLD}}]);
  s.addText("아래 내용은 일본 미용 자료에서 타입별로 자주 함께 소개되는 경향을 정리한 것입니다. 개인차가 있어 참고 항목으로 보시면 됩니다.",
    {x:0.55,y:2.12,w:12.2,h:0.32,fontFace:SANS,fontSize:11,color:GRAY,margin:0});
  const head=["타입","축","받는 인상","자주 소개되는 길이·질감","자주 소개되는 컬러"];
  const body=[
    ["큐트","아이 × 곡선","동그랗고 친근한","숏~세미 · 끝 안말음 · 컬 앞머리","핑크 · 베이지"],
    ["액티브 큐트","아이 × 곡선(강)","발랄하고 개성 있는","숏~세미 · 또렷한 라인 · 일자뱅","오렌지 · 체리 · 블랙"],
    ["프레시","아이 × 직선","산뜻하고 중성적인","숏~세미 · 스트레이트 / 겉말음","애쉬 · 베이지"],
    ["쿨 캐주얼","아이 × 직선(강)","보이시하고 시원한","울프 · 결이 살아있는 질감","한색 · 올리브"],
    ["페미닌","어른 × 곡선","화사하고 부드러운","세미~롱 · 웨이브 · 컬 앞머리","베이지 · 로즈브라운"],
    ["소프트 엘레강트","어른 × 중간","단정하고 온화한","숏보브~세미 · 굵은 원컬","내추럴 · 애쉬"],
    ["엘레강트","어른 × 직선(약)","또렷하고 세련된","롱 · 큰 웨이브 · 앞머리 없음","브라운 계열"],
    ["쿨","어른 × 직선","샤프하고 도회적인","세미~롱 · 스트레이트","그레이 · 라벤더 그레이지"],
  ];
  const rows=[head.map(t=>({text:t,options:{bold:true,color:GOLD,fontSize:9.5,charSpacing:1.3}}))]
    .concat(body.map(r=>r.map((t,i)=>({text:t,options:{bold:i===0,color:i===4?GOLD:(i===0?INK:BODY),fontSize:10.5}}))));
  s.addTable(rows,{x:0.55,y:2.6,w:12.2,colW:[2.05,1.95,2.1,3.9,2.2],
    border:{type:'solid',color:LINE,pt:0.5},fontFace:SANS,rowH:0.44,valign:'middle',
    margin:0.08,fill:{color:CREAM}});
  s.addNotes("표의 내용은 경향이며 개인차가 큽니다. 참고 항목으로 안내합니다.");
}

/* ── 10. 겹치는 용어 ───────────────────────── */
{
  const s = slide(); kicker(s,"04. 두 체계를 함께 볼 때");
  title(s,[{text:"같은 단어가 ",options:{color:INK}},{text:"두 체계 모두",options:{color:GOLD}},{text:"에 등장합니다",options:{color:INK}}]);
  lead(s,"엘레강트 · 쿨 캐주얼 · 쿨처럼 겹치는 이름이 있습니다. 다만 A는 이미지 표현을, B는 얼굴 인상을 가리키므로 같은 이름이라도 설명하는 대상이 다릅니다. 두 자료를 함께 볼 때 참고하시면 좋습니다.",2.35);
  const ov=[
    ["엘레강트","중간 톤의 우아하고 단정한 이미지","어른 인상에 직선이 약간 섞인 얼굴 타입"],
    ["쿨 캐주얼","차가운 계열의 산뜻하고 경쾌한 이미지","아이 인상에 직선이 뚜렷한 얼굴 타입"],
    ["쿨","모던·포멀과 인접한 차가운 영역","어른 인상에 직선이 뚜렷한 얼굴 타입"],
  ];
  s.addText("용어",{x:0.75,y:3.5,w:2.2,h:0.3,fontFace:SANS,fontSize:9.5,bold:true,color:GOLD,charSpacing:1.4,margin:0});
  s.addText("A · 언어 이미지 스케일에서",{x:3.15,y:3.5,w:4.6,h:0.3,fontFace:SANS,fontSize:9.5,bold:true,color:GOLD,charSpacing:1.2,margin:0});
  s.addText("B · 얼굴타입 분류에서",{x:8.15,y:3.5,w:4.6,h:0.3,fontFace:SANS,fontSize:9.5,bold:true,color:GOLD,charSpacing:1.2,margin:0});
  ov.forEach((o,i)=>{
    const y = 3.95 + i*0.95;
    s.addShape(pres.ShapeType.rect,{x:0.55,y:y,w:12.2,h:0.82,fill:{color:WHITE},line:{color:LINE,width:0.75}});
    s.addText(o[0],{x:0.75,y:y,w:2.3,h:0.82,fontFace:SANS,fontSize:14,bold:true,color:INK,margin:0,valign:'middle'});
    s.addText(o[1],{x:3.15,y:y,w:4.85,h:0.82,fontFace:SANS,fontSize:11.5,color:BODY,margin:0,valign:'middle'});
    s.addText(o[2],{x:8.15,y:y,w:4.4,h:0.82,fontFace:SANS,fontSize:11.5,color:BODY,margin:0,valign:'middle'});
  });
  s.addNotes("이름이 겹쳐 혼동되기 쉬운 부분이라 따로 정리했습니다.");
}

/* ── 11. 다섯 가지 항목 ────────────────────── */
{
  const s = slide(); kicker(s,"05. 헤어 요소로 옮겨 볼 때");
  title(s,[{text:"이미지를 시술 항목으로 옮길 때 ",options:{color:INK}},{text:"살펴보는 다섯 가지",options:{color:GOLD}}]);
  lead(s,"이미지를 나타내는 말은 그대로는 시술 지시가 되지 않기 때문에, 상담에서는 보통 아래 다섯 항목으로 나누어 확인합니다. 항목별로 정리해 두면 서로 떠올린 그림을 맞춰 보기 쉬워집니다.",2.35);
  const v=[
    ["길이","숏 · 보브 · 미디엄 · 세미롱 · 롱","전체 인상의 무게중심을 정하는 항목입니다."],
    ["질감","매끈함 · 자연스러움 · 거친 결","같은 길이라도 인상이 크게 달라지는 항목입니다."],
    ["컬","스트레이트 · 원컬 · 웨이브 · 끝 방향","안쪽·바깥쪽 방향까지 함께 확인합니다."],
    ["컬러","밝기 · 색조(웜/쿨) · 채도","A 스케일의 가로축과 직접 연결되는 항목입니다."],
    ["앞머리","없음 · 시스루 · 일자 · 흘림","얼굴 인상 변화가 가장 크게 나타나는 항목입니다."],
  ];
  v.forEach((c,i)=>{
    const x = 0.55 + i*2.47;
    s.addShape(pres.ShapeType.rect,{x:x,y:3.5,w:2.28,h:2.85,fill:{color:WHITE},line:{color:LINE,width:0.75}});
    s.addShape(pres.ShapeType.ellipse,{x:x+0.22,y:3.72,w:0.5,h:0.5,fill:{color:CREAM},line:{color:GOLD,width:1}});
    s.addText(String(i+1),{x:x+0.22,y:3.72,w:0.5,h:0.5,fontFace:SERIF,fontSize:13,bold:true,color:GOLD,align:'center',valign:'middle',margin:0});
    s.addText(c[0],{x:x+0.22,y:4.35,w:1.9,h:0.34,fontFace:SANS,fontSize:16,bold:true,color:INK,margin:0});
    s.addText(c[1],{x:x+0.22,y:4.75,w:1.9,h:0.72,fontFace:SANS,fontSize:10,color:GOLD,margin:0,lineSpacing:15});
    s.addText(c[2],{x:x+0.22,y:5.5,w:1.9,h:0.7,fontFace:SANS,fontSize:10,color:MUTE,margin:0,lineSpacing:15});
  });
  note(s,"참고","사진 자료를 함께 볼 때는 결과 이미지만 보는 대신 위 다섯 항목이 각각 어떻게 되어 있는지 함께 확인하면, 이야기한 내용을 서로 같은 그림으로 맞추기 쉬워집니다.",0.55,6.55,12.2,0.72);
  s.addNotes("다섯 항목은 상담 기록지의 칸과 동일하게 구성되어 있습니다.");
}

/* ── 12. 정리 예시 ─────────────────────────── */
{
  const s = slide(); kicker(s,"05. 헤어 요소로 옮겨 볼 때");
  title(s,[{text:"정리 ",options:{color:INK}},{text:"예시",options:{color:GOLD}}]);
  s.addText("실제 상담에서 나온 표현을 앞의 항목들로 옮겨 적어 본 예시입니다. 하나의 정답이 아니라 정리 방식의 예로 보시면 됩니다.",
    {x:0.55,y:2.12,w:12.2,h:0.32,fontFace:SANS,fontSize:11,color:GRAY,margin:0});
  const cs=[
    ["「청순한 느낌으로」","A · WARM–SOFT, CLEAR 부근","B · 큐트 (아이 × 곡선)",
     "세미롱 / 매끈한 질감 / 끝 안말음 원컬 / 베이지 / 시스루 앞머리",
     "같은 표현이라도 「어려 보이는 쪽」과 「정돈된 쪽」으로 나뉘는 경우가 있어, 어느 쪽에 가까운지 함께 확인해 두면 좋습니다."],
    ["「시크한 느낌으로」","A · COOL–HARD, GRAYISH 부근","B · 쿨 (어른 × 직선)",
     "세미~롱 / 매끈한 질감 / 스트레이트 / 그레이지 / 앞머리 없음",
     "끝부분에 아주 약한 곡선을 남기는 방식도 함께 소개됩니다. 인상이 차분해지는 정도를 조절할 때 참고하는 부분입니다."],
    ["「강한 느낌으로」","A · WARM–HARD, 다이나믹 부근","B · 큐트 (아이 × 곡선)",
     "단발 / 결이 살아있는 질감 / 끝 바깥 방향 / 어두운 애쉬 / 일자 앞머리",
     "표현하고 싶은 이미지와 얼굴 인상이 서로 멀리 놓이는 경우입니다. 이런 경우에는 관리 시간이나 생활 조건도 함께 확인하게 됩니다."],
  ];
  cs.forEach((c,i)=>{
    const x = 0.55 + i*4.1, w = 3.85;
    s.addShape(pres.ShapeType.rect,{x:x,y:2.6,w:w,h:4.3,fill:{color:WHITE},line:{color:LINE,width:0.75}});
    s.addText(c[0],{x:x+0.22,y:2.82,w:w-0.44,h:0.36,fontFace:SANS,fontSize:14.5,bold:true,color:INK,margin:0});
    s.addText(c[1],{x:x+0.22,y:3.28,w:w-0.44,h:0.28,fontFace:SANS,fontSize:10.5,color:BODY,margin:0,valign:'middle'});
    s.addText(c[2],{x:x+0.22,y:3.58,w:w-0.44,h:0.28,fontFace:SANS,fontSize:10.5,color:BODY,margin:0,valign:'middle'});
    s.addText("다섯 항목",{x:x+0.22,y:4.0,w:w-0.44,h:0.24,fontFace:SANS,fontSize:8.5,bold:true,color:GOLD,charSpacing:1.2,margin:0});
    s.addText(c[3],{x:x+0.22,y:4.26,w:w-0.44,h:0.85,fontFace:SANS,fontSize:10.5,color:BODY,margin:0,lineSpacing:16});
    s.addText("참고",{x:x+0.22,y:5.2,w:w-0.44,h:0.24,fontFace:SANS,fontSize:8.5,bold:true,color:GOLD,charSpacing:1.2,margin:0});
    s.addText(c[4],{x:x+0.22,y:5.46,w:w-0.44,h:1.25,fontFace:SANS,fontSize:10,color:MUTE,margin:0,lineSpacing:15});
  });
  s.addNotes("세 예시 모두 '이렇게 정리해 볼 수 있다'는 예시입니다. 실제로는 모발 상태와 생활 조건을 함께 확인합니다.");
}

/* ── 12-B. 참고 도판 (이미지가 준비된 경우에만) ── */
if(HAS_CASES){
  const s = slide(); kicker(s,"05. 헤어 요소로 옮겨 볼 때");
  title(s,[{text:"참고 ",options:{color:INK}},{text:"도판",options:{color:GOLD}}]);
  s.addText("앞 장의 세 예시를 그림으로 나타낸 것입니다. 길이·질감·컬·앞머리가 각각 어떻게 다른지 비교해 보실 수 있습니다.",
    {x:0.55,y:2.12,w:12.2,h:0.32,fontFace:SANS,fontSize:11,color:GRAY,margin:0});
  const cap=[
    ["「청순한 느낌으로」","세미롱 · 매끈함 · 끝 안말음 · 시스루 앞머리"],
    ["「시크한 느낌으로」","세미~롱 · 매끈함 · 스트레이트 · 앞머리 없음"],
    ["「강한 느낌으로」","단발 · 결이 살아있는 질감 · 끝 바깥 방향 · 일자 앞머리"],
  ];
  [1,2,3].forEach((n,i)=>{
    const x = 0.55 + i*4.1, w = 3.85;
    s.addShape(pres.ShapeType.rect,{x:x,y:2.6,w:w,h:4.3,fill:{color:WHITE},line:{color:LINE,width:0.75}});
    s.addImage({path:IMG(`nb_case${n}.png`),x:x+0.15,y:2.75,w:w-0.3,h:2.85});
    s.addText(cap[i][0],{x:x+0.25,y:5.75,w:w-0.5,h:0.34,fontFace:SANS,fontSize:14,bold:true,color:INK,margin:0});
    s.addText(cap[i][1],{x:x+0.25,y:6.15,w:w-0.5,h:0.62,fontFace:SANS,fontSize:10.5,color:MUTE,margin:0,lineSpacing:16});
  });
  s.addNotes("도판은 이해를 돕기 위한 예시 그림입니다. 실제 결과는 모발 상태에 따라 달라집니다.");
}

/* ── 13. 형용사 대조표 ─────────────────────── */
{
  const s = slide(); kicker(s,"부록");
  title(s,[{text:"상담에서 자주 나오는 ",options:{color:INK}},{text:"이미지 표현",options:{color:GOLD}}]);
  s.addText("손님이 쓰는 우리말 표현과, 두 체계에서 가까운 위치에 놓이는 이름을 나란히 정리했습니다.",
    {x:0.55,y:2.12,w:12.2,h:0.32,fontFace:SANS,fontSize:11,color:GRAY,margin:0});
  const head=["자주 쓰이는 표현","가까운 A 카테고리","축 방향","함께 언급되는 요소"];
  const body=[
    ["청순한 · 단정한","클리어 · 엘레강트","SOFT 쪽, 맑은 계열","매끈한 질감 · 밝은 베이지"],
    ["여성스러운 · 화사한","로맨틱 · 페미닌 계열","WARM–SOFT","웨이브 · 로즈 계열 컬러"],
    ["자연스러운 · 편안한","내추럴","중앙 부근","과하지 않은 층 · 중간 밝기"],
    ["시크한 · 세련된","시크 · 모던","COOL–HARD, 탁한 계열","스트레이트 · 그레이 계열"],
    ["도시적인 · 깔끔한","모던 · 포멀","COOL–HARD","블런트 라인 · 무채색"],
    ["개성 있는 · 강한","다이나믹 · 와일드","WARM–HARD","거친 결 · 어두운 톤"],
    ["귀여운 · 발랄한","프리티 · 캐주얼","WARM 쪽, 밝은 계열","짧은 길이 · 컬 앞머리"],
    ["고급스러운 · 우아한","엘레강트 · 고저스","중간~아래, 차분한 계열","큰 웨이브 · 브라운 계열"],
  ];
  const rows=[head.map(t=>({text:t,options:{bold:true,color:GOLD,fontSize:9.5,charSpacing:1.3}}))]
    .concat(body.map(r=>r.map((t,i)=>({text:t,options:{bold:i===0,color:i===0?INK:BODY,fontSize:11}}))));
  s.addTable(rows,{x:0.55,y:2.6,w:12.2,colW:[3.2,3.2,3.0,2.8],border:{type:'solid',color:LINE,pt:0.5},
    fontFace:SANS,rowH:0.45,valign:'middle',margin:0.08,fill:{color:CREAM}});
  s.addNotes("대응 관계는 참고용입니다. 같은 표현도 손님에 따라 다른 위치에 놓일 수 있습니다.");
}

/* ── 14. 정리 · 출처 ───────────────────────── */
{
  const s = slide(); kicker(s,"정리");
  title(s,[{text:"오늘 살펴본 ",options:{color:INK}},{text:"내용",options:{color:GOLD}}]);
  const sum=[
    ["언어 이미지 스케일 (A)","WARM↔COOL, SOFT↔HARD 두 축과 보조축 CLEAR↔GRAYISH 위에 16개 이미지 카테고리가 배치됩니다."],
    ["얼굴타입 분류 (B)","아이↔어른, 곡선↔직선 두 축 위에 8개 타입이 놓이며, 타입별로 자주 소개되는 실루엣이 정리되어 있습니다."],
    ["함께 볼 때","이름이 겹치는 용어가 있어 어느 체계의 이름인지 확인하면 혼동을 줄일 수 있습니다."],
    ["헤어 요소로 옮길 때","길이 · 질감 · 컬 · 컬러 · 앞머리 다섯 항목으로 나누어 정리하는 방식이 함께 소개됩니다."],
  ];
  sum.forEach((c,i)=>{
    const y = 2.4 + i*1.0;
    s.addShape(pres.ShapeType.ellipse,{x:0.55,y:y+0.08,w:0.42,h:0.42,fill:{color:CREAM},line:{color:GOLD,width:1}});
    s.addText(String(i+1),{x:0.55,y:y+0.08,w:0.42,h:0.42,fontFace:SERIF,fontSize:12,bold:true,color:GOLD,align:'center',valign:'middle',margin:0});
    s.addText(c[0],{x:1.2,y:y,w:3.6,h:0.32,fontFace:SANS,fontSize:14,bold:true,color:INK,margin:0,valign:'middle'});
    s.addText(c[1],{x:4.9,y:y,w:7.85,h:0.62,fontFace:SANS,fontSize:11.5,color:BODY,margin:0,lineSpacing:19,valign:'top'});
  });
  s.addShape(pres.ShapeType.rect,{x:0.55,y:6.4,w:12.2,h:0.72,fill:{color:WHITE},line:{color:LINE,width:0.75}});
  s.addText([
    {text:"참고 자료   ",options:{bold:true,color:GOLD,fontSize:9.5,charSpacing:1.3}},
    {text:"日本カラーデザイン研究所 「イメージスケール」 · 岩手県立大学 감성공학 강의자료 · 顔タイプ診断® 관련 일본 미용 자료",options:{fontSize:10.5,color:MUTE}},
  ],{x:0.75,y:6.4,w:11.8,h:0.72,fontFace:SANS,margin:0,valign:'middle'});
  s.addNotes("자료의 출처를 함께 안내합니다. 더 자세한 내용은 각 원자료에서 확인할 수 있습니다.");
}

pres.writeFile({fileName: path.join(__dirname,'L5_일본_이미지분류체계.pptx')})
  .then(f=>console.log("WROTE",f));
