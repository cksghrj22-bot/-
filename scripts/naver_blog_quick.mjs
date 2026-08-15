// 기존 Chrome 프로필 사용 — 로그인 세션 유지
import { chromium } from 'playwright';
import { readFileSync, writeFileSync, existsSync, readdirSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const CHROME_PROFILE = '/Users/chanho/Library/Application Support/Google/Chrome';
const BLOG = 'chanlolo2';
const RESULT = join(ROOT, '_cowork_sync/briefings/블로그_임시저장_결과.txt');
const sleep = ms => new Promise(r => setTimeout(r, ms));

function loadJob() {
  const dir = join(ROOT, '_publish_jobs/blog_parsed');
  const jobs = readdirSync(dir, { withFileTypes: true })
    .filter(e => e.isDirectory() && !e.name.startsWith('_') && existsSync(join(dir, e.name, 'blocks.json')))
    .map(e => e.name);
  if (!jobs.length) throw new Error('잡 없음');
  const picked = jobs.sort().pop();
  const d = join(dir, picked);
  return {
    name: picked,
    title: readFileSync(join(d, 'title.txt'), 'utf8').trim(),
    blocks: JSON.parse(readFileSync(join(d, 'blocks.json'), 'utf8'))
  };
}

const JOB = loadJob();
console.log('잡:', JOB.name, '제목:', JOB.title);

(async () => {
  const browser = await chromium.launchPersistentContext(CHROME_PROFILE, {
    channel: 'chrome',
    headless: false,
    viewport: { width: 1440, height: 900 },
    args: ['--profile-directory=Default']
  });
  
  const page = browser.pages()[0] || await browser.newPage();
  
  console.log('블로그 에디터로 이동...');
  await page.goto(`https://blog.naver.com/${BLOG}?Redirect=Write&`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await sleep(3000);
  
  // 로그인 체크
  if (page.url().includes('nid.naver.com')) {
    console.log('로그인 필요 — 로그인 후 Enter');
    await new Promise(r => process.stdin.once('data', r));
  }
  
  // 에디터 찾기
  let ed = null;
  for (const sc of [page, ...page.frames()]) {
    if (await sc.locator('[contenteditable="true"]').first().isVisible({ timeout: 1000 }).catch(() => false)) {
      ed = sc;
      break;
    }
  }
  if (!ed) throw new Error('에디터 못 찾음');
  
  console.log('제목 입력...');
  const titleEl = ed.locator('.se-documentTitle .se-text-paragraph, .se-title-text').first();
  await titleEl.click();
  await page.keyboard.type(JOB.title, { delay: 10 });
  await sleep(500);
  
  console.log('본문 입력...');
  const bodyEl = ed.locator('.se-component.se-text .se-text-paragraph').last();
  await bodyEl.click();
  await sleep(300);
  
  const paras = JOB.blocks.filter(b => b.type !== 'image').map(b => (b.text || '').trim()).filter(Boolean);
  for (let i = 0; i < paras.length; i++) {
    await page.keyboard.type(paras[i], { delay: 3 });
    if (i < paras.length - 1) {
      await page.keyboard.press('Enter');
      await page.keyboard.press('Enter');
    }
  }
  await sleep(1000);
  
  console.log('임시저장...');
  const saveBtn = ed.locator('button:has-text("저장")').first();
  await saveBtn.click({ timeout: 8000 });
  await sleep(3000);
  
  mkdirSync(dirname(RESULT), { recursive: true });
  writeFileSync(RESULT, `성공\n제목: ${JOB.title}\nURL: ${page.url()}\n`);
  console.log('완료:', page.url());
  
  await browser.close();
})();
