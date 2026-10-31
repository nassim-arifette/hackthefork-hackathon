// Simulateur : le calcul du prix garanti et du barème, refait dans le navigateur avec les chiffres
// de la coopérative, sur les mêmes 20 000 années simulées que le pipeline (07_contrats.py).
// Mêmes formules que pipeline/model.py : p_star, paiement, protection, calibrer_premier_palier.
// Avec les hypothèses par défaut, on retrouve exactement P* et la première tranche exportés (test).
import simRaw from './data/simulateur.json';
import { parcels, type SiteGeo } from './data';

interface RawSim {
  dep: string; n: number;
  defauts: { charges_ble: number; charges_lentille: number; aide: number; rotation: number; qualite: number; tau: number };
  suite_paliers: number[]; bornes: number[];
  reference: { p_star: number; paliers: number[] };
  yL: number[]; yW: number[]; pB: number[];
}
const S = simRaw as unknown as RawSim;
const YL = Float64Array.from(S.yL), YW = Float64Array.from(S.yW), PB = Float64Array.from(S.pB);
const N = YL.length;

export interface SimParams {
  chargesBle: number;      // €/ha
  chargesLentille: number; // €/ha
  aide: number;            // aide couplée, €/ha
  rotation: number;        // bénéfice de rotation pour le blé suivant, €/ha
  qualite: number;         // part de la récolte refusée au tri (0-1)
  tau: number;             // protection visée : part des années où la lentille bat le blé
}
export const SIM_DEFAUTS: SimParams = {
  chargesBle: S.defauts.charges_ble, chargesLentille: S.defauts.charges_lentille, aide: S.defauts.aide,
  rotation: S.defauts.rotation, qualite: S.defauts.qualite, tau: S.defauts.tau,
};
export const SIM_REFERENCE = S.reference;
export const SIM_DEP = S.dep;
const SUITE = S.suite_paliers as [number, number];
const [B1, B2] = S.bornes;

/** Quantile empirique « inverted_cdf » (numpy) : plus petite valeur atteinte dans une part tau des cas. */
function quantile(sorted: Float64Array, tau: number): number {
  const k = Math.min(sorted.length - 1, Math.max(0, Math.ceil(sorted.length * tau - 1e-9) - 1));
  return sorted[k];
}

function payePaliers(p1: number, y: number): number {
  return p1 * Math.min(y, B1) + SUITE[0] * Math.min(Math.max(y - B1, 0), B2 - B1) + SUITE[1] * Math.max(y - B2, 0);
}

export interface Agri { ecart: number; gain: number; perte: number; protection: number }
export interface SimResult {
  pStar: number;                       // prix unique nécessaire, €/t acceptée, départ ferme
  paliers: [number, number, number];   // barème par tranches calibré pour la même protection
  coutUnique: number;                  // €/t acceptée
  coutPaliers: number;                 // €/t acceptée, moyenne des années simulées
  margeBle: number;                    // marge moyenne du blé, €/ha
  rendementAccepte: number;            // t/ha acceptées en moyenne
  agriUnique: Agri;
  agriPaliers: Agri;
}

export function simuler(p: SimParams): SimResult {
  const bonus = p.aide + p.rotation, q = p.qualite;
  const acc = new Float64Array(N), mb = new Float64Array(N), R = new Float64Array(N);
  let sAcc = 0, sMb = 0;
  for (let i = 0; i < N; i++) {
    acc[i] = YL[i] * (1 - q);
    mb[i] = PB[i] * YW[i] - p.chargesBle;
    R[i] = (mb[i] + p.chargesLentille - bonus) / acc[i];
    sAcc += acc[i]; sMb += mb[i];
  }
  const pStar = Math.round(quantile(R.slice().sort(), p.tau));

  // Écart de marge lentille − blé de la même année, pour un contrat donné par sa fonction de paiement.
  const agri = (paye: (y: number) => number): Agri & { verse: number } => {
    let s = 0, gain = 0, nG = 0, perte = 0, nP = 0, verse = 0;
    for (let i = 0; i < N; i++) {
      const v = paye(acc[i]);
      const e = v - p.chargesLentille + bonus - mb[i];
      verse += v; s += e;
      if (e >= 0) { gain += e; nG++; } else { perte -= e; nP++; }
    }
    return { ecart: s / N, gain: nG ? gain / nG : 0, perte: nP ? perte / nP : 0, protection: nG / N, verse: verse / N };
  };

  // Première tranche : plus petit prix entier qui atteint la protection visée (recherche par dichotomie).
  const protege = (p1: number) => {
    let ok = 0;
    for (let i = 0; i < N; i++) if (payePaliers(p1, acc[i]) - p.chargesLentille + bonus >= mb[i]) ok++;
    return ok / N >= p.tau;
  };
  let lo = 0, hi = 20000;
  while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (protege(mid)) hi = mid; else lo = mid; }
  const p1 = hi;

  const u = agri((y) => pStar * y);
  const t = agri((y) => payePaliers(p1, y));
  const strip = ({ verse: _v, ...a }: Agri & { verse: number }): Agri => a;
  return {
    pStar, paliers: [p1, SUITE[0], SUITE[1]],
    coutUnique: pStar, coutPaliers: t.verse / (sAcc / N),
    margeBle: sMb / N, rendementAccepte: sAcc / N,
    agriUnique: strip(u), agriPaliers: strip(t),
  };
}

/** Parcelles de blé les plus proches du site, jusqu'au volume de lentilles acceptées visé. Les tonnes
 *  exportées supposent la part refusée par défaut : elles sont recalculées pour celle de la coopérative. */
export function parcellesPour(geo: SiteGeo, volume: number, qualite: number) {
  const k = (1 - qualite) / (1 - SIM_DEFAUTS.qualite);
  const idx = parcels.map((_, i) => i).filter((i) => parcels[i].culture === 'ble').sort((a, b) => geo.dist[a] - geo.dist[b]);
  const out: number[] = [];
  let t = 0, ha = 0, tkm = 0, km = 0;
  for (const i of idx) {
    if (t >= volume) break;
    const ti = parcels[i].tonnes * k;
    out.push(i); t += ti; ha += parcels[i].surface; tkm += ti * geo.dist[i]; km = geo.dist[i];
  }
  return { idx: out, n: out.length, ha, km, meanKm: t ? tkm / t : 0, tonnes: t, reached: t >= volume };
}
