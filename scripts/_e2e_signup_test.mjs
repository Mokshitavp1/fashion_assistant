import { chromium } from 'playwright';
import fs from 'fs';
import os from 'os';
import path from 'path';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
const failedRequests = [];
page.on('response', (res) => {
  if (res.status() >= 400) failedRequests.push(`${res.status()} ${res.url()} ${res.statusText()}`);
});

await page.goto('http://localhost:5173/onboarding', { waitUntil: 'networkidle' });
await page.click('text=Create Account');
await page.fill('input[placeholder="Enter your name"]', 'Playwright User');
const email = `pw.test.${Date.now()}@gmail.com`;
await page.fill('input[placeholder="you@example.com"]', email);
await page.fill('input[type="password"]', 'Playwright1');
await page.click('button:has-text("Continue")');

const tmp = path.join(os.tmpdir(), 'pw-body.jpg');
const buf = Buffer.from(
  '/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAn/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCwAB//2Q==',
  'base64',
);
fs.writeFileSync(tmp, buf);
await page.setInputFiles('#photo-upload', tmp);
await page.fill('input[placeholder="170"]', '170');
await page.fill('input[placeholder="65"]', '65');
await page.click('button:has-text("Continue")');
await page.click('button:has-text("Complete Setup")');
await page.waitForTimeout(15000);

console.log('URL:', page.url());
console.log('BODY:', await page.evaluate(() => document.body.innerText.slice(0, 400)));
console.log('STORAGE:', await page.evaluate(() => ({
  userId: localStorage.getItem('userId'),
  hasToken: Boolean(localStorage.getItem('accessToken')),
})));
console.log('FAILED:', failedRequests);

fs.unlinkSync(tmp);
await browser.close();
