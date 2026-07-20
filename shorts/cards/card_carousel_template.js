const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const HANDLE = '@ATNOWN_Chano';

// 콘텐츠 데이터
const shapes = [
  {
    emoji: '⭕', name: '둥근 얼굴',
    recs: ['세로 흐름의 레이어드', '사이드 파트로 옆선 살리기', '이마 여는 시스루 뱅'],
    tips: ['볼륨은 정수리에, 옆은 붙인다', '피할 것 — 일자 단발·옆 볼륨'],
  },
  {
    emoji: '📏', name: '긴 얼굴',
    recs: ['가로 볼륨 단발·미디엄', '이마 덮는 자연 앞머리', '끝단 C컬로 무게 주기'],
    tips: ['정수리는 낮추고 옆을 채운다', '피할 것 — 긴 생머리·센터 가르마'],
  },
  {
    emoji: '🔲', name: '각진 얼굴',
    recs: ['부드러운 레이어드 웨이브', '턱선 감싸는 얼굴 옆 컬', '사선 앞머리로 각 완화'],
    tips: ['직선보다 곡선, 끝은 안으로', '피할 것 — 일자 뱅·딱 떨어지는 단발'],
  },
  {
    emoji: '🔻', name: '역삼각 얼굴',
    recs: ['턱선 아래 볼륨 있는 컷', '안으로 말리는 C컬 보브', '이마 볼륨 줄이는 뱅'],
    tips: ['무게중심을 아래로 내린다', '피할 것 — 짧은 픽시·정수리 과볼륨'],
  },
];

function footer(n) {
  return `
    <div class="footer">
      <div class="handle">${HANDLE}</div>
      <div class="fr">
        <span class="pageno">${n}페이지</span>
        <span class="nextbtn">❯</span>
      </div>
    </div>`;
}

const bgLayers = (n) =>
  `<div class="bg" style="background-image:url('bg${n}.jpg')"></div><div class="grain"></div><div class="veil"></div>`;

// 표지 1p
let slides = [];
slides.push(`
  <section class="slide">
    ${bgLayers(1)}
    <div class="content cover">
      <div class="kicker">Chano's Hair Formula&nbsp;&nbsp;NO.4</div>
      <h1 class="title"><span class="em">💇</span> 얼굴형별<br>커트 지도</h1>
      <div class="redef">커트는 길이가 아니라<br><span class="hl">얼굴형</span>이 정합니다.</div>
      <div class="save"><span class="em">👉</span> 저장해두면 편해요.</div>
    </div>
    ${footer(1)}
  </section>`);

// 내용 2~5p
shapes.forEach((s, i) => {
  const recLines = s.recs.map(r =>
    `<div class="rec"><span class="lab">추천</span><span class="em point">👉</span><span class="rtext">${r}</span></div>`).join('');
  const tipLines = s.tips.map(t =>
    `<div class="tip"><span class="chk">✓</span><span class="ttext">${t}</span></div>`).join('');
  slides.push(`
  <section class="slide">
    ${bgLayers(i + 2)}
    <div class="content mid">
      <div class="ctitle"><span class="em">${s.emoji}</span> ${s.name}</div>
      <div class="recs">${recLines}</div>
      <div class="tips">${tipLines}</div>
    </div>
    ${footer(i + 2)}
  </section>`);
});

// 6p 내생각
slides.push(`
  <section class="slide">
    ${bgLayers(6)}
    <div class="content think">
      <div class="tk-lead">차노 한마디</div>
      <h2 class="tk-quote">얼굴형은<br>못 바꿔도,<br><span class="hl">시선의 방향</span>은<br>바꿉니다.</h2>
      <div class="tk-handle">${HANDLE} · AT NOWN</div>
    </div>
    ${footer(6)}
  </section>`);

const grainSVG = "data:image/svg+xml;utf8," + encodeURIComponent(
  `<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix type='saturate' values='0'/></filter><rect width='100%' height='100%' filter='url(#n)' opacity='1'/></svg>`);

const html = `<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{font-family:"NanumSquareRound","Pretendard","Apple SD Gothic Neo",sans-serif,"Noto Color Emoji";-webkit-font-smoothing:antialiased}
  .slide{width:1080px;height:1350px;position:relative;overflow:hidden;background:#171514;color:#fff}
  .bg{position:absolute;inset:0;background-color:#16130f;
    background-size:cover;background-position:center;background-repeat:no-repeat;}
  .grain{position:absolute;inset:0;background-image:url("${grainSVG}");
    background-size:300px 300px;opacity:.06;mix-blend-mode:soft-light;pointer-events:none;}
  .veil{position:absolute;inset:0;pointer-events:none;
    background:
      linear-gradient(180deg, rgba(0,0,0,.74) 0%, rgba(0,0,0,.34) 18%,
        rgba(0,0,0,.36) 50%, rgba(0,0,0,.62) 80%, rgba(0,0,0,.88) 100%),
      linear-gradient(90deg, rgba(0,0,0,.66) 0%, rgba(0,0,0,.40) 45%, rgba(0,0,0,.12) 78%, rgba(0,0,0,0) 100%);}
  .content{position:absolute;inset:0;padding:118px 96px 96px;display:flex;flex-direction:column;
    text-shadow:0 2px 10px rgba(0,0,0,.55), 0 1px 2px rgba(0,0,0,.5);}
  .em{font-family:"Noto Color Emoji";font-weight:normal;}

  /* 표지 */
  .cover{justify-content:flex-start;}
  .kicker{font-size:25px;letter-spacing:.14em;color:#9b938a;font-weight:600;
    text-transform:uppercase;margin-bottom:150px;}
  .title{font-size:92px;font-weight:800;line-height:1.14;letter-spacing:-.02em;}
  .title .em{font-size:80px;}
  .redef{margin-top:52px;font-size:47px;font-weight:600;line-height:1.42;color:#e9e4dc;}
  .redef .hl{color:#F2C230;}
  .save{margin-top:40px;font-size:32px;font-weight:600;color:#d9d2c8;}
  .save .em{font-size:34px;vertical-align:-4px;}

  /* 내용 */
  .mid{justify-content:center;padding-bottom:170px;}
  .ctitle{font-size:62px;font-weight:800;letter-spacing:-.01em;margin-bottom:58px;}
  .ctitle .em{font-size:56px;vertical-align:-2px;margin-right:8px;}
  .recs{display:flex;flex-direction:column;gap:30px;}
  .rec{display:flex;align-items:baseline;gap:20px;font-size:41px;font-weight:600;line-height:1.26;color:#f6f2ea;}
  .rec .lab{color:#a89f95;font-weight:600;flex:none;}
  .rec .em{font-size:38px;flex:none;align-self:center;}
  .rec .rtext{flex:1;}
  .tips{margin-top:66px;display:flex;flex-direction:column;gap:20px;
    border-top:1px solid rgba(255,255,255,.14);padding-top:44px;}
  .tip{display:flex;align-items:baseline;gap:14px;font-size:30px;font-weight:500;line-height:1.34;color:#cdc6bb;}
  .tip .chk{color:#F2C230;font-weight:700;flex:none;}
  .tip .ttext{flex:1;}

  /* 내생각 */
  .think{justify-content:center;}
  .tk-lead{font-size:27px;letter-spacing:.12em;color:#a89f95;font-weight:600;margin-bottom:38px;text-transform:uppercase;}
  .tk-quote{font-size:78px;font-weight:800;line-height:1.24;letter-spacing:-.02em;}
  .tk-quote .hl{color:#F2C230;}
  .tk-handle{margin-top:56px;font-size:29px;color:#cfc8bf;font-weight:600;}

  /* 푸터 */
  .footer{position:absolute;left:96px;right:96px;bottom:74px;
    display:flex;align-items:center;justify-content:space-between;
    text-shadow:0 2px 8px rgba(0,0,0,.6);}
  .handle{font-size:27px;color:#d3ccc2;font-weight:700;letter-spacing:.01em;}
  .fr{display:flex;align-items:center;gap:26px;}
  .pageno{font-size:25px;color:#9b938a;font-weight:500;}
  .nextbtn{width:62px;height:62px;border:1.5px solid rgba(255,255,255,.55);
    border-radius:50%;display:flex;align-items:center;justify-content:center;
    font-size:26px;color:#fff;padding-left:4px;}
</style></head><body>${slides.join('')}</body></html>`;

const outHtml = path.join(__dirname, 'index.html');
fs.writeFileSync(outHtml, html);

(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 1 });
  await page.goto('file://' + outHtml, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(500);
  const els = await page.$$('.slide');
  for (let i = 0; i < els.length; i++) {
    const n = String(i + 1).padStart(2, '0');
    await els[i].screenshot({ path: path.join(__dirname, `ATNOWN_얼굴형_${n}.png`) });
  }
  await browser.close();
  console.log('rendered', els.length, 'slides');
})();
