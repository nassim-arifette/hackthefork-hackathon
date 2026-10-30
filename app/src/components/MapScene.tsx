import { useEffect, useMemo, useRef, useState } from 'react';
import DeckGL from '@deck.gl/react';
import { FlyToInterpolator, MapView, type MapViewState } from '@deck.gl/core';
import { GeoJsonLayer, PolygonLayer, ScatterplotLayer, TextLayer } from '@deck.gl/layers';
import { contours, DEP_NAMES, fmt, france, H, held, meta, parcels, thresholds, type Parcel, type ReplayYear } from '../data';

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
};

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

function views(width: number): { france: MapViewState; idf: MapViewState } {
  const z = Math.log2(Math.max(360, width) / 1000);
  return {
    france: { longitude: 2.45, latitude: 46.6, zoom: 4.95 + z, pitch: 0, bearing: 0 },
    idf: { longitude: 2.48, latitude: 48.64, zoom: 8.05 + z, pitch: 0, bearing: 0 },
  };
}

export type Hover = { kind: 'parcel'; p: Parcel } | { kind: 'dep'; name: string; surface: number } | null;

interface Props {
  step: number;
  price: number;
  year: ReplayYear | null;
  /** Étape « contrat » : distance maximale des parcelles retenues pour le volume visé. */
  selectKm: number | null;
  onHover: (h: Hover) => void;
}

export default function MapScene({ step, price, year, selectKm, onHover }: Props) {
  const box = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(1000);
  const [fontsReady, setFontsReady] = useState(false);
  const target = step === 0 ? 'france' : 'idf';
  const [viewState, setViewState] = useState<MapViewState>(views(1000).france);

  useEffect(() => {
    const el = box.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setWidth(el.clientWidth));
    ro.observe(el);
    document.fonts?.ready.then(() => setFontsReady(true));
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    setViewState({ ...views(width)[target], transitionDuration: 1800, transitionInterpolator: new FlyToInterpolator({ speed: 1.6 }) } as MapViewState);
  }, [target, width]);

  const layers = useMemo(() => {
    const lentil = (p: Parcel) => price >= p.pRendu;
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
        id: 'parcelles', data: parcels, pickable: showParcels, visible: showParcels,
        stroked: false, filled: true,
        getPolygon: (p) => p.polygon,
        getFillColor: (p) => {
          if (selectKm !== null) {
            if (p.culture === 'lentille') return C.slate;
            return lentil(p) && p.dist <= selectKm ? C.lentil : C.wheatDim;
          }
          if (lentil(p)) return year ? (held(p, price, year) ? C.lentil : C.fail) : C.lentil;
          if (p.culture === 'lentille') return C.slate;
          if (year) {
            const d = year.par_departement[p.dep as keyof ReplayYear['par_departement']];
            return d.choc_ble < -0.15 ? C.wheatHit : C.wheat;
          }
          return C.wheat;
        },
        updateTriggers: { getFillColor: [price, year?.annee, selectKm] },
        transitions: { getFillColor: 500 },
        onHover: (info) => onHover(info.object ? { kind: 'parcel', p: info.object as Parcel } : null),
      }),
      new TextLayer({
        id: `dep-labels-${fontsReady}`, data: DEP_LABELS, visible: step === 1,
        getPosition: (d: any) => d.pos, getText: (d: any) => `${d.name}\n${fmt(d.pStar).replace(/\u202f/g, ' ')} €/t`,
        getSize: 14, getColor: C.ink, fontFamily: font, fontWeight: 600, lineHeight: 1.25, getPixelOffset: [0, -22],
        outlineWidth: 6, outlineColor: [255, 255, 255, 235], fontSettings: { sdf: true, fontSize: 64, buffer: 8 },
        characterSet: 'auto',
      }),
      new ScatterplotLayer({
        id: 'site', data: [H.site], visible: showParcels, getPosition: (d: [number, number]) => d,
        getRadius: 6, radiusUnits: 'pixels', getFillColor: C.ink, stroked: true,
        getLineColor: [255, 255, 255], getLineWidth: 3, lineWidthUnits: 'pixels',
      }),
    ];
  }, [step, price, year, selectKm, onHover, fontsReady]);

  return (
    <div ref={box} className="map-box">
      <DeckGL
        views={new MapView({ repeat: false })}
        viewState={viewState}
        onViewStateChange={({ viewState: v }) => setViewState({ ...(v as MapViewState), pitch: 0, bearing: 0 })}
        controller={{ dragRotate: false, touchRotate: false, doubleClickZoom: true }}
        layers={layers}
        getCursor={({ isHovering }) => (isHovering ? 'crosshair' : 'grab')}
      />
    </div>
  );
}
