// Gera o pop-up Aviator v7.
//   node render_v7.mjs          -> camada 3D das moedas + quadros da animação + PNG estático
//   node render_v7.mjs --popup  -> pula o 3D
// Depois: python3 montar_animacao.py v7  (gera popup_aviator_v7.webp)
// Avião (principal e menores) = aviao_oficial.png
// Requer Playwright + Chromium (no ambiente cloud já vêm instalados).
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require('playwright')); }
catch { ({ chromium } = require('/opt/node-tools/node_modules/playwright')); }

const dir = path.dirname(fileURLToPath(import.meta.url));
const types = { '.html': 'text/html', '.js': 'text/javascript', '.png': 'image/png', '.json': 'application/json', '.woff2': 'font/woff2' };
const server = http.createServer((req, res) => {
  const f = path.join(dir, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  if (!f.startsWith(dir) || !fs.existsSync(f)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'content-type': types[path.extname(f)] || 'application/octet-stream' });
  fs.createReadStream(f).pipe(res);
}).listen(0);
const base = `http://127.0.0.1:${server.address().port}`;

const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const onlyPopup = process.argv.includes('--popup');

if (!onlyPopup) {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1200 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => console.error('[arte3d]', e.message));
  for (const layer of ['back', 'front', 'near']) {
    await page.goto(`${base}/arte3d_v7.html?layer=${layer}`);
    await page.waitForFunction('window.__done === true', null, { timeout: 120000 });
    const url = await page.evaluate(() => document.querySelector('canvas').toDataURL('image/png'));
    fs.writeFileSync(path.join(dir, `arte3d_v7_${layer}.png`), Buffer.from(url.split(',')[1], 'base64'));
    console.log('ok', `arte3d_v7_${layer}.png`);
  }
  await page.close();
}

const FRAMES = 20, LOOP = 2000;   // 20 quadros de 100 ms
const page = await browser.newPage({ viewport: { width: 1080, height: 1200 }, deviceScaleFactor: 1 });
await page.goto(`${base}/popup_v7.html`);
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(400);
const seek = t => page.evaluate(t => { for (const a of document.getAnimations()) { a.pause(); a.currentTime = t; } }, t);
fs.mkdirSync(path.join(dir, 'frames_v7'), { recursive: true });
for (let i = 0; i < FRAMES; i++) {
  await seek(i * LOOP / FRAMES);
  await page.screenshot({ path: path.join(dir, 'frames_v7', `f${String(i).padStart(2, '0')}.png`), omitBackground: true });
}
await seek(0);
await page.screenshot({ path: path.join(dir, 'popup_aviator_v7.png'), omitBackground: true });
console.log('ok frames_v7 + popup_aviator_v7.png');
await browser.close();
server.close();
