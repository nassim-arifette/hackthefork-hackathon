/** Exploratory procurement on whole parcels; no claim of available industrial capacity. */
export interface SupplyParcel {
  dep: string; culture: string; surface: number; tonnes: number; lon: number; lat: number;
}
export interface SiteCosts { kappa: number; forfait: number; detour: number; qualite: number; tri: number }
export type SiteMode = 'collection' | 'landed';
export interface SiteGeo {
  site: [number, number]; dist: Float64Array; collecte: Float64Array; pRendu: Float64Array;
}
export interface SupplyRequest { volume: number; price: number; mode: SiteMode }
export interface SupplySelection {
  indices: number[]; tonnes: number; ha: number; n: number; km: number; meanKm: number;
  reached: boolean; farmPerT: number; collectionPerT: number; sortingPerT: number;
  landedPerT: number; budget: number; objective: number;
}
const RAD = Math.PI / 180;

export function haversineKm(lon1: number, lat1: number, lon2: number, lat2: number): number {
  const a = Math.sin((lat2 - lat1) * RAD / 2) ** 2
    + Math.cos(lat1 * RAD) * Math.cos(lat2 * RAD) * Math.sin((lon2 - lon1) * RAD / 2) ** 2;
  return 2 * 6371 * Math.asin(Math.sqrt(Math.min(1, Math.max(0, a))));
}

export function makeSiteGeo(parcels: readonly SupplyParcel[], farmPrices: Record<string, number>, costs: SiteCosts, site: [number, number]): SiteGeo {
  if (!(costs.qualite >= 0 && costs.qualite < 1) || costs.kappa < 0 || costs.forfait < 0 || costs.tri < 0 || costs.detour <= 0)
    throw new Error('Invalid transport or acceptance assumptions');
  const dist = new Float64Array(parcels.length), collecte = new Float64Array(parcels.length), pRendu = new Float64Array(parcels.length);
  parcels.forEach((p, i) => {
    dist[i] = haversineKm(p.lon, p.lat, site[0], site[1]) * costs.detour;
    // Transport is invoiced on gross tonnes; prices and expected parcel tonnes are net.
    collecte[i] = (costs.forfait + costs.kappa * dist[i]) / (1 - costs.qualite);
    pRendu[i] = (farmPrices[p.dep] ?? Infinity) + collecte[i];
  });
  return { site, dist, collecte, pRendu };
}

/** The same evaluator is used for the map, current site, and every candidate.
 * Whole parcels are taken in increasing unit-cost order. This is a transparent
 * procurement rule, not a solution of the indivisible-parcel knapsack problem. */
export function selectSupply(parcels: readonly SupplyParcel[], geo: SiteGeo, costs: SiteCosts, request: SupplyRequest): SupplySelection {
  if (!(request.volume > 0) || !Number.isFinite(request.volume) || !Number.isFinite(request.price)) throw new Error('Invalid supply request');
  const eligible: number[] = [];
  parcels.forEach((p, i) => {
    if (p.culture === 'ble' && p.tonnes > 0 && Number.isFinite(geo.pRendu[i])
      && (request.mode === 'landed' || request.price >= geo.pRendu[i])) eligible.push(i);
  });
  const order = request.mode === 'landed' ? geo.pRendu : geo.dist;
  eligible.sort((a, b) => order[a] - order[b] || a - b);
  const indices: number[] = [];
  let tonnes = 0, ha = 0, km = 0, tkm = 0, collection = 0, farm = 0;
  for (const i of eligible) {
    if (tonnes >= request.volume) break;
    const p = parcels[i];
    indices.push(i); tonnes += p.tonnes; ha += p.surface; km = Math.max(km, geo.dist[i]);
    tkm += p.tonnes * geo.dist[i]; collection += p.tonnes * geo.collecte[i];
    // A delivered quote already includes transport: deduct it once to recover farm payment.
    farm += p.tonnes * ((request.mode === 'landed' ? geo.pRendu[i] : request.price) - geo.collecte[i]);
  }
  const reached = tonnes >= request.volume;
  const collectionPerT = tonnes ? collection / tonnes : 0, farmPerT = tonnes ? farm / tonnes : 0;
  const sortingPerT = costs.tri / (1 - costs.qualite);
  const landedPerT = farmPerT + collectionPerT + sortingPerT;
  return { indices, tonnes, ha, n: indices.length, km, meanKm: tonnes ? tkm / tonnes : 0, reached,
    farmPerT, collectionPerT, sortingPerT, landedPerT, budget: tonnes * landedPerT,
    objective: reached ? (request.mode === 'landed' ? landedPerT : collectionPerT) : Infinity };
}

export interface SiteSearchResult { site: [number, number]; selection: SupplySelection; evaluated: number; improved: boolean }

/** Exact evaluation of a grid refined twice, including the current site.
 * Feasibility and the objective cannot deteriorate relative to a feasible current site.
 * The result is the best tested candidate, not a global location optimum. */
export async function searchSites(parcels: readonly SupplyParcel[], farmPrices: Record<string, number>, costs: SiteCosts,
  request: SupplyRequest, current: SiteGeo, yieldControl: () => Promise<void> = async () => {}): Promise<SiteSearchResult> {
  const initial = selectSupply(parcels, current, costs, request);
  let best: SiteSearchResult = { site: current.site, selection: initial, evaluated: 1, improved: false };
  const wheat = parcels.filter((p) => p.culture === 'ble' && p.tonnes > 0 && Number.isFinite(farmPrices[p.dep]));
  if (wheat.reduce((s, p) => s + p.tonnes, 0) < request.volume) return best;
  const bounds = wheat.reduce((b, p) => [Math.min(b[0], p.lon), Math.max(b[1], p.lon), Math.min(b[2], p.lat), Math.max(b[3], p.lat)], [Infinity, -Infinity, Infinity, -Infinity]);
  const scan = async (lo0: number, lo1: number, la0: number, la1: number, dx: number, dy: number) => {
    for (let lo = lo0; lo <= lo1 + 1e-10; lo += dx) for (let la = la0; la <= la1 + 1e-10; la += dy) {
      const site: [number, number] = [Math.round(lo * 1e5) / 1e5, Math.round(la * 1e5) / 1e5];
      const selection = selectSupply(parcels, makeSiteGeo(parcels, farmPrices, costs, site), costs, request);
      best.evaluated++;
      if (selection.objective < best.selection.objective - 1e-10) best = { ...best, site, selection };
      if (best.evaluated % 24 === 0) await yieldControl();
    }
  };
  await scan(bounds[0], bounds[1], bounds[2], bounds[3], 0.06, 0.04);
  if (best.selection.reached) {
    const [a, b] = best.site;
    await scan(a - 0.06, a + 0.06, b - 0.04, b + 0.04, 0.01, 0.007);
    const [c, d] = best.site;
    await scan(c - 0.01, c + 0.01, d - 0.007, d + 0.007, 0.002, 0.0014);
  }
  best.improved = best.selection.objective < initial.objective - 1e-10;
  return best;
}
