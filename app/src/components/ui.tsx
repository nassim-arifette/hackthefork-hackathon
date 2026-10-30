import type { ReactNode } from 'react';
import type { Label } from '../data';

const STATUS: Record<Label, string> = {
  mesure: 'Mesuré.',
  source: 'Sourcé.',
  suppose: 'Supposé.',
  synthetique: 'Synthétique.',
  modele: 'Modèle.',
};

/** Ligne de source, comme un crédit de presse : statut du chiffre puis provenance. */
export function Source({ k, children }: { k: Label; children: ReactNode }) {
  return <p className="source"><b>{STATUS[k]}</b> {children}</p>;
}

/** Grand chiffre et sa légende. */
export function Figure({ value, unit, label }: { value: ReactNode; unit?: string; label: ReactNode }) {
  return (
    <div className="figure">
      <div className="fig-v">{value}{unit && <span className="unit">{unit}</span>}</div>
      <div className="fig-l">{label}</div>
    </div>
  );
}

export function statusText(k: Label): string {
  return STATUS[k].replace('.', '');
}
