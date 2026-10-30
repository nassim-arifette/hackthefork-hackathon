import { useEffect, useRef, useState } from 'react';

const reduce = typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

/** Anime une valeur numérique vers sa cible (compteurs). */
export function useTween(target: number, ms = 450): number {
  const [v, setV] = useState(target);
  const from = useRef(target);
  useEffect(() => {
    if (reduce) { setV(target); return; }
    const start = performance.now(), a = from.current;
    let raf = 0;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / ms);
      const e = 1 - Math.pow(1 - t, 3);
      const cur = a + (target - a) * e;
      from.current = cur;
      setV(cur);
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, ms]);
  return v;
}
