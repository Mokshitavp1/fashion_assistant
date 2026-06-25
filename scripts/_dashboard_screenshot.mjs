import { chromium } from 'playwright';
import path from 'path';
import os from 'os';

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
const page = await context.newPage();

// Login via API
const loginRes = await fetch('http://127.0.0.1:8000/auth/login', {
  method: 'POST',
  body: new URLSearchParams({ email: 'e2e.31511396@gmail.com', password: 'E2eTest123' }),
});
const loginData = await loginRes.json();
if (!loginRes.ok) {
  console.log('Login failed, registering new user...');
  process.exit(1);
}

await context.addInitScript((data) => {
  localStorage.setItem('accessToken', data.access_token);
  localStorage.setItem('refreshToken', data.refresh_token);
  localStorage.setItem('userId', String(data.user_id));
}, loginData);

await page.goto('http://localhost:5173/dashboard', { waitUntil: 'networkidle' });
await page.waitForTimeout(3000);

const screenshotPath = path.join(os.tmpdir(), 'dashboard-screenshot.png');
await page.screenshot({ path: screenshotPath, fullPage: true });

const state = await page.evaluate(() => ({
  url: location.href,
  text: document.body.innerText.slice(0, 300),
  hasPg: Boolean(document.querySelector('.pg')),
  hasLoader: Boolean(document.querySelector('.loader-wrap')),
  htmlSnippet: document.querySelector('#root')?.innerHTML?.slice(0, 500),
}));

console.log(JSON.stringify(state, null, 2));
console.log('Screenshot:', screenshotPath);
await browser.close();
