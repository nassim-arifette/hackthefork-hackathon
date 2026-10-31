import { useEffect, useMemo, useRef, useState } from 'react';
import DeckGL from '@deck.gl/react';
import { FlyToInterpolator, MapView, type MapViewState } from '@deck.gl/core';
import { GeoJsonLayer, IconLayer, LineLayer, PolygonLayer, ScatterplotLayer, TextLayer } from '@deck.gl/layers';
import {
  BT_BY_YEAR, contours, DEP_NAMES, france, held, MAILLON, maillonCat, meta, ndviAt, parcels, SUIVI, SUIVI_INDEX, thresholds,
  type MaillonCat, type MaillonParcel, type MaillonVersion, type Parcel, type ReplayYear, type SiteGeo, type TruckTrip,
} from '../data';
import { ICON_ATLAS, ICON_MAPPING, type IconName } from './icons';

type RGB = [number, number, number];
// Mêmes valeurs que les jetons de docs/DESIGN.md.
const C = {
  land: [236, 238, 231] as RGB,
  landOut: [244, 245, 241] as RGB,
  border: [255, 255, 255] as RGB,
  ink: [29, 33, 28] as RGB,
  wheat: [200, 150, 47] as RGB,
  wheatHit: [226, 205, 158] as RGB,
  wheatDim: [222, 206, 170] as RGB,
  lentil: [47, 106, 80] as RGB,
  slate: [91, 115, 133] as RGB,
  fail: [181, 67, 44] as RGB,
  rule2: [198, 203, 192] as RGB,
};

// Étape « Vu du ciel » : jugée hors des blocs connus, ou bloc connu du collecteur.
const MAILLON_COLOR: Record<MaillonCat, RGB> = {
  repere: C.lentil, manque: C.slate, fausse: C.wheat, autre: C.wheatDim,
  connu_legume: [157, 184, 166], connu_autre: C.rule2, non_classe: C.landOut,
};
const [ZW, ZS, ZE, ZN] = MAILLON.zone;
const ZONE_RING: [number, number][] = [[ZW, ZS], [ZE, ZS], [ZE, ZN], [ZW, ZN], [ZW, ZS]];

const surf = meta.surface_lentille_par_dep_2025 as Record<string, number>;
// Prix plancher pour 8 années sur 10 dans chaque département producteur classé (même calcul qu'en Seine-et-Marne).
const PSTAR_FR = Object.fromEntries((meta.france as { dep: string; p_star: number }[]).map((d) => [d.dep, d.p_star]));
// Agreste publie parfois un seul rendement pour plusieurs départements : ceux-là prennent, en teinte pâle,
// le prix calculé pour le département qui les représente.
const NOM_CODE = Object.fromEntries((france as any).features.map((f: any) => [f.properties.nom, f.properties.code]));
const AVEC_FR: Record<string, { rep: string; p: number }> = {};
for (const d of meta.france as { nom: string; p_star: number; avec: string[] }[]) {
  for (const n of d.avec) if (NOM_CODE[n]) AVEC_FR[NOM_CODE[n]] = { rep: d.nom, p: d.p_star };
}
const PS_VALUES = Object.values(PSTAR_FR);
export const PSTAR_RANGE: [number, number] = [Math.min(...PS_VALUES), Math.max(...PS_VALUES)];
const surfMax = Math.max(...Object.values(surf));
const IDF_CODES = ['75', '77', '78', '91', '92', '93', '94', '95'];
const reduce = typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

function mix(a: RGB, b: RGB, t: number): RGB {
  return [0, 1, 2].map((i) => Math.round(a[i] + (b[i] - a[i]) * t)) as RGB;
}

function centroid(geom: any): [number, number] {
  const ring = geom.type === 'Polygon' ? geom.coordinates[0] : geom.coordinates[0][0];
  let x = 0, y = 0;
  for (const [a, b] of ring) { x += a; y += b; }
  return [x / ring.length, y / ring.length];
}

const DEP_LABELS = (contours as any).features.map((f: any) => {
  const d = thresholds.par_departement.find((t) => t.dep === f.properties.code)!;
  return { pos: centroid(f.geometry), name: DEP_NAMES[f.properties.code], pStar: d.p_star };
});

const SUIVI_CENTER = [SUIVI.reduce((a, p) => a + p.lon, 0) / SUIVI.length, SUIVI.reduce((a, p) => a + p.lat, 0) / SUIVI.length];
// Deux parcelles voisines : la lettre de la seconde passe à gauche du point.
const SUIVI_LEFT = new Set(SUIVI.filter((p, k) => SUIVI.slice(0, k).some((q) => Math.abs(q.lon - p.lon) < 0.01 && Math.abs(q.lat - p.lat) < 0.006)).map((p) => p.id));

// Illustration des importations : des cargos qui rejoignent quatre ports (aucune origine n'est affirmée).
const BOATS: TruckTrip[] = [
  { from: [-6.8, 50.25], to: [0.1, 49.47], delay: 0, dur: 6800, tonnes: 0 },
  { from: [-7.4, 46.4], to: [-2.25, 47.25], delay: 1500, dur: 6200, tonnes: 0 },
  { from: [6.6, 41.6], to: [4.86, 43.32], delay: 700, dur: 5600, tonnes: 0 },
  { from: [0.6, 52.5], to: [2.36, 51.06], delay: 2600, dur: 5400, tonnes: 0 },
];

export type Camera = 'france' | 'idf' | 'suivi' | 'ciel' | 'site';
export type FranceMode = 'surface' | 'backtest' | 'pstar' | 'plain';

function viewFor(target: Camera, width: number, site: [number, number], radiusKm: number): MapViewState {
  const w = Math.max(360, width);
  const z = Math.log2(w / 1000);
  switch (target) {
    case 'france': return { longitude: 2.45, latitude: 46.6, zoom: 4.95 + z, pitch: 0, bearing: 0 };
    case 'suivi': return { longitude: SUIVI_CENTER[0], latitude: SUIVI_CENTER[1], zoom: 10.3 + z, pitch: 0, bearing: 0 };
    case 'ciel': return { longitude: (ZW + ZE) / 2, latitude: (ZS + ZN) / 2, zoom: 10.35 + z, pitch: 0, bearing: 0 };
    case 'site': {
      // Le rayon de la collecte occupe environ un tiers de la largeur de la carte.
      const metersPerPixel = (radiusKm * 1000) / (0.33 * w);
      const zoom = Math.log2((40075016 * Math.cos((site[1] * Math.PI) / 180)) / (512 * metersPerPixel));
      return { longitude: site[0], latitude: site[1], zoom: Math.max(8.2, Math.min(12, zoom)), pitch: 0, bearing: 0 };
    }
    default: return { longitude: 2.48, latitude: 48.64, zoom: 8.05 + z, pitch: 0, bearing: 0 };
  }
}

// Rampe de NDVI : sol nu (0,15) vers végétation dense (0,9).
const NDVI_LO: RGB = [226, 214, 182], NDVI_HI: RGB = [33, 92, 63];
const ndviColor = (v: number): RGB => mix(NDVI_LO, NDVI_HI, Math.max(0, Math.min(1, (v - 0.15) / 0.75)));
const ease = (p: number) => p * p * (3 - 2 * p);
const PAUSE_MS = 1800;

/** Position de chaque trajet à l'instant `t` : départ échelonné, aller simple, pause, puis on recommence. */
function moving(trips: TruckTrip[], t: number): { pos: [number, number]; icon: IconName }[] {
  const out: { pos: [number, number]; icon: IconName }[] = [];
  for (const tr of trips) {
    const local = t - tr.delay;
    if (local < 0) continue;
    const ph = local % (tr.dur + PAUSE_MS);
    if (ph > tr.dur) continue;
    const p = ease(ph / tr.dur);
    out.push({
      pos: [tr.from[0] + (tr.to[0] - tr.from[0]) * p, tr.from[1] + (tr.to[1] - tr.from[1]) * p],
      icon: tr.to[0] >= tr.from[0] ? 'truckR' : 'truckL',
    });
  }
  return out;
}

export type Hover = { kind: 'parcel'; p: Parcel; i: number } | { kind: 'dep'; name: string; surface: number; pStar?: number; pstarMode?: boolean; avec?: { rep: string; p: number } }
  | { kind: 'maillon'; p: MaillonParcel; cat: MaillonCat } | null;

interface Props {
  camera: Camera;
  /** Caméra « site » : rayon de la collecte à montrer, en km. */
  radiusKm?: number;
  showParcels: boolean;
  franceMode: FranceMode;
  /** Carte de France du backtest : année affichée. */
  btYear?: number | null;
  depLabels?: boolean;
  price: number;
  year: ReplayYear | null;
  /** Parcelles du contrat : distance maximale des parcelles retenues pour le volume visé. */
  selectKm: number | null;
  onHover: (h: Hover) => void;
  /** Distances et prix rendu de chaque parcelle pour le site de collecte courant. */
  geo: SiteGeo;
  /** Si fourni, un clic sur la carte déplace le site de collecte. */
  onPickSite?: (site: [number, number]) => void;
  /** Étape « La saison » : jour du replay, et parcelle mise en avant. */
  season: number | null;
  focus: string | null;
  /** Étape « Vu du ciel » : version affichée (images jusqu'au 10 juin, ou saison complète). */
  maillon: MaillonVersion | null;
  /** Silo de la coopérative au site de collecte. */
  silo?: boolean;
  /** Camions des parcelles vers le silo ; la clé relance l'animation. */
  trucks?: { key: string; trips: TruckTrip[] } | null;
  boats?: boolean;
  /** Part des tonnes déjà arrivées au silo, au premier passage des camions. */
  onDelivered?: (fraction: number) => void;
}

export default function MapScene({
  camera, radiusKm = 6, showParcels, franceMode, btYear = null, depLabels = false, price, year, selectKm, onHover, geo,
  onPickSite, season, focus, maillon, silo = false, trucks = null, boats = false, onDelivered,
}: Props) {
  const box = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(1000);
  const [fontsReady, setFontsReady] = useState(false);
  const targetKey = camera === 'site' ? `site:${radiusKm.toFixed(1)}:${geo.site.join(',')}` : camera;
  const [viewState, setViewState] = useState<MapViewState>(viewFor('france', 1000, geo.site, radiusKm));
  // Seul un changement de vue anime la caméra. Une largeur mesurée tardivement s'applique sans
  // transition : sinon la dernière image de cette transition peut écraser la suivante.
  const shownTarget = useRef(targetKey);

  useEffect(() => {
    const el = box.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setWidth(el.clientWidth));
    ro.observe(el);
    document.fonts?.ready.then(() => setFontsReady(true));
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    const animate = shownTarget.current !== targetKey;
    shownTarget.current = targetKey;
    const v = viewFor(camera, width, geo.site, radiusKm);
    setViewState(animate
      ? { ...v, transitionDuration: 1800, transitionInterpolator: new FlyToInterpolator({ speed: 1.6 }) } as MapViewState
      : v);
    // La clé de vue résume caméra, rayon et site : pas besoin de les lister à part.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [targetKey, width]);

  // Horloge des animations (camions, bateaux), environ 30 images par seconde, relancée à chaque scène.
  const animKey = trucks ? `t:${trucks.key}` : boats ? 'boats' : null;
  const [clock, setClock] = useState(0);
  useEffect(() => {
    setClock(0);
    if (!animKey || reduce) return;
    let raf = 0, last = -1;
    const t0 = performance.now();
    const tick = (now: number) => {
      if (now - last >= 33) { last = now; setClock(Math.max(0, now - t0)); }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [animKey]);

  const totalT = useMemo(() => (trucks ? trucks.trips.reduce((a, t) => a + t.tonnes, 0) : 0), [trucks]);
  const arrivedT = useMemo(() => {
    if (!trucks) return 0;
    if (reduce) return totalT;
    let s = 0;
    for (const t of trucks.trips) if (clock >= t.delay + t.dur) s += t.tonnes;
    return s;
  }, [trucks, clock, totalT]);
  useEffect(() => { onDelivered?.(totalT ? arrivedT / totalT : 0); }, [arrivedT, totalT, onDelivered]);

  const layers = useMemo(() => {
    const lentil = (i: number) => price >= geo.pRendu[i];
    const font = '"Archivo Variable", Archivo, system-ui, sans-serif';
    const btMap = btYear ? BT_BY_YEAR[btYear] : undefined;
    return [
      new GeoJsonLayer({
        id: 'france', data: france as any, stroked: true, filled: true, pickable: !showParcels && (franceMode === 'surface' || franceMode === 'pstar'),
        getFillColor: (f: any) => {
          if (showParcels) return C.landOut;
          if (franceMode === 'backtest') {
            const r = btMap?.[f.properties.code];
            return r === undefined ? C.land : r ? C.lentil : C.fail;
          }
          if (franceMode === 'pstar') {
            const code = f.properties.code, v = PSTAR_FR[code] ?? AVEC_FR[code]?.p;
            if (v === undefined) return C.land;
            // Vert foncé là où la lentille bat le blé à bas prix, clair là où il faut payer cher.
            const c = mix(C.lentil, [214, 226, 218], (v - PSTAR_RANGE[0]) / (PSTAR_RANGE[1] - PSTAR_RANGE[0]));
            return PSTAR_FR[code] === undefined ? mix(c, C.land, 0.55) : c;
          }
          if (franceMode === 'plain') return C.land;
          const s = surf[f.properties.code] ?? 0;
          return s > 0 ? mix(C.land, C.lentil, 0.12 + 0.88 * Math.sqrt(s / surfMax)) : C.land;
        },
        getLineColor: (f: any) => (!showParcels && franceMode === 'surface' && IDF_CODES.includes(f.properties.code) ? C.ink : C.border),
        getLineWidth: (f: any) => (!showParcels && franceMode === 'surface' && IDF_CODES.includes(f.properties.code) ? 1.6 : 1),
        lineWidthUnits: 'pixels',
        updateTriggers: { getFillColor: [showParcels, franceMode, btYear], getLineColor: [showParcels, franceMode], getLineWidth: [showParcels, franceMode] },
        transitions: { getFillColor: 350 },
        onHover: (info: any) => {
          if (showParcels || (franceMode !== 'surface' && franceMode !== 'pstar')) return;
          const c = info.object?.properties.code;
          onHover(info.object ? { kind: 'dep', name: info.object.properties.nom, surface: surf[c] ?? 0, pStar: franceMode === 'pstar' ? PSTAR_FR[c] : undefined, pstarMode: franceMode === 'pstar', avec: AVEC_FR[c] } : null);
        },
      }),
      new GeoJsonLayer({
        id: 'idf', data: contours as any, stroked: true, filled: true, visible: showParcels,
        getFillColor: C.land, getLineColor: C.border, lineWidthMinPixels: 2,
      }),
      new PolygonLayer<Parcel>({
        id: 'parcelles', data: parcels, pickable: showParcels && maillon === null, visible: showParcels && maillon === null,
        stroked: false, filled: true,
        getPolygon: (p) => p.polygon,
        getFillColor: (p, { index: i }) => {
          if (season !== null) {
            const s = SUIVI_INDEX.has(i) ? SUIVI.find((q) => q.id === p.id) : undefined;
            return s ? ndviColor(ndviAt(s.serie, season)) : C.wheatDim;
          }
          if (selectKm !== null) {
            if (p.culture === 'lentille') return C.slate;
            return lentil(i) && geo.dist[i] <= selectKm ? C.lentil : C.wheatDim;
          }
          if (p.culture === 'ble' && lentil(i)) return year ? (held(p, geo.dist[i], price, year) ? C.lentil : C.fail) : C.lentil;
          if (p.culture === 'lentille') return C.slate;
          if (year) {
            const d = year.par_departement[p.dep as keyof ReplayYear['par_departement']];
            return d.choc_ble < -0.15 ? C.wheatHit : C.wheat;
          }
          return C.wheat;
        },
        updateTriggers: { getFillColor: [price, year?.annee, selectKm, geo, season] },
        transitions: { getFillColor: 500 },
        onHover: (info) => onHover(info.object ? { kind: 'parcel', p: info.object as Parcel, i: info.index } : null),
      }),
      new TextLayer({
        id: `dep-labels-${fontsReady}`, data: DEP_LABELS, visible: depLabels,
        getPosition: (d: any) => d.pos, getText: (d: any) => `${d.name}\n${d.pStar} €/t`,
        getSize: 14, getColor: C.ink, fontFamily: font, fontWeight: 600, lineHeight: 1.25, getPixelOffset: [0, -22],
        outlineWidth: 6, outlineColor: [255, 255, 255, 235], fontSettings: { sdf: true, fontSize: 64, buffer: 8 },
        characterSet: 'auto',
      }),
      new ScatterplotLayer({
        id: 'suivi-points', data: SUIVI, visible: season !== null, pickable: false,
        getPosition: (d: (typeof SUIVI)[number]) => [d.lon, d.lat],
        getRadius: (d: (typeof SUIVI)[number]) => (focus === d.id ? 13 : 10), radiusUnits: 'pixels',
        getFillColor: (d: (typeof SUIVI)[number]) => ndviColor(ndviAt(d.serie, season ?? 0)),
        stroked: true, getLineColor: (d: (typeof SUIVI)[number]) => (focus === d.id ? C.ink : [255, 255, 255]),
        getLineWidth: 2.5, lineWidthUnits: 'pixels',
        updateTriggers: { getFillColor: [season], getRadius: [focus], getLineColor: [focus] },
      }),
      new TextLayer({
        id: `suivi-lettres-${fontsReady}`, data: SUIVI, visible: season !== null,
        getPosition: (d: (typeof SUIVI)[number]) => [d.lon, d.lat], getText: (d: (typeof SUIVI)[number]) => d.lettre,
        getSize: 13, getColor: C.ink, fontFamily: font, fontWeight: 700,
        getPixelOffset: (d: (typeof SUIVI)[number]) => (SUIVI_LEFT.has(d.id) ? [-17, 0] : [17, 0]),
        getTextAnchor: (d: (typeof SUIVI)[number]) => (SUIVI_LEFT.has(d.id) ? 'end' : 'start'),
        outlineWidth: 6, outlineColor: [255, 255, 255, 235], fontSettings: { sdf: true, fontSize: 64, buffer: 8 },
      }),
      new PolygonLayer<MaillonParcel>({
        id: 'maillon', data: MAILLON.parcelles, visible: maillon !== null, pickable: maillon !== null,
        stroked: false, filled: true, getPolygon: (p) => p.polygon,
        getFillColor: (p) => MAILLON_COLOR[maillonCat(p, maillon ?? 'saison')],
        updateTriggers: { getFillColor: [maillon] },
        transitions: { getFillColor: 400 },
        onHover: (info) => onHover(info.object ? { kind: 'maillon', p: info.object as MaillonParcel, cat: maillonCat(info.object as MaillonParcel, maillon ?? 'saison') } : null),
      }),
      new PolygonLayer({
        id: 'maillon-zone', data: [ZONE_RING], visible: maillon !== null, pickable: false,
        stroked: true, filled: false, getPolygon: (d: [number, number][]) => d,
        getLineColor: [...C.ink, 150] as [number, number, number, number], getLineWidth: 1, lineWidthUnits: 'pixels',
      }),
      new LineLayer<TruckTrip>({
        id: 'routes', data: trucks?.trips ?? [], visible: !!trucks, pickable: false,
        getSourcePosition: (d) => d.from, getTargetPosition: (d) => d.to,
        getColor: [...C.ink, 46] as [number, number, number, number], getWidth: 1, widthUnits: 'pixels',
      }),
      new ScatterplotLayer({
        id: 'site', data: [geo.site], visible: showParcels && !silo, getPosition: (d: [number, number]) => d,
        getRadius: 6, radiusUnits: 'pixels', getFillColor: C.ink, stroked: true,
        getLineColor: [255, 255, 255], getLineWidth: 3, lineWidthUnits: 'pixels',
      }),
    ];
  }, [showParcels, franceMode, btYear, depLabels, price, year, selectKm, onHover, fontsReady, geo, season, focus, maillon, trucks, silo]);

  // Couches animées, recalculées à chaque image de l'horloge.
  const animated = useMemo(() => {
    if (!ICON_ATLAS) return [];
    const truckData = trucks && !reduce ? moving(trucks.trips, clock) : [];
    const boatData = boats && !reduce ? moving(BOATS, clock) : [];
    return [
      new IconLayer({
        id: 'silo', data: silo ? [geo.site] : [], iconAtlas: ICON_ATLAS, iconMapping: ICON_MAPPING,
        getIcon: () => 'silo', getPosition: (d: [number, number]) => d, getSize: 40, sizeUnits: 'pixels', pickable: false,
      }),
      new IconLayer({
        id: 'trucks', data: truckData, iconAtlas: ICON_ATLAS, iconMapping: ICON_MAPPING,
        getIcon: (d: { icon: IconName }) => d.icon, getPosition: (d: { pos: [number, number] }) => d.pos,
        getSize: 30, sizeUnits: 'pixels', pickable: false,
      }),
      new IconLayer({
        id: 'boats', data: boatData, iconAtlas: ICON_ATLAS, iconMapping: ICON_MAPPING,
        getIcon: () => 'boat', getPosition: (d: { pos: [number, number] }) => d.pos,
        getSize: 34, sizeUnits: 'pixels', pickable: false,
      }),
    ];
  }, [trucks, boats, silo, clock, geo]);

  return (
    <div ref={box} className="map-box">
      <DeckGL
        views={new MapView({ repeat: false })}
        viewState={viewState}
        onViewStateChange={({ viewState: v }) => setViewState({ ...(v as MapViewState), pitch: 0, bearing: 0 })}
        controller={{ dragRotate: false, touchRotate: false, doubleClickZoom: true }}
        layers={[...layers, ...animated]}
        onClick={(info) => { if (onPickSite && info.coordinate) onPickSite([info.coordinate[0], info.coordinate[1]]); }}
        getCursor={({ isHovering, isDragging }) => (isDragging ? 'grabbing' : onPickSite || isHovering ? 'crosshair' : 'grab')}
      />
    </div>
  );
}
