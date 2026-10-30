import { backtest, fmt, pct, supply, thresholds } from '../data';

const W = 340;

/** Courbe d'offre : tonnes mobilisables selon le prix rendu proposé. */
export function SupplyChart({ price, min, max }: { price: number; min: number; max: number }) {
  const pts = supply.filter((s) => s.prix >= min && s.prix <= max);
  const tMax = Math.max(1, ...pts.map((s) => s.tonnes));
  const h = 150, l = 44, r = 10, t = 10, b = 22;
  const X = (v: number) => l + ((W - l - r) * v) / tMax;
  const Y = (p: number) => t + (h - t - b) * (1 - (p - min) / (max - min));
  const cur = [...pts].reverse().find((s) => s.prix <= price) ?? pts[0];
  const path = pts.map((s, i) => `${i ? 'L' : 'M'}${X(s.tonnes).toFixed(1)},${Y(s.prix).toFixed(1)}`).join('');
  const ticks = [min, Math.round((min + max) / 2 / 50) * 50, max];
  return (
    <svg viewBox={`0 0 ${W} ${h}`} role="img" aria-label="Courbe d'offre">
      {ticks.map((p) => (
        <g key={p}>
          <line x1={l} x2={W - r} y1={Y(p)} y2={Y(p)} className="grid" />
          <text x={l - 6} y={Y(p) + 3} className="tick" textAnchor="end">{p}</text>
        </g>
      ))}
      <text x={l} y={h - 6} className="tick">0 t</text>
      <text x={W - r} y={h - 6} className="tick" textAnchor="end">{fmt(tMax / 1000)} kt</text>
      <path d={path} className="line-wheat" />
      <line x1={l} x2={X(cur.tonnes)} y1={Y(price)} y2={Y(price)} className="guide" />
      <line x1={X(cur.tonnes)} x2={X(cur.tonnes)} y1={Y(price)} y2={h - b} className="guide" />
      <circle cx={X(cur.tonnes)} cy={Y(Math.min(max, price))} r={4.5} className="dot" />
    </svg>
  );
}

/** Prix de la sécurité : P* selon la fiabilité visée (Seine-et-Marne). */
export function SecurityChart() {
  const pts = thresholds.sensibilite.fiabilite;
  const h = 130, l = 44, r = 10, t = 10, b = 22;
  const pMin = 600, pMax = 2700;
  const X = (x: number) => l + ((W - l - r) * (x - 0.5)) / 0.45;
  const Y = (p: number) => t + (h - t - b) * (1 - (p - pMin) / (pMax - pMin));
  const path = pts.map((s, i) => `${i ? 'L' : 'M'}${X(s.x).toFixed(1)},${Y(s.p_star).toFixed(1)}`).join('');
  const p80 = pts.find((s) => Math.abs(s.x - 0.8) < 1e-6)!;
  return (
    <svg viewBox={`0 0 ${W} ${h}`} role="img" aria-label="Prix plancher selon la fiabilité">
      {[1000, 1500, 2000, 2500].map((p) => (
        <g key={p}>
          <line x1={l} x2={W - r} y1={Y(p)} y2={Y(p)} className="grid" />
          <text x={l - 6} y={Y(p) + 3} className="tick" textAnchor="end">{p}</text>
        </g>
      ))}
      {[0.5, 0.6, 0.7, 0.8, 0.9].map((x) => (
        <text key={x} x={X(x)} y={h - 6} className="tick" textAnchor="middle">{pct(x)}</text>
      ))}
      <path d={path} className="line-lentil" />
      <circle cx={X(0.8)} cy={Y(p80.p_star)} r={4.5} className="dot" />
      <text x={X(0.8) - 8} y={Y(p80.p_star) - 9} className="tick strong" textAnchor="end">{fmt(p80.p_star)} €/t</text>
    </svg>
  );
}

/** Révélation du backtest : années 2019-2025, intervalle prédit puis réel. */
export function BacktestReveal({ shown }: { shown: number }) {
  const years = backtest.annees;
  const h = 170, l = 30, r = 10, t = 12, b = 22;
  const lo = 0.3, hi = 1.6;
  const X = (i: number) => l + ((W - l - r) * (i + 0.5)) / years.length;
  const Y = (v: number) => t + (h - t - b) * (1 - (v - lo) / (hi - lo));
  return (
    <svg viewBox={`0 0 ${W} ${h}`} role="img" aria-label="Backtest année par année">
      {[0.5, 1, 1.5].map((v) => (
        <g key={v}>
          <line x1={l} x2={W - r} y1={Y(v)} y2={Y(v)} className={v === 1 ? 'grid strong' : 'grid'} />
          <text x={l - 5} y={Y(v) + 3} className="tick" textAnchor="end">{v}</text>
        </g>
      ))}
      {years.map((y, i) => {
        const vis = i < shown;
        const ok = y.rel_reel_moyen >= y.rel_q10_moyen && y.rel_reel_moyen <= y.rel_q90_moyen;
        return (
          <g key={y.annee} className={vis ? 'bt-on' : 'bt-off'}>
            <rect x={X(i) - 11} width={22} y={Y(y.rel_q90_moyen)} height={Y(y.rel_q10_moyen) - Y(y.rel_q90_moyen)} rx={4} className="band" />
            <line x1={X(i) - 11} x2={X(i) + 11} y1={Y(y.rel_q50_moyen)} y2={Y(y.rel_q50_moyen)} className="median" />
            <circle cx={X(i)} cy={Y(y.rel_reel_moyen)} r={5.5} className={ok ? 'real ok' : 'real ko'} />
            <text x={X(i)} y={h - 6} className="tick" textAnchor="middle">{y.annee}</text>
          </g>
        );
      })}
    </svg>
  );
}
