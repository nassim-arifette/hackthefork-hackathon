import { useEffect, useMemo, useRef, useState } from 'react';
import DeckGL from '@deck.gl/react';
import { FlyToInterpolator, MapView, type MapViewState } from '@deck.gl/core';
import { GeoJsonLayer, PolygonLayer, ScatterplotLayer, TextLayer } from '@deck.gl/layers';
import {
  contours, DEP_NAMES, france, held, MAILLON, maillonCat, meta, ndviAt, parcels, SUIVI, SUIVI_INDEX, thresholds,
  type MaillonCat, type MaillonParcel, type MaillonVersion, type Parcel, type ReplayYear, type SiteGeo,
} from '../data';

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
const surfMax = Math.max(...Object.values(surf));
const IDF_CODES = ['75', '77', '78', '91', '92', '93', '94', '95'];

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

function views(width: number): { france: MapViewState; idf: MapViewState; suivi: MapViewState; ciel: MapViewState } {
  const z = Math.log2(Math.max(360, width) / 1000);
  return {
    france: { longitude: 2.45, latitude: 46.6, zoom: 4.95 + z, pitch: 0, bearing: 0 },
    idf: { longitude: 2.48, latitude: 48.64, zoom: 8.05 + z, pitch: 0, bearing: 0 },
    suivi: { longitude: SUIVI_CENTER[0], latitude: SUIVI_CENTER[1], zoom: 10.3 + z, pitch: 0, bearing: 0 },
    ciel: { longitude: (ZW + ZE) / 2, latitude: (ZS + ZN) / 2, zoom: 10.35 + z, pitch: 0, bearing: 0 },
  };
}

// Rampe de NDVI : sol nu (0,15) vers végétation dense (0,9).
const NDVI_LO: RGB = [226, 214, 182], NDVI_HI: RGB = [33, 92, 63];
const ndviColor = (v: number): RGB => mix(NDVI_LO, NDVI_HI, Math.max(0, Math.min(1, (v - 0.15) / 0.75)));

export type Hover = { kind: 'parcel'; p: Parcel; i: number } | { kind: 'dep'; name: string; surface: number }
  | { kind: 'maillon'; p: MaillonParcel; cat: MaillonCat } | null;

interface Props {
  step: number;
  price: number;
  year: ReplayYear | null;
  /** Étape « contrat » : distance maximale des parcelles retenues pour le volume visé. */
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
}

export default function MapScene({ step, price, year, selectKm, onHover, geo, onPickSite, season, focus, maillon }: Props) {
  const box = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(1000);
  const [fontsReady, setFontsReady] = useState(false);
  const target = step === 0 ? 'france' : step === 5 ? 'suivi' : step === 6 ? 'ciel' : 'idf';
  const [viewState, setViewState] = useState<MapViewState>(views(1000).france);
  // Seul un changement d'étape anime la caméra. Une largeur mesurée tardivement s'applique sans
  // transition : sinon la dernière image de cette transition peut écraser la suivante.
  const shownTarget = useRef(target);

  useEffect(() => {
    const el = box.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setWidth(el.clientWidth));
    ro.observe(el);
    document.fonts?.ready.then(() => setFontsReady(true));
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    const animate = shownTarget.current !== target;
    shownTarget.current = target;
    setViewState(animate
      ? { ...views(width)[target], transitionDuration: 1800, transitionInterpolator: new FlyToInterpolator({ speed: 1.6 }) } as MapViewState
      : views(width)[target]);
  }, [target, width]);

  const layers = useMemo(() => {
    const lentil = (i: number) => price >= geo.pRendu[i];
    const showParcels = step > 0;
    const font = '"Archivo Variable", Archivo, system-ui, sans-serif';
    return [
      new GeoJsonLayer({
        id: 'france', data: france as any, stroked: true, filled: true, pickable: !showParcels,
        getFillColor: (f: any) => {
          const s = surf[f.properties.code] ?? 0;
          if (showParcels) return C.landOut;
          return s > 0 ? mix(C.land, C.lentil, 0.12 + 0.88 * Math.sqrt(s / surfMax)) : C.land;
        },
        getLineColor: (f: any) => (!showParcels && IDF_CODES.includes(f.properties.code) ? C.ink : C.border),
        getLineWidth: (f: any) => (!showParcels && IDF_CODES.includes(f.properties.code) ? 1.6 : 1),
        lineWidthUnits: 'pixels',
        updateTriggers: { getFillColor: [showParcels], getLineColor: [showParcels], getLineWidth: [showParcels] },
        onHover: (info: any) => !showParcels && onHover(info.object ? { kind: 'dep', name: info.object.properties.nom, surface: surf[info.object.properties.code] ?? 0 } : null),
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
        id: `dep-labels-${fontsReady}`, data: DEP_LABELS, visible: step === 1,
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
      new ScatterplotLayer({
        id: 'site', data: [geo.site], visible: showParcels, getPosition: (d: [number, number]) => d,
        getRadius: 6, radiusUnits: 'pixels', getFillColor: C.ink, stroked: true,
        getLineColor: [255, 255, 255], getLineWidth: 3, lineWidthUnits: 'pixels',
      }),
    ];
  }, [step, price, year, selectKm, onHover, fontsReady, geo, season, focus, maillon]);

  return (
    <div ref={box} className="map-box">
      <DeckGL
        views={new MapView({ repeat: false })}
        viewState={viewState}
        onViewStateChange={({ viewState: v }) => setViewState({ ...(v as MapViewState), pitch: 0, bearing: 0 })}
        controller={{ dragRotate: false, touchRotate: false, doubleClickZoom: true }}
        layers={layers}
        onClick={(info) => { if (onPickSite && info.coordinate) onPickSite([info.coordinate[0], info.coordinate[1]]); }}
        getCursor={({ isHovering, isDragging }) => (isDragging ? 'grabbing' : onPickSite || isHovering ? 'crosshair' : 'grab')}
      />
    </div>
  );
}
