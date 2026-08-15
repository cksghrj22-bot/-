// 네이버 로그인 1회 — 세션만 저장한다. 글 안 쓰고 발행 버튼 없다.
import { chromium } from 'playwright';
import { mkdirSync, existsSync, readFileSync, writeFileSync, unlinkSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const PROFILE = join(ROOT, '_naver_profile');
const STATE = join(ROOT, 'secrets/naver_state.json');
const LOCK = join(PROFILE, '.run.lock');
const WAIT = Number(process.env.WAIT || 900);
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const log = (...a) => console.log(new Date().toISOString(), '-', ...a);
mkdirSync(PROFILE, { recursive: true }); mkdirSync(join(ROOT, 'secrets'), { recursive: true });
if (existsSync(LOCK)) {
  const pid = parseInt(readFileSync(LOCK, 'utf8').trim(), 10);
  let alive = false; try { process.kill(pid, 0); alive = true; } catch {}
  if (alive) { console.error(`이미 실행 중 (PID ${pid})`); process.exit(0); }
  try { unlinkSync(LOCK); } catch {}
}
writeFileSync(LOCK, String(process.pid), 'utf8');
const rel = () => { try { unlinkSync(LOCK); } catch {} };
process.on('exit', rel);
let CTX = null, DONE = false;
async function save(reason) {
  if (!CTX) return false;
  try {
    const prev = existsSync(STATE) ? JSON.parse(readFileSync(STATE, 'utf8')) : {};
    const next = await CTX.storageState();
    if (Array.isArray(prev.published_titles)) next.published_titles = prev.published_titles;
    writeFileSync(STATE, JSON.stringify(next, null, 2), 'utf8');
    log('세션 저장', reason, `쿠키 ${next.cookies?.length ?? 0}개`);
    return true;
  } catch (e) { log('저장 실패', e?.message); return false; }
}
async function bye(c) { if (DONE) return; DONE = true; await save('exit'); try { if (CTX) await CTX.close(); } catch {} rel(); process.exit(c); }
process.on('SIGINT', () => bye(0)); process.on('SIGTERM', () => bye(0));
(async () => {
  CTX = await chromium.launchPersistentContext(PROFILE, {
    channel: 'chrome', headless: false, viewport: { width: 1440, height: 900 },
    locale: 'ko-KR', timezoneId: 'Asia/Seoul', args: ['--disable-blink-features=AutomationControlled'],
  });
  const page = CTX.pages()[0] || await CTX.newPage();
  await page.goto('https://blog.naver.com/MyBlog.naver', { waitUntil: 'domcontentloaded', timeout: 60000 });
  if (!page.url().includes('nid.naver.com')) {
    console.log('\n>>> 이미 로그인되어 있습니다. 세션만 저장하고 닫습니다.\n');
    await save('already'); await bye(0); return;
  }
  console.log('\n>>> 열린 크롬 창에서 네이버 로그인만 해주세요. 되면 자동으로 저장하고 닫힙니다.\n');
  for (let w = 0; w < WAIT; w += 3) {
    await sleep(3000);
    if (!page.url().includes('nid.naver.com')) {
      await sleep(2500);
      await save('login-done');
      console.log('\n>>> 저장 완료. 이제 임시저장이 로그인 없이 돕니다.\n');
      await bye(0); return;
    }
  }
  console.error('시간 초과. 다시 실행해 주세요.');
  await bye(1);
})();
