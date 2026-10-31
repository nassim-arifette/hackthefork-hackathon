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
import contrats from './data/contrats.json';
import sentinelRaw from './data/sentinel.json';

export type Label = 'mesure' | 'source' | 'suppose' | 'synthetique' | 'modele';

export interface Parcel {
  id: string;
  dep: string;
  culture: 'ble' | 'lentille';
  surface: number;   // ha
  tonnes: number;    // tonnes de lentilles acceptées attendues
  polygon: [number, number][];
  lon: number;       // point représentatif
  lat: number;
}

type RawParcel = [string, string, 'ble' | 'lentille', number, number, number, number, number[], number, number];

export const parcels: Parcel[] = (parcelsRaw as unknown as RawParcel[]).map((p) => {
  const ring: [number, number][] = [];
  for (let i = 0; i < p[7].length; i += 2) ring.push([p[7][i], p[7][i + 1]]);
  return { id: p[0], dep: p[1], culture: p[2], surface: p[3], tonnes: p[6], polygon: ring, lon: p[8], lat: p[9] };
});

export { thresholds, supply, replay, backtest, meta, contours, france, lettre, contrats };
export type ReplayYear = (typeof replay)[number];

const hyp = meta.hypotheses as Record<string, { valeur: any; etiquette: Label; source: string; url?: string }>;
export const H = {
  chargesBle: hyp.charges_ble_eur_ha.valeur as number,
  chargesLentille: hyp.charges_lentille_eur_ha.valeur as number,
  aide: hyp.aide_couplee_eur_ha.valeur as number,
  rotation: hyp.bonus_rotation_eur_ha.valeur as number,
  kappa: hyp.cout_transport_eur_t_km.valeur as number,
  detour: hyp.facteur_detour_route.valeur as number,
  forfait: hyp.forfait_collecte_eur_t.valeur as number,
  qualite: hyp.part_non_valorisee.valeur as number,
  tau: hyp.fiabilite_visee.valeur as number,
  site: hyp.site_acheteur.valeur as [number, number],
  volumes: { pilote: hyp.volume_pilote_t.valeur as number, ambition: hyp.volume_vise_t.valeur as number },
  impact: {
    proteines: hyp.proteines_part.valeur as number,
    azote: hyp.azote_ble_kg_ha.valeur as number,
    co2e: hyp.co2e_t_par_ha.valeur as number,
  },
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

// ---------- suivi en saison (pipeline/08_sentinel.py) ----------
export type Statut = 'conforme' | 'a_surveiller' | 'en_retard';
export interface SuiviParcel {
  id: string; lettre: string; dep: string; surface: number; distKm: number; lon: number; lat: number;
  statut: Statut; ecart: number; datesValides: number; datesVues: number;
  serie: { day: number; ndvi: number }[];
}
const DAY0 = Date.parse(sentinelRaw.periode[0]);
export const dayOf = (iso: string) => Math.round((Date.parse(iso) - DAY0) / 864e5);
export const dateOf = (day: number) => new Date(DAY0 + day * 864e5);
export const SAISON = {
  annee: sentinelRaw.saison,
  jours: dayOf(sentinelRaw.periode[1]),
  fenetre: sentinelRaw.fenetre_ecart.map(dayOf) as [number, number],
  seuils: sentinelRaw.seuils_statut,
  nImages: sentinelRaw.n_images,
  partValide: sentinelRaw.seuil_part_valide,
  reference: (sentinelRaw.reference as [string, number][]).map(([d, v]) => ({ day: dayOf(d), ndvi: v })),
};
const PARCEL_BY_ID = new Map(parcels.map((p, i) => [p.id, i]));
export const SUIVI: SuiviParcel[] = sentinelRaw.parcelles.map((p, k) => {
  const q = parcels[PARCEL_BY_ID.get(p.id)!];
  return {
    id: p.id, lettre: String.fromCharCode(65 + k), dep: p.dep, surface: p.surface_ha, distKm: p.dist_km,
    lon: q.lon, lat: q.lat, statut: p.statut as Statut, ecart: p.ecart_floraison,
    datesValides: p.dates_valides, datesVues: p.dates_vues,
    serie: (p.serie as [string, number][]).map(([d, v]) => ({ day: dayOf(d), ndvi: v })),
  };
});
export const SUIVI_INDEX = new Set(SUIVI.map((p) => PARCEL_BY_ID.get(p.id)!));

/** NDVI interpolé au jour donné, entre les dates valides (constant avant la première et après la dernière). */
export function ndviAt(serie: { day: number; ndvi: number }[], day: number): number {
  if (day <= serie[0].day) return serie[0].ndvi;
  for (let k = 1; k < serie.length; k++) {
    if (day <= serie[k].day) {
      const a = serie[k - 1], b = serie[k];
      return a.ndvi + ((b.ndvi - a.ndvi) * (day - a.day)) / (b.day - a.day);
    }
  }
  return serie[serie.length - 1].ndvi;
}

/** Contrats comparés (pipeline/07_contrats.py) : existants, puis calibrés pour 8 années sur 10. */
export const CONTRATS = {
  existants: contrats.existants,
  calibres: Object.fromEntries(contrats.calibres.map((c) => [c.id, c])) as Record<'unique' | 'paliers' | 'prime_ha', (typeof contrats.calibres)[number]>,
  yFaible: contrats.rendement_accepte_annee_faible_tha,
};

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

// ---------- site de collecte ----------
const P_STAR_DEP: Record<string, number> = Object.fromEntries(thresholds.par_departement.map((d) => [d.dep, d.p_star]));
const RAD = Math.PI / 180;

function haversineKm(lon1: number, lat1: number, lon2: number, lat2: number): number {
  const a = Math.sin(((lat2 - lat1) * RAD) / 2) ** 2
    + Math.cos(lat1 * RAD) * Math.cos(lat2 * RAD) * Math.sin(((lon2 - lon1) * RAD) / 2) ** 2;
  return 2 * 6371 * Math.asin(Math.sqrt(a));
}

/** Distances au site (km routiers approchés) et prix rendu de bascule de chaque parcelle. Même calcul que 05_export.py. */
export interface SiteGeo { site: [number, number]; dist: Float64Array; pRendu: Float64Array }
export function siteGeo(site: [number, number]): SiteGeo {
  const n = parcels.length, dist = new Float64Array(n), pRendu = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    const p = parcels[i];
    dist[i] = haversineKm(p.lon, p.lat, site[0], site[1]) * H.detour;
    pRendu[i] = P_STAR_DEP[p.dep] + H.forfait + H.kappa * dist[i];
  }
  return { site, dist, pRendu };
}
export const SITE_SCENARIO = siteGeo(H.site);

/** Courbe d'offre : hectares et tonnes de blé qui basculent à chaque prix rendu, de 400 à 3 000 €/t. */
export function supplyCurve(geo: SiteGeo) {
  const idx = parcels.map((_, i) => i).filter((i) => parcels[i].culture === 'ble').sort((a, b) => geo.pRendu[a] - geo.pRendu[b]);
  const out: { prix: number; tonnes: number; hectares: number; parcelles: number }[] = [];
  let j = 0, t = 0, ha = 0;
  for (let q = 400; q <= 3000; q += 10) {
    while (j < idx.length && geo.pRendu[idx[j]] <= q) { t += parcels[idx[j]].tonnes; ha += parcels[idx[j]].surface; j++; }
    out.push({ prix: q, tonnes: Math.round(t), hectares: Math.round(ha), parcelles: j });
  }
  return out;
}

/** Distance moyenne (km routiers), pondérée par les tonnes, des parcelles de blé les plus proches
 *  qu'il faut réunir pour atteindre le volume. Recherche rapide par tranches de 250 m. */
const WHEAT = parcels.map((p, i) => ({ p, i })).filter(({ p }) => p.culture === 'ble');
const W_LON = Float64Array.from(WHEAT, ({ p }) => p.lon), W_LAT = Float64Array.from(WHEAT, ({ p }) => p.lat);
const W_T = Float64Array.from(WHEAT, ({ p }) => p.tonnes);
function meanKmFor(site: [number, number], volume: number): number {
  const B = 400, step = 0.25, tB = new Float64Array(B), tdB = new Float64Array(B);
  const kx = 111.32 * Math.cos(site[1] * RAD), ky = 110.57;
  for (let k = 0; k < W_T.length; k++) {
    const d = Math.hypot((W_LON[k] - site[0]) * kx, (W_LAT[k] - site[1]) * ky) * H.detour;
    const b = Math.min(B - 1, Math.floor(d / step));
    tB[b] += W_T[k]; tdB[b] += W_T[k] * d;
  }
  let t = 0, td = 0;
  for (let b = 0; b < B && t < volume; b++) {
    const take = Math.min(1, (volume - t) / (tB[b] || 1));
    t += tB[b] * take; td += tdB[b] * take;
  }
  return t ? td / t : Infinity;
}

/** Meilleur point de collecte pour le volume, sur une grille de candidats affinée deux fois. */
export function bestSite(volume: number): { site: [number, number]; km: number } {
  let lonMin = Infinity, lonMax = -Infinity, latMin = Infinity, latMax = -Infinity;
  for (let k = 0; k < W_LON.length; k++) {
    lonMin = Math.min(lonMin, W_LON[k]); lonMax = Math.max(lonMax, W_LON[k]);
    latMin = Math.min(latMin, W_LAT[k]); latMax = Math.max(latMax, W_LAT[k]);
  }
  let best = { site: [lonMin, latMin] as [number, number], km: Infinity };
  const scan = (lo0: number, lo1: number, la0: number, la1: number, dLon: number, dLat: number) => {
    for (let lo = lo0; lo <= lo1; lo += dLon)
      for (let la = la0; la <= la1; la += dLat) {
        const km = meanKmFor([lo, la], volume);
        if (km < best.km) best = { site: [lo, la], km };
      }
  };
  scan(lonMin, lonMax, latMin, latMax, 0.06, 0.04);
  const [a, b] = best.site;
  scan(a - 0.06, a + 0.06, b - 0.04, b + 0.04, 0.01, 0.007);
  const [c, d] = best.site;
  scan(c - 0.01, c + 0.01, d - 0.007, d + 0.007, 0.002, 0.0014);
  return { site: [Math.round(best.site[0] * 1e5) / 1e5, Math.round(best.site[1] * 1e5) / 1e5], km: best.km };
}

/** Le contrat a-t-il tenu sur cette parcelle l'année rejouée ? Même règle que le backtest. */
export function held(p: Parcel, dist: number, price: number, r: ReplayYear): boolean {
  const d = r.par_departement[p.dep as keyof ReplayYear['par_departement']];
  const farm = price - H.forfait - H.kappa * dist;
  // Le prix garanti est payé sur les tonnes acceptées au tri.
  const margeL = farm * d.rendement_lentille_tha * (1 - H.qualite) - H.chargesLentille + H.aide + H.rotation;
  const margeB = r.prix_ble * d.rendement_ble_tha - H.chargesBle;
  return margeL >= margeB;
}

// Signe moins typographique et espace insécable avant « % » : affichage homogène.
export const fmt = (n: number) => Math.round(n).toLocaleString('fr-FR').replace('-', '\u2212');
export const pct = (x: number) => `${Math.round(x * 100)}\u00a0%`;
/** Pourcentage avec une décimale sous 10 % (0,8 % plutôt que 1 %). */
export const pctFine = (x: number) => (x < 0.1 ? `${dec(x * 100, 1)}\u00a0%` : pct(x));
export const signedPct = (x: number) => `${x > 0 ? '+' : x < 0 ? '−' : ''}${Math.abs(Math.round(x * 100))}\u00a0%`;
export const dec = (x: number, d = 1) => x.toLocaleString('fr-FR', { minimumFractionDigits: d, maximumFractionDigits: d }).replace('-', '\u2212');
