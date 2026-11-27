// Gera o pop-up Aviator v2.
//   node render_v2.mjs          -> renderiza as camadas 3D (arte3d_*.png) e o popup_aviator_v2.png
//   node render_v2.mjs --popup  -> só refaz o popup_aviator_v2.png (reaproveita as camadas 3D)
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
const types = { '.html': 'text/html', '.js': 'text/javascript', '.png': 'image/png', '.woff2': 'font/woff2' };
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
  page.on('console', m => m.type() === 'error' && console.error('[arte3d]', m.text()));
  page.on('pageerror', e => console.error('[arte3d]', e.message));
  for (const layer of ['back', 'front', 'near']) {
    await page.goto(`${base}/arte3d.html?layer=${layer}`);
    await page.waitForFunction('window.__done === true', null, { timeout: 120000 });
    const url = await page.evaluate(() => document.querySelector('canvas').toDataURL('image/png'));
    fs.writeFileSync(path.join(dir, `arte3d_${layer}.png`), Buffer.from(url.split(',')[1], 'base64'));
    console.log('ok', `arte3d_${layer}.png`);
  }
  await page.close();
}

const page = await browser.newPage({ viewport: { width: 1080, height: 1200 }, deviceScaleFactor: 1 });
await page.goto(`${base}/popup_v2.html`);
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(400);
await page.screenshot({ path: path.join(dir, 'popup_aviator_v2.png'), omitBackground: true });
console.log('ok popup_aviator_v2.png');
await browser.close();
server.close();
