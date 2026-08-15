// 네이버 블로그 임시저장 — 형 실측 서식판. 한 주제 = 임시저장 1건.
// 같은 제목이 이미 있으면 그걸 열어 본문만 갈아끼운다(새 글 안 만듦). 삭제는 ALLOW_DELETE=1 일 때만.
// 발행 버튼은 절대 클릭하지 않는다.
import { chromium } from 'playwright';
import { mkdirSync, readFileSync, writeFileSync, existsSync, unlinkSync, readdirSync, statSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const PROFILE = join(ROOT, '_naver_profile');
const STATE = join(ROOT, 'secrets/naver_state.json');
const RESULT = join(ROOT, '_cowork_sync/briefings/블로그_임시저장_결과.txt');
const REPORT = join(ROOT, '_cowork_sync/briefings/블로그_서식적용_리포트.json');
const BLOG = process.env.BLOG_ID || 'chanlolo2';
const FONT = process.env.BLOG_FONT || '나눔스퀘어';
const SZ_BODY = '19', SZ_HEAD = '24', SZ_SMALL = '16';
const ALLOW_DELETE = process.env.ALLOW_DELETE === '1';
const JOB_NAME = process.env.JOB || '';

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const log = (...a) => console.log(new Date().toISOString(), '-', ...a);
const MOD = process.platform === 'darwin' ? 'Meta' : 'Control';

function loadJob() {
  const dir = join(ROOT, '_publish_jobs/blog_parsed');
  let picked = null;
  const jobs = [];
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    if (!e.isDirectory() || e.name.startsWith('_')) continue;
    if (existsSync(join(dir, e.name, 'blocks.json'))) jobs.push(e.name);
  }
  if (!jobs.length) throw new Error('blog_parsed에 잡이 없습니다.');
  picked = JOB_NAME && jobs.includes(JOB_NAME) ? JOB_NAME : jobs.sort()[jobs.length - 1];
  const d = join(dir, picked);
  const meta = JSON.parse(readFileSync(join(d, 'meta.json'), 'utf8'));
  return { name: picked, title: readFileSync(join(d, 'title.txt'), 'utf8').trim(),
           blocks: JSON.parse(readFileSync(join(d, 'blocks.json'), 'utf8')),
           color: (meta.color || '').replace('#', '').toLowerCase() };
}
const JOB = loadJob();

mkdirSync(PROFILE, { recursive: true });
mkdirSync(dirname(RESULT), { recursive: true });
const LOCK = join(PROFILE, '.run.lock');
if (existsSync(LOCK)) {
  const pid = parseInt(readFileSync(LOCK, 'utf8').trim(), 10);
  let alive = false; try { process.kill(pid, 0); alive = true; } catch {}
  // 10분 넘게 잡고 있는 락은 좀비로 보고 강제로 뺏는다 (오늘 5분+ 멈춤 사고)
  let stale = false;
  try { stale = (Date.now() - statSync(LOCK).mtimeMs) > 10 * 60 * 1000; } catch {}
  if (alive && !stale) { console.error(`이미 실행 중 (PID ${pid})`); process.exit(0); }
  if (alive && stale) {
    console.error(`좀비 감지 (PID ${pid}, 10분 초과) — 종료하고 진행합니다`);
    try { process.kill(pid, 'SIGKILL'); } catch {}
    const until = Date.now() + 2000; while (Date.now() < until) {}
  }
  try { unlinkSync(LOCK); } catch {}
}
writeFileSync(LOCK, String(process.pid), 'utf8');
const rel = () => { try { unlinkSync(LOCK); } catch {} };
process.on('exit', rel);

let CTX = null, SHUT = false;
const RP = { job: JOB.name, title: JOB.title, color: JOB.color, mode: '', existing: 0, deleted: 0, applied: {}, skipped: [], error: null };
const rep = () => writeFileSync(REPORT, JSON.stringify(RP, null, 2), 'utf8');
const res = (s, u, b = '', x = '') => writeFileSync(RESULT, `상태: ${s}\n임시글URL: ${u || ''}\n막힌지점: ${b || ''}\n서식: ${x}\n`, 'utf8');
async function saveState() {
  try {
    if (!CTX) return;
    const prev = existsSync(STATE) ? JSON.parse(readFileSync(STATE, 'utf8')) : {};
    const next = await CTX.storageState();
    if (Array.isArray(prev.published_titles)) next.published_titles = prev.published_titles;
    writeFileSync(STATE, JSON.stringify(next, null, 2), 'utf8');
  } catch {}
}
async function bye(c) { if (SHUT) return; SHUT = true; await saveState(); rep(); try { if (CTX) await CTX.close(); } catch {} rel(); process.exit(c); }
process.on('SIGINT', () => bye(0)); process.on('SIGTERM', () => bye(0));
const vis = async (l, t = 1000) => { try { return await l.isVisible({ timeout: t }); } catch { return false; } };

async function closePopups(page) {
  for (let i = 0; i < 14; i += 1) {
    let hit = false;
    for (const sc of [page, ...page.frames()]) {
      for (const sel of ['[class*="layer_popup"] button:has-text("취소")', '[class*="layer_popup"] button:has-text("새로 작성")',
                         '[class*="layer_popup"] [class*="cancel"]', 'button.se-popup-button-cancel', 'button:has-text("취소")']) {
        const l = sc.locator(sel).first();
        if (await l.isVisible({ timeout: 150 }).catch(() => false)) { await l.click({ timeout: 3000, force: true }).catch(()=>{}); hit = true; await sleep(600); }
      }
    }
    for (const sc of [page, ...page.frames()]) {
      const d = sc.locator('[class*="dimmed"]').first();
      if (await d.isVisible({ timeout: 120 }).catch(() => false)) { await page.keyboard.press('Escape').catch(()=>{}); await sleep(400); hit = true; }
    }
    if (!hit && i > 3) break;
    await sleep(200);
  }
}
async function noDim(ed, page, ms = 9000) {
  const dl = Date.now() + ms;
  while (Date.now() < dl) {
    const d = ed.locator('[class*="dimmed"]').first();
    if (!(await d.isVisible({ timeout: 200 }).catch(() => false))) return true;
    await closePopups(page); await sleep(400);
  }
  return false;
}
async function pick(ed, page, toggle, wants, label) {
  try {
    if (!(await vis(toggle, 1500))) { RP.skipped.push(`${label}: 토글없음`); return false; }
    await toggle.click({ timeout: 6000 }); await sleep(650);
    for (const w of wants) {
      for (const c of [ed.locator(`button:text-is("${w}")`).first(), ed.locator(`li:text-is("${w}")`).first(),
                       ed.locator(`button[aria-label="${w}"]`).first(), ed.locator(`button:has-text("${w}")`).first()]) {
        if (await vis(c, 400)) { await c.click({ timeout: 4000 }).catch(()=>{}); await sleep(450); return true; }
      }
    }
    await page.keyboard.press('Escape').catch(()=>{}); await sleep(250);
    RP.skipped.push(`${label}: 옵션없음`); return false;
  } catch (e) { RP.skipped.push(`${label}: ${(e?.message||'').slice(0,50)}`); return false; }
}
const setFont = (e,p)=>pick(e,p,e.locator('button.se-font-family-toolbar-button').first(),[FONT,'나눔스퀘어OTF'],'서체');
const setSize = (e,p,s)=>pick(e,p,e.locator('button.se-font-size-code-toolbar-button').first(),[s],`크기${s}`);
const setCenter = (e,p)=>pick(e,p,e.locator('button.se-align-left-toolbar-button, button[data-name="align-drop-down-with-justify"]').first(),['가운데 정렬','가운데정렬','가운데'],'가운데정렬');
async function setColor(ed, page, hex, label) {
  try {
    const t = ed.locator('button.se-font-color-toolbar-button').first();
    if (!(await vis(t, 1200))) { RP.skipped.push(`${label}: 색버튼없음`); return false; }
    await t.click({ timeout: 6000 }); await sleep(750);
    const inp = ed.locator('input[type="text"]').first();
    if (await vis(inp, 600)) { await inp.fill('').catch(()=>{}); await inp.type(hex, { delay: 20 }).catch(()=>{}); await page.keyboard.press('Enter'); await sleep(550); return true; }
    for (const sel of [`[data-value="#${hex}"]`, `[data-value="${hex}"]`, `button[title*="${hex}" i]`, `[style*="#${hex}" i]`]) {
      const c = ed.locator(sel).first();
      if (await vis(c, 400)) { await c.click({ timeout: 4000 }).catch(()=>{}); await sleep(450); return true; }
    }
    await page.keyboard.press('Escape').catch(()=>{}); await sleep(250);
    RP.skipped.push(`${label}: 색${hex} 못찾음`); return false;
  } catch (e) { RP.skipped.push(`${label}: ${(e?.message||'').slice(0,50)}`); return false; }
}
const bold = async (ed) => { const b = ed.locator('button.se-bold-toolbar-button').first(); if (await vis(b, 800)) { await b.click({timeout:4000}).catch(()=>{}); await sleep(220); return true; } return false; };

// 예약발행 글 중복 체크 (2026-08-16 차노 지시: 임시저장뿐 아니라 예약발행도 체크)
async function checkReserved(page) {
  try {
    // 글 관리 페이지에서 예약발행 글 확인
    await page.goto(`https://blog.naver.com/PostList.naver?blogId=${BLOG}&categoryNo=0&from=postList`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await sleep(2000);
    // 예약발행 탭 클릭 (있으면)
    const reserveTab = page.locator('a:has-text("예약발행"), button:has-text("예약")').first();
    if (await vis(reserveTab, 2000)) {
      await reserveTab.click({ timeout: 5000 }).catch(()=>{});
      await sleep(2000);
    }
    // 같은 제목의 글 찾기
    const titles = await page.locator('.post-title, .title, [class*="title"]').allInnerTexts().catch(() => []);
    const found = titles.filter(t => t.includes(JOB.title));
    if (found.length > 0) {
      log('⚠️ 예약발행 중복 발견:', found.length, '건');
      RP.skipped.push(`예약발행 중복 ${found.length}건: ${JOB.title}`);
      return found.length;
    }
    return 0;
  } catch (e) {
    RP.skipped.push(`예약체크실패: ${(e?.message||'').slice(0,30)}`);
    return 0;
  }
}

async function reuse(ed, page) {
  const op = ed.locator('button[class*="save_count"]').first();
  if (!(await vis(op, 1500))) { RP.skipped.push('목록버튼 없음'); return 'new'; }
  if (!(await noDim(ed, page))) { RP.skipped.push('복구팝업 안닫힘'); return 'new'; }
  await op.click({ timeout: 8000 }).catch((e)=>RP.skipped.push('목록열기실패'));
  await sleep(1700);
  const rows = () => ed.locator('li[class*="item__"]').filter({ hasText: JOB.title });
  RP.existing = await rows().count().catch(() => 0);
  log('같은 제목', RP.existing, '건');
  if (!RP.existing) { await page.keyboard.press('Escape').catch(()=>{}); await sleep(600); return 'new'; }
  if (!ALLOW_DELETE && RP.existing > 1) RP.skipped.push(`중복 ${RP.existing}건 — 형 승인 없어 삭제 안 함`);
  for (let k = 0; ALLOW_DELETE && k < 6; k += 1) {
    const cur = rows(); const n = await cur.count().catch(() => 0);
    if (n <= 1) break;
    const row = cur.nth(n - 1);
    await row.hover({ timeout: 3000 }).catch(()=>{}); await sleep(400);
    const del = row.locator('[class*="delete_button__"], button[class*="delete"]').first();
    if (!(await vis(del, 1200))) { RP.skipped.push('휴지통 못찾음'); break; }
    await del.click({ timeout: 5000, force: true }).catch(()=>{}); await sleep(800);
    for (const sc of [page, ...page.frames()]) {
      const ok = sc.locator('[class*="layer_popup"] button:has-text("확인"), button.se-popup-button-confirm, button:has-text("확인")').first();
      if (await ok.isVisible({ timeout: 800 }).catch(() => false)) { await ok.click({ timeout: 4000, force: true }).catch(()=>{}); break; }
    }
    await sleep(1300); RP.deleted += 1;
  }
  const open = rows().first().locator('[class*="article_button__"]').first();
  if (await vis(open, 1500)) { await open.click({ timeout: 6000, force: true }).catch(()=>{}); await sleep(3500); await closePopups(page); return 'opened'; }
  RP.skipped.push('열기버튼 없음');
  await page.keyboard.press('Escape').catch(()=>{}); await sleep(600);
  return 'new';
}

(async () => {
  try {
    res('진행중', '', 'Chrome 실행');
    CTX = await chromium.launchPersistentContext(PROFILE, {
      channel: 'chrome', headless: false, viewport: { width: 1440, height: 900 },
      locale: 'ko-KR', timezoneId: 'Asia/Seoul', args: ['--disable-blink-features=AutomationControlled'],
    });
    if (existsSync(STATE)) { try { const st = JSON.parse(readFileSync(STATE, 'utf8')); if (st?.cookies?.length) await CTX.addCookies(st.cookies); } catch {} }
    const page = CTX.pages()[0] || await CTX.newPage();
    await page.goto('https://blog.naver.com/MyBlog.naver', { waitUntil: 'domcontentloaded', timeout: 60000 });
    if (page.url().includes('nid.naver.com')) {
      // 로그인 화면이면 사람이 로그인할 때까지 기다린다. 계정 정보는 스크립트가 입력하지 않는다.
      const WAIT = Number(process.env.LOGIN_WAIT || 600);
      res('대기', page.url(), '네이버 로그인 대기 중 — 열린 창에서 로그인해 주세요');
      console.log('\n>>> 열린 크롬 창에서 네이버 로그인만 해주세요. 되면 자동으로 이어서 글을 넣습니다.\n');
      let ok = false;
      for (let w = 0; w < WAIT; w += 3) {
        await sleep(3000);
        if (!page.url().includes('nid.naver.com')) { ok = true; break; }
      }
      if (!ok) throw new Error('로그인 대기 시간 초과');
      await sleep(2500);
      console.log('>>> 로그인 확인. 이어서 진행합니다.\n');
    }
    await saveState();

    // 예약발행 중복 체크 (2026-08-16 차노 지시)
    res('진행중', '', '예약발행 중복 체크');
    const reservedCount = await checkReserved(page);
    if (reservedCount > 0 && !process.env.FORCE_WRITE) {
      log('⛔ 예약발행 중복 — 중단 (FORCE_WRITE=1 로 강제 진행 가능)');
      res('중단', '', `예약발행 중복 ${reservedCount}건`);
      RP.error = `예약발행 중복 ${reservedCount}건`;
      await bye(1);
    }

    await page.goto(`https://blog.naver.com/${BLOG}?Redirect=Write&`, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await sleep(3500); await closePopups(page);
    let ed = null;
    for (const sc of [page, ...page.frames()]) {
      if (await sc.locator('[contenteditable="true"]').first().isVisible({ timeout: 600 }).catch(() => false)) { ed = sc; break; }
    }
    if (!ed) throw new Error('에디터 못 찾음');
    await noDim(ed, page, 10000);

    res('진행중', page.url(), '기존 임시저장 확인');
    RP.mode = await reuse(ed, page);
    log('모드', RP.mode, '기존', RP.existing, '삭제', RP.deleted);
    await noDim(ed, page, 6000);

    // 본문 = 제목(se-documentTitle) 바깥의 텍스트 컴포넌트만. contenteditable 폴백 금지(제목이 잡힌다).
    const BODY_SEL = '.se-component.se-text:not(.se-documentTitle) .se-text-paragraph, .se-section-text:not(.se-section-documentTitle) .se-text-paragraph';
    const TITLE_SEL = '.se-documentTitle .se-text-paragraph, .se-section-documentTitle .se-text-paragraph, .se-title-text';
    let bodyFirst = ed.locator(BODY_SEL).last();
    if (!(await vis(bodyFirst, 3000))) {
      const add = ed.locator('button.se-canvas-bottom-button, button:has-text("본문")').first();
      if (await vis(add, 1500)) { await add.click({ timeout: 5000 }).catch(()=>{}); await sleep(900); }
      bodyFirst = ed.locator(BODY_SEL).last();
    }
    await bodyFirst.scrollIntoViewIfNeeded().catch(()=>{});
    await bodyFirst.click({ force: true, timeout: 8000 }).catch(()=>{}); await sleep(500);
    if (RP.mode === 'opened') {
      res('진행중', page.url(), '기존 본문 비우기');
      await page.keyboard.press(`${MOD}+A`); await sleep(500);
      await page.keyboard.press('Delete'); await sleep(900);
    }

    res('진행중', page.url(), '제목');
    const tl = ed.locator(TITLE_SEL).first();
    if (!(await vis(tl, 3000))) throw new Error('제목칸을 찾지 못했습니다');
    const cur = (await tl.innerText().catch(() => '')).trim();
    if (!cur || cur === '제목') { await tl.click(); await page.keyboard.type(JOB.title, { delay: 8 }); await sleep(400); }
    let tcheck = (await tl.innerText().catch(() => '')).trim();
    if (tcheck && tcheck !== '제목' && tcheck !== JOB.title) {
      RP.skipped.push(`제목 정정: "${tcheck.slice(0,30)}"`);
      await tl.click(); await page.keyboard.press(`${MOD}+A`); await sleep(200);
      await page.keyboard.press('Delete'); await sleep(300);
      await page.keyboard.type(JOB.title, { delay: 8 }); await sleep(400);
    }
    RP.applied.title = (await tl.innerText().catch(() => '')).trim();

    res('진행중', page.url(), '본문 입력');
    const bl = ed.locator(BODY_SEL).last();
    if (!(await vis(bl, 3000))) throw new Error('본문칸을 찾지 못했습니다 — 제목칸에 쓰지 않기 위해 중단');
    await bl.scrollIntoViewIfNeeded().catch(()=>{});
    await bl.click({ force: true, timeout: 8000 }).catch(()=>{}); await sleep(400);
    const paras = JOB.blocks.filter(b => b.type !== 'image').map(b => ({ type: b.type, lines: (b.text || '').trim().split('\n') })).filter(p => p.lines.join(''));
    for (let i = 0; i < paras.length; i += 1) {
      const p = paras[i];
      for (let j = 0; j < p.lines.length; j += 1) {
        await page.keyboard.type(p.lines[j], { delay: 2 });
        if (j < p.lines.length - 1) { await page.keyboard.down('Shift'); await page.keyboard.press('Enter'); await page.keyboard.up('Shift'); }
      }
      if (i < paras.length - 1) { await page.keyboard.press('Enter'); await page.keyboard.press('Enter'); }
    }
    await sleep(1000);

    // ① 글부터 저장한다. 서식이 실패해도 글은 남는다.
    async function doSave(tag) {
      const sv = ed.locator('button[class*="save_btn__"], button:has-text("저장")').first();
      if (!(await vis(sv, 3000))) { RP.skipped.push(`${tag}: 저장버튼 없음`); return false; }
      const st = (await sv.innerText().catch(() => '')).trim();
      if (st.includes('발행') || st.includes('공개')) { RP.skipped.push(`${tag}: 발행버튼으로 보임 — 중단`); return false; }
      await sv.click({ timeout: 8000 }).catch(()=>{}); await sleep(2500);
      log('저장', tag); return true;
    }
    res('진행중', page.url(), '1차 저장(글만)');
    RP.applied.savedText = await doSave('1차');

    res('진행중', page.url(), '전체 서식');
    await page.keyboard.press(`${MOD}+A`); await sleep(600);
    RP.applied.font = await setFont(ed, page);
    RP.applied.body19 = await setSize(ed, page, SZ_BODY);
    RP.applied.center = await setCenter(ed, page);
    await sleep(400);

    // ② 전체 서식 후 한 번 더 저장
    RP.applied.savedGlobal = await doSave('2차');

    res('진행중', page.url(), '블록별 서식');
    const DEADLINE = Date.now() + Number(process.env.FORMAT_BUDGET || 180) * 1000;
    const P = ed.locator(BODY_SEL);
    RP.applied.paragraphs = await P.count().catch(() => 0);
    let h=0,c=0,s=0,bo=0,pt=0;
    for (const p of paras) {
      if (!['heading','center','small','bold','point'].includes(p.type)) continue;
      if (Date.now() > DEADLINE) { RP.skipped.push('서식 시간초과 — 남은 블록 건너뜀'); break; }
      const key = p.lines[0].slice(0, 18);
      const tgt = P.filter({ hasText: key }).first();
      if (!(await vis(tgt, 800))) { RP.skipped.push(`문단못찾음: ${key}`); continue; }
      await tgt.click({ clickCount: 3 }).catch(()=>{}); await sleep(330);
      if (p.type === 'point') {
        // 진짜 강조 — 여기만 포인트색을 쓴다 (차노: "핑크는 진짜 강조할 때만")
        await setSize(ed, page, SZ_HEAD);
        if (JOB.color) await setColor(ed, page, JOB.color, 'point');
        await bold(ed); pt++;
      } else if (p.type === 'heading' || p.type === 'center') {
        // 소제목·선언 = 24px + 검은 굵게. 색 안 쓴다
        await setSize(ed, page, SZ_HEAD);
        await bold(ed);
        if (p.type === 'heading') h++; else c++;
      } else if (p.type === 'small') { await setSize(ed, page, SZ_SMALL); s++; }
      else { await bold(ed); bo++; }
      await sleep(280);
    }
    RP.applied.heading=h; RP.applied.center_n=c; RP.applied.small=s; RP.applied.bold=bo; RP.applied.point=pt;

    res('진행중', page.url(), '임시저장');
    const tfinal = (await ed.locator(TITLE_SEL).first().innerText().catch(() => '')).trim();
    if (tfinal !== JOB.title) {
      RP.skipped.push(`저장전 제목 불일치: "${tfinal.slice(0,40)}" → 재설정`);
      const t2 = ed.locator(TITLE_SEL).first();
      await t2.click(); await page.keyboard.press(`${MOD}+A`); await sleep(200);
      await page.keyboard.press('Delete'); await sleep(300);
      await page.keyboard.type(JOB.title, { delay: 8 }); await sleep(500);
    }
    RP.applied.titleFinal = (await ed.locator(TITLE_SEL).first().innerText().catch(() => '')).trim();

    res('진행중', page.url(), '최종 저장');
    RP.applied.savedFinal = await doSave('최종');

    await saveState(); rep();
    const sum = `모드:${RP.mode} 기존:${RP.existing} 삭제:${RP.deleted} | 서체:${RP.applied.font?'O':'X'} 19:${RP.applied.body19?'O':'X'} 가운데:${RP.applied.center?'O':'X'} 소제목:${h} 선언:${c} 검은굵게:${bo} 포인트색:${pt} 작은글씨:${s}`;
    res('성공', page.url(), '', sum);
    log('완료', sum);
  } catch (e) {
    RP.error = e?.message || String(e);
    await saveState(); rep();
    res('막힘', '', RP.error, JSON.stringify(RP.applied));
    log('막힘', RP.error);
    process.exitCode = 1;
  } finally {
    try { if (CTX && !SHUT) await CTX.close(); } catch {}
    rel();
  }
})();
