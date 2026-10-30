// Chargement et typage des exports du pipeline (pipeline/05_export.py).
import parcelsRaw from './data/parcels.json';
import thresholds from './data/thresholds.json';
import supply from './data/supply_curve.json';
import replay from './data/replay.json';
import backtest from './data/backtest.json';
import meta from './data/meta.json';
import contours from './data/contours.json';

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

export { thresholds, supply, replay, backtest, meta, contours };

export const H = {
  prixBle: meta.hypotheses.prix_ble_eur_t.valeur as number,
  chargesBle: meta.hypotheses.charges_ble_eur_ha.valeur as number,
  chargesLentille: meta.hypotheses.charges_lentille_eur_ha.valeur as number,
  bonus: meta.hypotheses.bonus_rotation_eur_ha.valeur as number,
  kappa: meta.hypotheses.cout_transport_eur_t_km.valeur as number,
  tau: meta.hypotheses.fiabilite_visee.valeur as number,
  site: meta.site_acheteur as [number, number],
};

export const DEP_NAMES: Record<string, string> = {
  '77': 'Seine-et-Marne', '78': 'Yvelines', '91': 'Essonne', '95': "Val-d'Oise",
};

export const fmt = (n: number) => Math.round(n).toLocaleString('fr-FR');
export const pct = (x: number) => `${Math.round(x * 100)} %`;
