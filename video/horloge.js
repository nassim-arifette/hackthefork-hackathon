// Horloge virtuelle injectée avant le code de l'application (page.addInitScript).
// Le temps de la page n'avance que lorsque l'enregistreur appelle __vt.step(dt) :
// performance.now, Date, setTimeout/setInterval et requestAnimationFrame suivent ce temps,
// et les animations et transitions CSS sont mises en pause puis positionnées dessus.
// MessageChannel reste réel : React l'utilise pour appliquer ses mises à jour.
(() => {
  const realNow = performance.now.bind(performance);
  const base = realNow();
  const RealDate = Date;
  const dateBase = RealDate.now();
  let vnow = 0;
  let seq = 1;
  const timers = new Map();
  let rafs = new Map();

  const asFn = (fn) => (typeof fn === 'function' ? fn : () => {});
  const report = (e) => queueMicrotask(() => { throw e; });

  window.setTimeout = (fn, ms = 0, ...args) => {
    const id = seq++;
    timers.set(id, { due: vnow + Math.max(0, Number(ms) || 0), fn: asFn(fn), args, every: 0, id });
    return id;
  };
  window.setInterval = (fn, ms = 0, ...args) => {
    const id = seq++;
    const every = Math.max(1, Number(ms) || 0);
    timers.set(id, { due: vnow + every, fn: asFn(fn), args, every, id });
    return id;
  };
  window.clearTimeout = window.clearInterval = (id) => { timers.delete(id); };
  window.requestAnimationFrame = (fn) => { const id = seq++; rafs.set(id, fn); return id; };
  window.cancelAnimationFrame = (id) => { rafs.delete(id); };
  performance.now = () => base + vnow;

  class VDate extends RealDate {
    constructor(...a) { if (a.length === 0) super(dateBase + vnow); else super(...a); }
    static now() { return dateBase + vnow; }
  }
  window.Date = VDate;

  const runTimers = (target) => {
    for (;;) {
      let next = null;
      for (const t of timers.values()) {
        if (t.due <= target && (!next || t.due < next.due || (t.due === next.due && t.id < next.id))) next = t;
      }
      if (!next) break;
      vnow = Math.max(vnow, next.due);
      if (next.every) next.due += next.every; else timers.delete(next.id);
      try { next.fn(...next.args); } catch (e) { report(e); }
    }
    vnow = target;
  };

  const runRaf = () => {
    const cbs = rafs;
    rafs = new Map();
    for (const cb of cbs.values()) { try { cb(base + vnow); } catch (e) { report(e); } }
  };

  // Laisse React appliquer ses mises à jour (tâches MessageChannel réelles).
  const flush = async (n = 3) => {
    for (let i = 0; i < n; i++) {
      await new Promise((r) => { const c = new MessageChannel(); c.port1.onmessage = () => r(); c.port2.postMessage(0); });
    }
  };

  const starts = new WeakMap();
  const syncCss = () => {
    for (const a of document.getAnimations()) {
      if (!starts.has(a)) starts.set(a, vnow);
      a.pause();
      a.currentTime = vnow - starts.get(a);
    }
  };

  window.__vt = {
    now: () => vnow,
    async step(dt) {
      runTimers(vnow + dt);
      await flush();
      runRaf();
      await flush();
      runRaf();
      await flush();
      syncCss();
    },
  };
})();
