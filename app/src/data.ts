// Chargement et typage des exports du pipeline (pipeline/05_export.py).
import parcelsRaw from './data/parcels.json';
import thresholds from './data/thresholds.json';
import supply from './data/supply_curve.json';
import replay from './data/replay.json';
import backtest from './data/backtest.json';
import meta from './data/meta.json';
import contours from './data/contours.json';
import france from './data/france.json';
import lettre from './data/lettre.json';

export type Label = 'mesure' | 'source' | 'suppose' | 'synthetique' | 'modele';

export interface Parcel {
  id: string;
  dep: string;
  culture: 'ble' | 'lentille';
  surface: number;   // ha
  dist: number;      // km jusqu'au site acheteur (détour inclus)
  pRendu: number;    // €/t rendu acheteur au-dessus duquel la parcelle bascule
  tonnes: number;    // tonnes de lentilles attendues
  polygon: [number, number][];
}

type RawParcel = [string, string, 'ble' | 'lentille', number, number, number, number, number[]];

export const parcels: Parcel[] = (parcelsRaw as unknown as RawParcel[]).map((p) => {
  const ring: [number, number][] = [];
  for (let i = 0; i < p[7].length; i += 2) ring.push([p[7][i], p[7][i + 1]]);
  return { id: p[0], dep: p[1], culture: p[2], surface: p[3], dist: p[4], pRendu: p[5], tonnes: p[6], polygon: ring };
});

export { thresholds, supply, replay, backtest, meta, contours, france, lettre };
export type ReplayYear = (typeof replay)[number];

const hyp = meta.hypotheses as Record<string, { valeur: any; etiquette: Label; source: string; url?: string }>;
export const H = {
  chargesBle: hyp.charges_ble_eur_ha.valeur as number,
  chargesLentille: hyp.charges_lentille_eur_ha.valeur as number,
  aide: hyp.aide_couplee_eur_ha.valeur as number,
  rotation: hyp.bonus_rotation_eur_ha.valeur as number,
  kappa: hyp.cout_transport_eur_t_km.valeur as number,
  tau: hyp.fiabilite_visee.valeur as number,
  site: hyp.site_acheteur.valeur as [number, number],
};
export const HYPOTHESES = hyp;

export const DEP_NAMES: Record<string, string> = {
  '77': 'Seine-et-Marne', '78': 'Yvelines', '91': 'Essonne', '95': "Val-d'Oise",
};

export const D77 = thresholds.par_departement.find((d) => d.dep === '77')!;
export const CHALLENGER = (meta as any).challenger_lightgbm as {
  p_star_77: number; importances_q50: { variable: string; part: number }[]; elargissement_conformal: number;
};

export const FEATURE_LABELS: Record<string, string> = {
  tendance: 'Tendance',
  pluie_mj_anom: 'Pluie de mars à juillet',
  pluie_avj_anom: 'Pluie d’avril à juin',
  j30_jj_anom: 'Jours > 30 °C en juin-juillet',
  gel_tardif_anom: 'Gelées tardives',
  pluie_recolte_anom: 'Pluie à la récolte',
  tmax_mj_anom: 'Température maximale',
};
export const MARKET = meta.prix_lentille_observes;

/** Part des années simulées où la lentille bat le blé, au prix donné (Seine-et-Marne). */
export function reliabilityAt(price: number, dep = D77): number {
  const rows = dep.fiabilite_par_prix;
  if (price <= rows[0].prix) return rows[0].fiabilite;
  for (let i = 1; i < rows.length; i++) {
    if (price <= rows[i].prix) {
      const a = rows[i - 1], b = rows[i];
      return a.fiabilite + ((b.fiabilite - a.fiabilite) * (price - a.prix)) / (b.prix - a.prix);
    }
  }
  return rows[rows.length - 1].fiabilite;
}

/** Le contrat a-t-il tenu sur cette parcelle l'année rejouée ? Même règle que le backtest. */
export function held(p: Parcel, price: number, r: ReplayYear): boolean {
  const d = r.par_departement[p.dep as keyof ReplayYear['par_departement']];
  const farm = price - H.kappa * p.dist;
  const margeL = farm * d.rendement_lentille_tha - H.chargesLentille + H.aide + H.rotation;
  const margeB = r.prix_ble * d.rendement_ble_tha - H.chargesBle;
  return margeL >= margeB;
}

export const fmt = (n: number) => Math.round(n).toLocaleString('fr-FR');
export const pct = (x: number) => `${Math.round(x * 100)} %`;
export const signedPct = (x: number) => `${x > 0 ? '+' : x < 0 ? '−' : ''}${Math.abs(Math.round(x * 100))} %`;
export const dec = (x: number, d = 1) => x.toLocaleString('fr-FR', { minimumFractionDigits: d, maximumFractionDigits: d });
