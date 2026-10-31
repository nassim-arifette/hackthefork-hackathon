// Voie A : Chromium utilise-t-il le GPU dans le conteneur ? Pour chaque jeu d'options, lit
// Voie A : Chromium utilise-t-il le GPU dans le conteneur ? Pour chaque jeu d'options, lit le renderer WebGL
const { chromium } = require('playwright');
const html = process.argv[2];

const essais = {
  'angle-vulkan': ['--use-angle=vulkan', '--enable-features=Vulkan', '--ignore-gpu-blocklist', '--enable-gpu'],
  'angle-gl-egl': ['--use-angle=gl-egl', '--use-gl=angle', '--ignore-gpu-blocklist', '--enable-gpu'],
  'egl': ['--use-gl=egl', '--ignore-gpu-blocklist', '--enable-gpu'],
};

(async () => {
  for (const [nom, args] of Object.entries(essais)) {
    for (const channel of ['chromium']) {
      let b;
      try {
        b = await chromium.launch({ channel, args });
        const p = await b.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1.5 });
        await p.goto('file://' + html);
        const info = await p.evaluate(() => {
          const gl = document.createElement('canvas').getContext('webgl2');
          const ext = gl && gl.getExtension('WEBGL_debug_renderer_info');
          return ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : 'renderer ?';
        });
        await p.waitForTimeout(3000);
        for (let i = 0; i < 3; i++) { await p.keyboard.press('Space'); await p.waitForTimeout(800); }
        await p.waitForTimeout(6500);
        const fps = await p.evaluate(() => new Promise((r) => {
          let n = 0; const t0 = performance.now();
          const f = () => { n++; if (performance.now() - t0 < 3000) requestAnimationFrame(f); else r(n / ((performance.now() - t0) / 1000)); };
          requestAnimationFrame(f);
        }));
        console.log(`${nom} / ${channel || 'headless-shell'} : ${fps.toFixed(1)} i/s | ${info}`);
      } catch (e) {
        console.log(`${nom} / ${channel || 'headless-shell'} : échec ${String(e).slice(0, 200)}`);
      } finally { if (b) await b.close(); }
    }
  }
})();
