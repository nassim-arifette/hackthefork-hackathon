import { useMemo } from 'react';
import DeckGL from '@deck.gl/react';
import { MapView } from '@deck.gl/core';
import { GeoJsonLayer, PolygonLayer, ScatterplotLayer, TextLayer } from '@deck.gl/layers';
import { contours, H, parcels, replay, type Parcel } from '../data';

type RGB = [number, number, number];
const WHEAT: RGB = [217, 164, 65];
const WHEAT_HIT: RGB = [120, 92, 40];
const LENTIL: RGB = [143, 209, 106];
const LENTIL_DECLARED: RGB = [86, 178, 168];
const FAIL: RGB = [229, 85, 59];

export type Replay = (typeof replay)[number];

/** Le contrat a-t-il tenu sur cette parcelle l'année rejouée ? (même règle que le backtest) */
export function held(p: Parcel, price: number, r: Replay): boolean {
  const d = r.par_departement[p.dep as keyof Replay['par_departement']];
  const farm = price - H.kappa * p.dist;
  const margeL = farm * d.rendement_lentille_tha - H.chargesLentille + H.bonus;
  const margeB = H.prixBle * d.rendement_ble_tha - H.chargesBle;
  return margeL >= margeB;
}

interface Props { price: number; year: Replay | null; onHover: (p: Parcel | null) => void }

export default function ParcelMap({ price, year, onHover }: Props) {
  const layers = useMemo(() => {
    const isLentil = (p: Parcel) => price >= p.pRendu;
    return [
      new GeoJsonLayer({
        id: 'contours', data: contours as any, stroked: true, filled: true,
        getFillColor: [22, 33, 54, 255], getLineColor: [60, 80, 112, 255], lineWidthMinPixels: 1.2,
      }),
      new PolygonLayer<Parcel>({
        id: 'parcelles', data: parcels, extruded: true, pickable: true,
        getPolygon: (p) => p.polygon,
        getElevation: (p) => {
          if (!year) return 300;
          const d = year.par_departement[p.dep as keyof Replay['par_departement']];
          return 300 * (1 + (isLentil(p) ? year.choc_lentille_national : d.choc_ble));
        },
        getFillColor: (p) => {
          if (isLentil(p)) return year ? (held(p, price, year) ? LENTIL : FAIL) : LENTIL;
          if (p.culture === 'lentille') return LENTIL_DECLARED;
          if (year) {
            const d = year.par_departement[p.dep as keyof Replay['par_departement']];
            return d.choc_ble < -0.15 ? WHEAT_HIT : WHEAT;
          }
          return WHEAT;
        },
        updateTriggers: { getFillColor: [price, year?.annee], getElevation: [price, year?.annee] },
        transitions: { getFillColor: 450, getElevation: 700 },
        material: { ambient: 0.55, diffuse: 0.6, shininess: 12, specularColor: [40, 40, 40] },
        onHover: (info) => onHover((info.object as Parcel) ?? null),
      }),
      new ScatterplotLayer({
        id: 'site', data: [H.site], getPosition: (d: [number, number]) => d,
        getRadius: 1400, getFillColor: [233, 238, 246, 230], stroked: true,
        getLineColor: [233, 238, 246, 90], lineWidthMinPixels: 8,
      }),
      new TextLayer({
        id: 'site-label', data: [H.site], getPosition: (d: [number, number]) => d,
        getText: () => 'Site acheteur (fictif)', getSize: 14, getColor: [233, 238, 246, 255],
        getPixelOffset: [0, -26], fontFamily: 'IBM Plex Mono, Menlo, monospace',
        outlineWidth: 4, outlineColor: [12, 19, 32, 255], fontSettings: { sdf: true },
      }),
    ];
  }, [price, year, onHover]);

  return (
    <DeckGL
      views={new MapView({ repeat: false })}
      initialViewState={{ longitude: 2.62, latitude: 48.55, zoom: 8.35, pitch: 52, bearing: -14 }}
      controller={{ dragRotate: true }}
      layers={layers}
      style={{ position: 'absolute', inset: '0' }}
    />
  );
}
