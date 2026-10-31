// Visuels du parcours de présentation : pictogrammes animés, lisibles au vidéoprojecteur.
// Les animations sont en CSS (styles.css) et s'arrêtent quand le système demande moins de mouvement.
import type { CSSProperties, ReactNode } from 'react';
import { meta } from '../data';

const W = 416;
const style = (vars: Record<string, string | number>) => vars as CSSProperties;

/** Dix bols de lentilles : ceux qui viennent des champs français, puis ceux qui arrivent de l'étranger. */
export function Bowls({ imported, total = 10 }: { imported: number; total?: number }) {
  const slot = W / total;
  return (
    <svg viewBox={`0 0 ${W} 92`} className="picto" role="img"
      aria-label={`Sur ${total} bols de lentilles mangés en France, ${imported} viennent de l’étranger`}>
      {Array.from({ length: total }, (_, i) => {
        const imp = i >= total - imported;
        return (
          <g key={i} transform={`translate(${slot * i + slot / 2},0)`}>
            <g className={`bowl ${imp ? 'imp' : 'fr'}`} style={{ animationDelay: `${(imp ? 700 : 0) + i * 110}ms` }}>
              {[-8, -3, 2, 7, -5, 0, 5].map((x, k) => (
                <circle key={k} cx={x} cy={k < 4 ? 34 : 29} r={3.4} className="lentil-dot" />
              ))}
              <path d="M-18,36 Q-18,58 0,58 Q18,58 18,36 Z" className="cup" />
              {imp && (
                <g className="ship" transform="translate(0,74)">
                  <path d="M-11,0 L11,0 L8,5 L-8,5 Z" />
                  <rect x={-6} y={-5} width={5} height={4} /><rect x={0} y={-5} width={5} height={4} />
                </g>
              )}
            </g>
          </g>
        );
      })}
    </svg>
  );
}

/** Récolte par hectare, en écart à l'année moyenne 2010-2025 : le blé bouge peu, la lentille beaucoup. */
export function HarvestBars() {
  const rows = meta.rendements_nationaux;
  const mean = (k: 'ble' | 'lentille') => rows.reduce((a, r) => a + r[k], 0) / rows.length;
  const h = 236, l = 70, r = 6, S = 44 / 0.45;
  const bw = (W - l - r) / rows.length;
  const panels = [
    { k: 'ble' as const, label: 'Blé', y0: 58, m: mean('ble'), note: 2016 },
    { k: 'lentille' as const, label: 'Lentille', y0: 160, m: mean('lentille'), note: 2020 },
  ];
  return (
    <svg viewBox={`0 0 ${W} ${h}`} className="picto" role="img"
      aria-label="Récolte par hectare du blé et de la lentille en France, de 2010 à 2025, en écart à l’année moyenne">
      {panels.map((p, pi) => (
        <g key={p.k}>
          <text x={0} y={p.y0 + 4} className={`lbl ${p.k === 'ble' ? 'wheat' : 'lentil'}`}>{p.label}</text>
          <line x1={l} x2={W - r} y1={p.y0} y2={p.y0} className="base" />
          {rows.map((d, i) => {
            const dev = d[p.k] / p.m - 1;
            const hgt = Math.max(1.5, Math.abs(dev) * S);
            const x = l + i * bw + 1.5;
            const y = dev >= 0 ? p.y0 - hgt : p.y0;
            return (
              <rect key={d.annee} x={x} y={y} width={bw - 3} height={hgt} className={`hb ${p.k}`}
                style={{ animationDelay: `${pi * 350 + i * 70}ms`, transformOrigin: `${x + (bw - 3) / 2}px ${p.y0}px` }} />
            );
          })}
          {rows.filter((d) => d.annee === p.note).map((d) => {
            const i = rows.indexOf(d), dev = d[p.k] / p.m - 1;
            return (
              <text key="n" x={l + i * bw + bw / 2} y={p.y0 + Math.abs(dev) * S + 14} className="lbl ink small hb-note"
                textAnchor="middle" style={{ animationDelay: `${pi * 350 + rows.length * 70}ms` }}>{d.annee}</text>
            );
          })}
        </g>
      ))}
      {[2010, 2015, 2020, 2025].map((y) => (
        <text key={y} x={l + (y - 2010) * bw + bw / 2} y={h - 4} className="tick" textAnchor="middle">{y}</text>
      ))}
    </svg>
  );
}

function Truck({ x, y }: { x: number; y: number }) {
  return (
    <g transform={`translate(${x},${y})`} className="mini-truck">
      <rect x={-14} y={-9} width={15} height={10} rx={1.5} className="box" />
      <path d="M2,-6 L8,-6 L12,-1 L12,1 L2,1 Z" className="cab" />
      <circle cx={-9} cy={3} r={2.6} className="wheel" /><circle cx={7} cy={3} r={2.6} className="wheel" />
    </g>
  );
}

/** La filière : le champ, la coopérative, le conditionneur, l'assiette. Le contrat se signe avant les semis. */
export function Filiere() {
  const xs = [34, 142, 252, 360], yIcon = 74, yLine = 82;
  const links = [0, 1, 2].map((k) => ({ a: xs[k] + 26, b: xs[k + 1] - 26 }));
  return (
    <svg viewBox={`0 0 ${W} 168`} className="picto filiere" role="img"
      aria-label="La filière : l’agriculteur, la coopérative qui collecte, trie et stocke, le conditionneur, puis la cantine ou le magasin">
      <g className="contract-tag">
        <path d={`M${xs[0]},40 L${xs[0]},30 L${xs[1]},30 L${xs[1]},40`} className="bracket" />
        <rect x={(xs[0] + xs[1]) / 2 - 74} y={14} width={148} height={22} rx={3} className="tag-box" />
        <text x={(xs[0] + xs[1]) / 2} y={29} textAnchor="middle" className="tag-text">Contrat avant les semis</text>
      </g>
      {links.map((k, i) => (
        <g key={i}>
          <line x1={k.a} x2={k.b} y1={yLine} y2={yLine} className="link" />
          <g className="mover" style={style({ '--dx': `${k.b - k.a - 18}px`, animationDelay: `${i * 0.9}s` })}>
            {i < 2 ? <Truck x={k.a + 14} y={yLine - 4} /> : <rect x={k.a + 2} y={yLine - 10} width={11} height={9} rx={1.5} className="parcel-box" />}
          </g>
        </g>
      ))}
      {/* Champ de lentilles */}
      <g transform={`translate(${xs[0]},${yIcon})`}>
        <path d="M-24,10 L-14,-14 L24,-14 L14,10 Z" className="field" />
        {[-8, 0, 8].map((dx) => <path key={dx} d={`M${dx - 9},8 L${dx + 1},-12`} className="row" />)}
      </g>
      {/* Coopérative : silo */}
      <g transform={`translate(${xs[1]},${yIcon})`} className="node">
        <path d="M-16,12 L-16,-12 A6,6 0 0 1 -4,-12 L-4,12 Z" /><path d="M-3,12 L-3,-8 A6,6 0 0 1 9,-8 L9,12 Z" />
        <rect x={9} y={-2} width={10} height={14} />
      </g>
      {/* Conditionneur : atelier */}
      <g transform={`translate(${xs[2]},${yIcon})`} className="node">
        <path d="M-18,12 L-18,-4 L-10,-12 L-10,-4 L-2,-12 L-2,-4 L6,-12 L6,-4 L18,-4 L18,12 Z" />
        <rect x={10} y={-16} width={4} height={10} />
      </g>
      {/* Assiette */}
      <g transform={`translate(${xs[3]},${yIcon})`} className="node plate">
        <circle cx={2} cy={0} r={13} className="dish" /><circle cx={2} cy={0} r={8} className="dish-in" />
        <path d="M-17,-12 L-17,12 M-20,-12 L-20,-4 M-14,-12 L-14,-4" className="fork" />
      </g>
      {[['Agriculteur', ''], ['Coopérative', 'collecte, tri, stockage'], ['Conditionneur', 'nettoie, ensache'], ['Cantine, magasin', '']].map(([a, b], i) => (
        <g key={a}>
          <text x={xs[i]} y={118} textAnchor="middle" className="node-l">{a}</text>
          {b && <text x={xs[i]} y={134} textAnchor="middle" className="node-s">{b}</text>}
        </g>
      ))}
    </svg>
  );
}

function Sun() {
  return (
    <g className="sun">
      <circle r={7.5} />
      {Array.from({ length: 8 }, (_, k) => {
        const a = (k * Math.PI) / 4;
        return <line key={k} x1={Math.cos(a) * 11} y1={Math.sin(a) * 11} x2={Math.cos(a) * 15} y2={Math.sin(a) * 15} />;
      })}
    </g>
  );
}
function Storm() {
  return (
    <g className="storm">
      <path d="M-12,2 A6,6 0 0 1 -9,-8 A8,8 0 0 1 6,-9 A6,6 0 0 1 12,2 Z" />
      <path d="M-2,4 L-6,12 L-1,12 L-4,18" className="bolt" />
    </g>
  );
}

/** Dix années : soleil quand la lentille rapporte au moins autant que le blé, orage sinon. */
export function YearsIcons({ wins, total = 10 }: { wins: number; total?: number }) {
  const slot = W / total;
  return (
    <svg viewBox={`0 0 ${W} 48`} className="picto years-icons" role="img"
      aria-label={`${wins} années sur ${total} où la lentille rapporte au moins autant que le blé`}>
      {Array.from({ length: total }, (_, i) => (
        <g key={i} transform={`translate(${slot * i + slot / 2},24)`} className={`yr ${i < wins ? 'win' : 'loss'}`}>
          <rect x={-slot / 2 + 3} y={-21} width={slot - 6} height={42} rx={4} className="yr-bg" />
          <Sun /><Storm />
        </g>
      ))}
    </svg>
  );
}

/** Dix contrats : tenus (coche verte) ou rompus (croix rouge), qui apparaissent l'un après l'autre. */
export function ContractsRow({ held, label, value, delay = 0, total = 10 }: { held: number; label: ReactNode; value: string; delay?: number; total?: number }) {
  const slot = W / total;
  return (
    <div className="contracts-row">
      <div className="cr-head"><span>{label}</span><b className={held / total < 0.5 ? 'bad' : ''}>{value}</b></div>
      <svg viewBox={`0 0 ${W} 50`} className="picto" role="img" aria-label={`${held} contrats tenus sur ${total}`}>
        {Array.from({ length: total }, (_, i) => {
          const ok = i < held;
          return (
            <g key={i} transform={`translate(${slot * i + slot / 2},25)`}>
              <g className={`doc ${ok ? 'ok' : 'ko'}`} style={{ animationDelay: `${delay + i * 120}ms` }}>
                <path d="M-11,-17 L5,-17 L11,-11 L11,17 L-11,17 Z" className="paper" />
                <path d="M5,-17 L5,-11 L11,-11" className="fold" />
                {ok ? <path d="M-6,1 L-1,6 L7,-4" className="mark" /> : <path d="M-5,-4 L5,6 M5,-4 L-5,6" className="mark" />}
              </g>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

/** Jauge horizontale qui se remplit jusqu'à `value` (de 0 à 1). */
export function Gauge({ value, label }: { value: number; label: ReactNode }) {
  return (
    <div className="gauge">
      <div className="gauge-track"><span className="gauge-fill" style={style({ '--w': `${Math.min(100, value * 100)}%` })} /></div>
      <p>{label}</p>
    </div>
  );
}
