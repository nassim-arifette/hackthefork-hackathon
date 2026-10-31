import { backtest, D77, dateOf, fmt, MARKET, meta, ndviAt, pct, reliabilityAt, SAISON, SUIVI, thresholds, type Statut } from '../data';

// Largeur logique commune : le texte du panneau fait environ 416 px.
const W = 416;

/** Rendements nationaux 2010-2025 en indice (moyenne = 100). Étiquettes directes, pas de légende. */
export function YieldsChart() {
  const rows = meta.rendements_nationaux;
  const mB = rows.reduce((a, r) => a + r.ble, 0) / rows.length;
  const mL = rows.reduce((a, r) => a + r.lentille, 0) / rows.length;
  const h = 196, l = 28, r = 64, t = 12, b = 26, lo = 50, hi = 135;
  const X = (y: number) => l + ((W - l - r) * (y - 2010)) / 15;
  const Y = (v: number) => t + (h - t - b) * (1 - (v - lo) / (hi - lo));
  const idx = (k: 'ble' | 'lentille', m: number) => rows.map((d) => (100 * d[k]) / m);
  const path = (vals: number[]) => vals.map((v, i) => `${i ? 'L' : 'M'}${X(2010 + i).toFixed(1)},${Y(v).toFixed(1)}`).join('');
  const b16 = (100 * rows.find((d) => d.annee === 2016)!.ble) / mB;
  const l20 = (100 * rows.find((d) => d.annee === 2020)!.lentille) / mL;
  const lastB = idx('ble', mB)[15], lastL = idx('lentille', mL)[15];
  return (
    <svg viewBox={`0 0 ${W} ${h}`} role="img" aria-label="Rendement national du blé et de la lentille, en indice, de 2010 à 2025">
      {[60, 80, 120].map((v) => (
        <g key={v}><line x1={l} x2={W - r} y1={Y(v)} y2={Y(v)} className="grid" />
          <text x={l - 6} y={Y(v) + 3.5} className="tick" textAnchor="end">{v}</text></g>
      ))}
      <line x1={l} x2={W - r} y1={Y(100)} y2={Y(100)} className="ref" />
      <text x={l - 6} y={Y(100) + 3.5} className="tick" textAnchor="end">100</text>
      {[2010, 2015, 2020, 2025].map((y) => <text key={y} x={X(y)} y={h - 8} className="tick" textAnchor="middle">{y}</text>)}
      <path d={path(idx('ble', mB))} className="ln wheat" />
      <path d={path(idx('lentille', mL))} className="ln lentil" />
      <text x={X(2025) + 8} y={Y(lastB) + 4} className="lbl wheat">Blé</text>
      <text x={X(2025) + 8} y={Y(lastL) + 4} className="lbl lentil">Lentille</text>
      <circle cx={X(2016)} cy={Y(b16)} r={3.5} className="pt wheat" />
      <text x={X(2016)} y={Y(b16) + 17} className="note" textAnchor="middle">2016</text>
      <circle cx={X(2020)} cy={Y(l20)} r={3.5} className="pt lentil" />
      <text x={X(2020) + 8} y={Y(l20) + 4} className="note">2020</text>
    </svg>
  );
}

/** Prix proposé → part des années où la lentille gagne (haut) et hectares qui basculent (bas). */
export function PriceChart({ price, min, max, supply }: { price: number; min: number; max: number; supply: { prix: number; hectares: number }[] }) {
  const h = 276, l = 40, r = 14;
  const top = [26, 118] as const;
  const bot = [170, 236] as const;
  const X = (p: number) => l + ((W - l - r) * (p - min)) / (max - min);
  const Yr = (v: number) => top[0] + (top[1] - top[0]) * (1 - v);
  const haMax = Math.max(1, ...supply.map((s) => s.hectares));
  const Yh = (v: number) => bot[0] + (bot[1] - bot[0]) * (1 - v / haMax);
  const rel: [number, number][] = [];
  for (let p = min; p <= max; p += 10) rel.push([p, reliabilityAt(p)]);
  const relPath = rel.map(([p, v], i) => `${i ? 'L' : 'M'}${X(p).toFixed(1)},${Yr(v).toFixed(1)}`).join('');
  const pts = supply.filter((s) => s.prix >= min && s.prix <= max);
  const supPath = `M${X(min)},${Yh(0)}` + pts.map((s) => `L${X(s.prix).toFixed(1)},${Yh(s.hectares).toFixed(1)}`).join('') + `L${X(max)},${Yh(0)}Z`;
  const cur = Math.max(min, Math.min(max, price));
  const ticks = [800, 1200, 1600, 2000].filter((v) => v > min && v < max);
  return (
    <svg viewBox={`0 0 ${W} ${h}`} role="img" aria-label="Part des années gagnantes et hectares qui basculent selon le prix">
      <rect x={X(MARKET.min)} width={X(MARKET.max) - X(MARKET.min)} y={top[0] - 14} height={bot[1] - top[0] + 14} className="band-market" />
      <text x={X(MARKET.max) + 5} y={Yr(0.12)} className="note">référence 2012–2016</text>

      <text x={l} y={10} className="axis-title">Années où la lentille rapporte au moins autant que le blé</text>
      {[0, 0.5, 1].map((v) => (
        <g key={v}><line x1={l} x2={W - r} y1={Yr(v)} y2={Yr(v)} className="grid" />
          <text x={l - 6} y={Yr(v) + 3.5} className="tick" textAnchor="end">{v === 0 ? '0' : v === 1 ? '10' : '5'}</text></g>
      ))}
      <line x1={l} x2={W - r} y1={Yr(0.8)} y2={Yr(0.8)} className="ref" />
      <text x={X(MARKET.max) + 5} y={Yr(0.8) - 5} className="note">objectif 8 sur 10</text>
      <path d={relPath} className="ln lentil" />

      <text x={l} y={bot[0] - 12} className="axis-title">Hectares de blé qui basculent</text>
      <path d={supPath} className="area wheat" />
      <line x1={l} x2={W - r} y1={Yh(0)} y2={Yh(0)} className="base" />
      <text x={l - 6} y={Yh(haMax) + 3.5} className="tick" textAnchor="end">{fmt(haMax / 1000)} k</text>

      {ticks.map((tk) => <text key={tk} x={X(tk)} y={h - 14} className="tick" textAnchor="middle">{fmt(tk)}</text>)}
      <text x={W - r} y={h - 1} className="tick" textAnchor="end">€/t rendu</text>
      <line x1={X(cur)} x2={X(cur)} y1={top[0] - 14} y2={bot[1]} className="cursor" />
      <circle cx={X(cur)} cy={Yr(reliabilityAt(cur))} r={4.5} className="pt ink" />
    </svg>
  );
}

/** Marge par hectare, lentille sous contrat contre blé, une année rejouée. */
export function MarginBars({ lentil, wheat }: { lentil: number; wheat: number }) {
  const rows = [
    { label: 'Lentille sous contrat', v: lentil, cls: 'lentil' },
    { label: 'Blé tendre d’hiver', v: wheat, cls: 'wheat' },
  ];
  const max = Math.max(1, ...rows.map((r) => Math.abs(r.v)));
  return (
    <div className="bars">
      {rows.map((r) => (
        <div key={r.label} className="bar-row">
          <span className="bar-l">{r.label}</span>
          <span className="bar-track"><span className={`bar ${r.cls}`} style={{ width: `${(Math.max(0, r.v) / max) * 100}%` }} /></span>
          <b className="bar-v">{fmt(r.v)} €/ha</b>
        </div>
      ))}
    </div>
  );
}

/** Prix plancher selon la fiabilité visée (Seine-et-Marne), de 5 à 9 années sur 10. */
export function SecurityChart() {
  const pts = thresholds.sensibilite.fiabilite.filter((s) => s.x <= 0.9 + 1e-6);
  const h = 176, l = 44, r = 16, t = 14, b = 26;
  const pMin = 500, pMax = Math.ceil((Math.max(...pts.map((s) => s.p_star)) * 1.08) / 500) * 500;
  const X = (x: number) => l + ((W - l - r) * (x - 0.5)) / 0.4;
  const Y = (p: number) => t + (h - t - b) * (1 - (p - pMin) / (pMax - pMin));
  const path = pts.map((s, i) => `${i ? 'L' : 'M'}${X(s.x).toFixed(1)},${Y(s.p_star).toFixed(1)}`).join('');
  const p80 = pts.find((s) => Math.abs(s.x - 0.8) < 1e-6)!;
  const p50 = pts.find((s) => Math.abs(s.x - 0.5) < 1e-6)!;
  const p90 = pts.find((s) => Math.abs(s.x - 0.9) < 1e-6)!;
  const gridVals = [1000, 2000, 3000, 4000].filter((v) => v < pMax);
  return (
    <svg viewBox={`0 0 ${W} ${h}`} role="img" aria-label="Prix plancher selon la fiabilité visée">
      <rect x={l} width={W - l - r} y={Y(MARKET.max)} height={Y(MARKET.min) - Y(MARKET.max)} className="band-market" />
      <text x={W - r} y={Y(MARKET.max) - 5} className="note" textAnchor="end">référence historique {MARKET.annees[0]}–{MARKET.annees[1]}</text>
      {gridVals.map((p) => (
        <g key={p}><line x1={l} x2={W - r} y1={Y(p)} y2={Y(p)} className="grid" />
          <text x={l - 6} y={Y(p) + 3.5} className="tick" textAnchor="end">{fmt(p)}</text></g>
      ))}
      {[0.5, 0.6, 0.7, 0.8, 0.9].map((x) => <text key={x} x={X(x)} y={h - 8} className="tick" textAnchor="middle">{Math.round(x * 10)} sur 10</text>)}
      <path d={path} className="ln lentil" />
      <circle cx={X(0.5)} cy={Y(p50.p_star)} r={3.5} className="pt lentil" />
      <text x={X(0.5) + 8} y={Y(p50.p_star) - 8} className="lbl ink">{fmt(p50.p_star)} €/t</text>
      <circle cx={X(0.8)} cy={Y(p80.p_star)} r={4.5} className="pt ink" />
      <text x={X(0.8) - 9} y={Y(p80.p_star) - 9} className="lbl ink" textAnchor="end">{fmt(p80.p_star)} €/t</text>
      <circle cx={X(0.9)} cy={Y(p90.p_star)} r={3.5} className="pt lentil" />
      <text x={X(0.9) - 9} y={Y(p90.p_star) + 4} className="lbl ink" textAnchor="end">{fmt(p90.p_star)} €/t</text>
    </svg>
  );
}

/** Sensibilité de P* (Seine-et-Marne) à chaque hypothèse : un segment par hypothèse. */
export function Sensitivity() {
  const s = thresholds.sensibilite;
  const base = D77.p_star;
  const rows = [
    { label: 'Prix du blé, de 160 à 280 €/t', a: s.prix_ble_fixe[0].p_star, b: s.prix_ble_fixe[s.prix_ble_fixe.length - 1].p_star },
    { label: 'Part refusée au tri, de 0 à 20 %', a: s.qualite[0].p_star, b: s.qualite[s.qualite.length - 1].p_star },
    { label: 'Bénéfice de rotation, de 0 à 200 €/ha', a: s.bonus_rotation[s.bonus_rotation.length - 1].p_star, b: s.bonus_rotation[0].p_star },
    { label: 'Charges du blé, de 600 à 800 €/ha', a: s.charges_ble[s.charges_ble.length - 1].p_star, b: s.charges_ble[0].p_star },
    { label: 'Charges de la lentille, de 400 à 600 €/ha', a: s.charges_lentille[0].p_star, b: s.charges_lentille[s.charges_lentille.length - 1].p_star },
    { label: 'Aide couplée, de 0 à 122 €/ha', a: s.aide[s.aide.length - 1].p_star, b: s.aide[0].p_star },
  ];
  const all = rows.flatMap((r) => [r.a, r.b]);
  const lo = Math.floor((Math.min(...all) - 100) / 100) * 100, hi = Math.ceil((Math.max(...all) + 100) / 100) * 100, pad = 6;
  const X = (p: number) => pad + ((W - 2 * pad) * (p - lo)) / (hi - lo);
  return (
    <div className="sens">
      {rows.map((row) => {
        const a = Math.min(row.a, row.b), b = Math.max(row.a, row.b);
        return (
          <div key={row.label} className="sens-row">
            <div className="sens-label"><span>{row.label}</span><b>{fmt(a)} – {fmt(b)} €/t</b></div>
            <svg viewBox={`0 0 ${W} 16`} aria-hidden="true">
              <line x1={X(base)} x2={X(base)} y1={0} y2={16} className="ref" />
              <line x1={X(a)} x2={X(b)} y1={8} y2={8} className="dumbbell" />
              <circle cx={X(a)} cy={8} r={3.5} className="pt ink" />
              <circle cx={X(b)} cy={8} r={3.5} className="pt ink" />
            </svg>
          </div>
        );
      })}
      <div className="sens-scale"><span>{fmt(lo)} €/t</span><span>pointillé : valeur retenue, {fmt(base)} €/t</span><span>{fmt(hi)} €/t</span></div>
    </div>
  );
}

/** Révélation du backtest : par année, intervalle à 80 % prédit, puis rendement réel. */
export function BacktestReveal({ shown }: { shown: number }) {
  const years = backtest.annees;
  const h = 214, l = 30, r = 8, t = 10, b = 28;
  const lo = Math.min(0, ...years.map((y) => y.rel_q10_moyen));
  const hi = Math.max(1.6, ...years.map((y) => y.rel_q90_moyen)) + 0.05;
  const X = (i: number) => l + ((W - l - r) * (i + 0.5)) / years.length;
  const Y = (v: number) => t + (h - t - b) * (1 - (v - lo) / (hi - lo));
  return (
    <svg viewBox={`0 0 ${W} ${h}`} role="img" aria-label="Backtest, année par année">
      {[0.5, 1.5].filter((v) => v >= lo && v <= hi).map((v) => (
        <g key={v}><line x1={l} x2={W - r} y1={Y(v)} y2={Y(v)} className="grid" />
          <text x={l - 6} y={Y(v) + 3.5} className="tick" textAnchor="end">{v.toLocaleString('fr-FR')}</text></g>
      ))}
      <line x1={l} x2={W - r} y1={Y(1)} y2={Y(1)} className="ref" />
      <text x={l - 6} y={Y(1) + 3.5} className="tick" textAnchor="end">1</text>
      {years.map((y, i) => {
        const vis = i < shown;
        const ok = y.rel_reel_moyen >= y.rel_q10_moyen && y.rel_reel_moyen <= y.rel_q90_moyen;
        return (
          <g key={y.annee}>
            <text x={X(i)} y={h - 10} className={`tick ${vis ? 'on' : ''}`} textAnchor="middle">{y.annee}</text>
            <g className={vis ? 'bt bt-on' : 'bt'}>
              <rect x={X(i) - 13} width={26} y={Y(y.rel_q90_moyen)} height={Y(y.rel_q10_moyen) - Y(y.rel_q90_moyen)} rx={2} className="interval" />
              <line x1={X(i) - 13} x2={X(i) + 13} y1={Y(y.rel_q50_moyen)} y2={Y(y.rel_q50_moyen)} className="median" />
              <circle cx={X(i)} cy={Y(y.rel_reel_moyen)} r={5.5} className={ok ? 'pt ink real' : 'pt fail real'} />
            </g>
          </g>
        );
      })}
    </svg>
  );
}

export { pct };


const STATUT_CLASS: Record<Statut, string> = { conforme: 'lentil', a_surveiller: 'wheat', en_retard: 'fail' };
const MOIS = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.'];

/** Courbes NDVI de la saison, dessinées jusqu'au jour du replay. */
export function SeasonChart({ day, focus }: { day: number; focus: string | null }) {
  const h = 232, l = 34, r = 14, t = 16, b = 28;
  const X = (d: number) => l + ((W - l - r) * d) / SAISON.jours;
  const Y = (v: number) => t + (h - t - b) * (1 - v);
  const upTo = (serie: { day: number; ndvi: number }[]) => {
    const pts = serie.filter((q) => q.day <= day);
    if (day > serie[0].day && day < serie[serie.length - 1].day) pts.push({ day, ndvi: ndviAt(serie, day) });
    return pts;
  };
  const path = (pts: { day: number; ndvi: number }[]) => pts.map((q, i) => `${i ? 'L' : 'M'}${X(q.day).toFixed(1)},${Y(q.ndvi).toFixed(1)}`).join('');
  const months: { day: number; label: string }[] = [];
  for (let m = 2; m <= 7; m++) {
    const d = Math.round((Date.UTC(SAISON.annee, m, 1) - dateOf(0).getTime()) / 864e5);
    if (d >= 0 && d <= SAISON.jours) months.push({ day: d, label: MOIS[m] });
  }
  const ref = upTo(SAISON.reference);
  const date = dateOf(day);
  return (
    <svg viewBox={`0 0 ${W} ${h}`} role="img" aria-label="NDVI des parcelles suivies pendant la saison">
      <rect x={X(SAISON.fenetre[0])} width={X(SAISON.fenetre[1]) - X(SAISON.fenetre[0])} y={t} height={h - t - b} className="band-market" />
      <text x={X(SAISON.fenetre[0]) + 5} y={t + 11} className="note">floraison, remplissage</text>
      {[0, 0.5, 1].map((v) => (
        <g key={v}><line x1={l} x2={W - r} y1={Y(v)} y2={Y(v)} className="grid" />
          <text x={l - 6} y={Y(v) + 3.5} className="tick" textAnchor="end">{v.toLocaleString('fr-FR')}</text></g>
      ))}
      {months.map((m) => <text key={m.day} x={X(m.day)} y={h - 10} className="tick" textAnchor="start">{m.label}</text>)}
      {SUIVI.map((p) => {
        const pts = upTo(p.serie);
        const on = focus === null || focus === p.id;
        return (
          <g key={p.id} opacity={on ? 1 : 0.22}>
            <path d={path(pts)} className={`ln thin ${STATUT_CLASS[p.statut]}`} />
            {pts.length > 0 && (p.statut !== 'conforme' || focus === p.id) && (
              <text x={X(pts[pts.length - 1].day) + 4} y={Y(pts[pts.length - 1].ndvi) + 3.5} className={`lbl small ${STATUT_CLASS[p.statut]}`}>{p.lettre}</text>
            )}
          </g>
        );
      })}
      <path d={path(ref)} className="ln ref-line" />
      <line x1={X(day)} x2={X(day)} y1={t} y2={h - b} className="cursor" />
      <text x={Math.min(X(day) + 5, W - r - 60)} y={h - b - 6} className="tick on">{date.getUTCDate()} {MOIS[date.getUTCMonth()]}</text>
    </svg>
  );
}
