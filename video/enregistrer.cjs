#!/usr/bin/env node
// Enregistre la démo image par image en temps virtuel et encode un segment vidéo.
// Usage : node enregistrer.cjs --html app/dist-single/index.html --sortie seg.mp4 [--de N] [--a N]
//   --de / --a : plage d'images [de, a) ; par défaut toute la vidéo. Les images avant --de sont
//   calculées sans capture, pour que chaque segment parte du même état que l'enregistrement complet.
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { chromium } = require('playwright');

const args = Object.fromEntries(process.argv.slice(2).reduce((acc, a, i, all) => {
  if (a.startsWith('--')) acc.push([a.slice(2), all[i + 1]]);
  return acc;
}, []));

const ici = __dirname;
const cfg = JSON.parse(fs.readFileSync(args.config || path.join(ici, 'timing.json'), 'utf8'));
const sec = (s) => { const [m, x] = s.split(':').map(Number); return m * 60 + x; };
const fps = cfg.fps;
const total = Math.round(sec(cfg.duree) * fps);
// Touches à frapper, par numéro d'image : Espace (écran suivant) puis les touches de « touches ».
const evenements = new Map();
const ajoute = (t, touche) => { const i = Math.round(sec(t) * fps); evenements.set(i, [...(evenements.get(i) || []), touche]); };
cfg.espace.forEach((t) => ajoute(t, 'Space'));
(cfg.touches || []).forEach((k) => ajoute(k.a, k.touche));
const presses = [...evenements.keys()].sort((x, y) => x - y);
const frappe = async (page, i) => { for (const k of evenements.get(i) || []) await page.keyboard.press(k); };
const de = Number(args.de ?? 0);
const a = Math.min(total, Number(args.a ?? total));
const html = path.resolve(args.html);
const sortie = path.resolve(args.sortie);
const { largeur, hauteur, echelle } = cfg.fenetre;
const qualite = Number(args.qualite ?? 92);

(async () => {
  // --gpu 1 : rendu matériel (ANGLE sur Vulkan, nouveau mode headless), vérifié sur GPU NVIDIA L4.
  const gpu = args.gpu === '1';
  const browser = await chromium.launch({
    channel: gpu ? 'chromium' : undefined,
    args: [...(gpu ? ['--use-angle=vulkan', '--enable-features=Vulkan', '--enable-gpu'] : ['--enable-unsafe-swiftshader']),
      '--ignore-gpu-blocklist', '--disable-background-timer-throttling',
      '--disable-renderer-backgrounding', '--force-color-profile=srgb', '--hide-scrollbars'],
  });
  const ctx = await browser.newContext({ viewport: { width: largeur, height: hauteur }, deviceScaleFactor: echelle });
  const page = await ctx.newPage();
  const erreurs = [];
  // Les avertissements « GL Driver Message » viennent du rendu logiciel et de la capture, pas de l'application.
  page.on('console', (m) => {
    if ((m.type() === 'error' || m.type() === 'warning') && !m.text().includes('GL Driver Message')) erreurs.push(`[${m.type()}] ${m.text()}`);
  });
  page.on('pageerror', (e) => erreurs.push(`[pageerror] ${e.message}`));
  await page.addInitScript({ path: path.join(ici, 'horloge.js') });
  await page.goto('file://' + html);
  await page.evaluate(() => document.fonts.ready);

  // Premier rendu de la carte : canevas WebGL présent puis quelques passes à temps figé.
  for (let i = 0; i < 200; i++) {
    await page.evaluate(() => window.__vt.step(0));
    const ok = await page.evaluate(() => { const c = document.querySelector('canvas'); return !!c && c.width > 0; });
    if (ok) break;
    await new Promise((r) => setTimeout(r, 50));
  }
  for (let i = 0; i < 10; i++) { await page.evaluate(() => window.__vt.step(0)); await new Promise((r) => setTimeout(r, 30)); }
  await page.evaluate(() => document.fonts.ready);
  const renderer = await page.evaluate(() => {
    const gl = document.createElement('canvas').getContext('webgl2');
    const ext = gl && gl.getExtension('WEBGL_debug_renderer_info');
    return ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : '?';
  });
  console.error(`[${path.basename(sortie)}] renderer WebGL : ${renderer}`);

  const cdp = await ctx.newCDPSession(page);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    '-vf', `scale=${Math.round(largeur * echelle)}:${Math.round(hauteur * echelle)}:flags=lanczos,format=yuv420p`,
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '12', '-r', String(fps), sortie], { stdio: ['pipe', 'inherit', 'inherit'] });

  const dt = 1000 / fps;
  const t0 = Date.now();
  // Avance rapide jusqu'à 1 s avant la dernière touche frappée avant le segment, par pas de 15 images
  // (les minuteries s'exécutent toujours dans l'ordre), puis image par image sans capture.
  const ecranDebut = Math.max(0, ...presses.filter((p) => p <= de));
  const fin_rapide = Math.max(0, ecranDebut - fps);
  let i0 = 0;
  while (i0 < fin_rapide) {
    const prochain = presses.find((p) => p > i0) ?? Infinity;
    const n = Math.min(15, fin_rapide - i0, prochain - i0);
    await frappe(page, i0);
    await page.evaluate((d) => window.__vt.step(d), (i0 === 0 ? 0 : dt) + (n - 1) * dt);
    i0 += n;
  }
  let tCap = Date.now();
  for (let i = i0; i < a; i++) {
    await frappe(page, i);
    await page.evaluate((d) => window.__vt.step(d), i === 0 ? 0 : dt);
    if (i < de) continue;
    if (i === de) tCap = Date.now();
    const { data } = await cdp.send('Page.captureScreenshot', { format: 'jpeg', quality: qualite });
    if (!ff.stdin.write(Buffer.from(data, 'base64'))) await new Promise((r) => ff.stdin.once('drain', r));
    if ((i - de) % 150 === 0) {
      process.stderr.write(`[${path.basename(sortie)}] image ${i}/${a} (${((Date.now() - tCap) / 1000 / (i - de + 1)).toFixed(2)} s par image capturée)\n`);
    }
  }
  ff.stdin.end();
  await new Promise((r) => ff.on('close', r));
  await browser.close();
  fs.writeFileSync(sortie + '.erreurs.txt', erreurs.join('\n'));
  if (erreurs.length) { console.error(`${erreurs.length} message(s) console :\n` + erreurs.slice(0, 20).join('\n')); }
  console.error(`[${path.basename(sortie)}] fini : images ${de}–${a}, ${((Date.now() - t0) / 1000).toFixed(0)} s`);
})().catch((e) => { console.error(e); process.exit(1); });
