import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import MapScene, { type Hover } from './components/MapScene';
import Method from './components/Method';
import { BacktestReveal, MarginBars, PriceChart, SeasonChart, SecurityChart, Sensitivity, YieldsChart } from './components/charts';
import { Figure, Source } from './components/ui';
import {
  backtest, bestSite, CHALLENGER, CODE_LABELS, CONTRATS, CULTURES, D77, DEP_NAMES, dec, FEATURE_LABELS, fmt, H, held, lettre, MAILLON, MARKET, meta,
  parcels, pct, pctFine, reliabilityAt, replay, SAISON, signedPct, siteGeo, SITE_SCENARIO, SUIVI, supplyCurve, thresholds,
  type MaillonCat, type MaillonVersion, type ReplayYear, type Statut,
} from './data';
import { useTween } from './useTween';

const STEPS = ['Le verrou', 'Le prix', 'L’épreuve', 'La preuve', 'Le contrat', 'La saison', 'Vu du ciel'];
const pStars = thresholds.par_departement.map((d) => d.p_star);
const MIN = 600;
const MAX = 2000;
const G = backtest.global;
const L25 = meta.lentille_2025;
const surf = meta.surface_lentille_par_dep_2025 as Record<string, number>;
const IDF_LENTIL_HA = ['77', '78', '91', '95'].reduce((a, d) => a + (surf[d] ?? 0), 0);
const MARKET_MID = (MARKET.min + MARKET.max) / 2;
const REL_MARKET = reliabilityAt(MARKET_MID);
const CONTRACT_PRICE = Math.ceil((Math.max(...pStars) + 30) / 10) * 10;

const BT2020 = backtest.annees.find((y) => y.annee === 2020)!;
const START_PRICE = 900;
const IC77 = (D77 as any).p_star_ic80 as [number, number] | undefined;
const { unique: C_UNIQUE, paliers: C_PALIERS, prime_ha: C_PRIME } = CONTRATS.calibres;
const C_BT = (G as any).contrats as Record<string, { taux_tenus: number; cout_moyen_t: number }>;
const C_2022 = (backtest.annees.find((y) => y.annee === 2022) as any).contrats as Record<string, number>;
const saving = (a: number, b: number) => Math.round((1 - a / b) * 100);
const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

const STATUT_LABEL: Record<Statut, string> = { conforme: 'Conforme', a_surveiller: 'À surveiller', en_retard: 'En retard' };
function seasonSummary(): string {
  const n = (st: Statut) => SUIVI.filter((p) => p.statut === st).length;
  const parts = [`${n('conforme')} parcelles suivent le groupe`];
  if (n('a_surveiller')) parts.push(`${n('a_surveiller')} restent sous le groupe en mai-juin et sont à surveiller`);
  if (n('en_retard')) parts.push(`${n('en_retard')} sont en retard`);
  return parts.join(', ') + '.';
}

const M25 = MAILLON.campagnes[String(MAILLON.campagne)];
const M24 = MAILLON.campagnes[String(MAILLON.apprentissage)];
const MAILLON_CAT: Record<MaillonCat, string> = {
  repere: 'Légumineuse repérée par le satellite.',
  manque: 'Légumineuse que le satellite n’a pas repérée.',
  fausse: 'Signalée à tort comme légumineuse.',
  autre: 'Non signalée, à raison.',
  connu_legume: 'Carré connu du collecteur : sert d’exemple à l’apprentissage.',
  connu_autre: 'Carré connu du collecteur : sert d’exemple à l’apprentissage.',
  non_classe: 'Non classée : parcelle trop étroite, ou trop peu d’images sans nuages.',
};
const MAILLON_TABS: { v: MaillonVersion; date: string; label: string }[] = [
  { v: 'saison', date: '31 juillet', label: 'Saison complète' },
  { v: 'avant_recolte', date: '10 juin', label: 'Avant la récolte' },
];
const quand = (iso: string | null) => (iso ? `le ${dayMonth(iso)}` : 'après le 31 juillet');
const ECART25 = M25.maturite_ndvi_05.BTH && M25.maturite_ndvi_05.FVL
  ? Math.round(Math.abs(Date.parse(M25.maturite_ndvi_05.FVL) - Date.parse(M25.maturite_ndvi_05.BTH)) / 864e5) : null;
const FEMININ = /^(betterave|jachère|prairie|luzerne|pomme|moutarde|féverole|lentille)/;
const dayMonth = (iso: string | null) => (iso
  ? new Date(`${iso}T12:00:00`).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' }).replace(/^1 /, '1er ')
  : 'après le 31 juillet');

/** Volume visé : les parcelles de blé éligibles les plus proches du site, jusqu'au volume. */
function selectTarget(geo: ReturnType<typeof siteGeo>, price: number, volume: number) {
  const elig = parcels.map((_, i) => i).filter((i) => parcels[i].culture === 'ble' && price >= geo.pRendu[i])
    .sort((a, b) => geo.dist[a] - geo.dist[b]);
  let t = 0, ha = 0, n = 0, km = 0, tkm = 0;
  for (const i of elig) {
    if (t >= volume) break;
    t += parcels[i].tonnes; ha += parcels[i].surface; n++; km = geo.dist[i]; tkm += parcels[i].tonnes * geo.dist[i];
  }
  return { ha, n, km, meanKm: t ? tkm / t : 0, reached: t >= volume };
}
const pos = (p: number) => `${((p - MIN) / (MAX - MIN)) * 100}%`;

export default function App() {
  const [step, setStep] = useState(0);
  const [price, setPrice] = useState(START_PRICE);
  const [year, setYear] = useState<ReplayYear | null>(null);
  const [shown, setShown] = useState(0);
  const [seasonDay, setSeasonDay] = useState(SAISON.jours);
  const [focus, setFocus] = useState<string | null>(null);
  const [hover, setHover] = useState<Hover>(null);
  const [method, setMethod] = useState(false);
  const [volumeKey, setVolumeKey] = useState<'pilote' | 'ambition'>('pilote');
  const [maillonV, setMaillonV] = useState<MaillonVersion>('saison');
  const VOLUME = H.volumes[volumeKey];
  // Site de collecte : déplaçable d'un clic sur la carte aux étapes « Le prix » et « Le contrat ».
  const [geo, setGeo] = useState(SITE_SCENARIO);
  const [best, setBest] = useState<{ volume: number; site: [number, number] } | null>(null);
  const moveSite = useCallback((site: [number, number]) => setGeo(siteGeo(site)), []);
  const supply = useMemo(() => supplyCurve(geo), [geo]);
  const timers = useRef<number[]>([]);

  const stop = () => { timers.current.forEach(clearTimeout); timers.current = []; };
  const at = (ms: number, fn: () => void) => { timers.current.push(window.setTimeout(fn, reduce ? 0 : ms)); };

  const stats = useMemo(() => {
    let tonnes = 0, ha = 0, n = 0, kept = 0;
    parcels.forEach((p, i) => {
      if (p.culture !== 'ble' || price < geo.pRendu[i]) return;
      tonnes += p.tonnes; ha += p.surface; n++;
      if (year && held(p, geo.dist[i], price, year)) kept++;
    });
    return { tonnes, ha, n, kept };
  }, [price, year, geo]);

  const target = useMemo(() => selectTarget(geo, price, VOLUME), [price, VOLUME, geo]);
  const targetScenario = useMemo(() => selectTarget(SITE_SCENARIO, price, VOLUME), [price, VOLUME]);
  const [busy, setBusy] = useState(false);
  const findBest = () => {
    setBusy(true);
    // Laisse le navigateur afficher « Calcul… » avant la recherche sur la grille.
    window.setTimeout(() => { const b = bestSite(VOLUME); moveSite(b.site); setBest({ volume: VOLUME, site: b.site }); setBusy(false); }, 30);
  };

  const animatePrice = useCallback((from: number, to: number, ms = 5600) => {
    stop();
    const n = Math.max(1, Math.round((to - from) / 5));
    for (let i = 0; i <= n; i++) at((ms * i) / n, () => setPrice(Math.round(from + ((to - from) * i) / n)));
  }, []);

  const reveal = useCallback(() => {
    stop(); setShown(0);
    backtest.annees.forEach((_, i) => at(400 + i * 650, () => setShown(i + 1)));
  }, []);

  const replaySeason = useCallback(() => {
    stop(); setSeasonDay(0);
    const n = 84;
    for (let i = 1; i <= n; i++) at(600 + i * 75, () => setSeasonDay(Math.round((SAISON.jours * i) / n)));
  }, []);
  const go = useCallback((s: number) => {
    const next = Math.max(0, Math.min(STEPS.length - 1, s));
    stop(); setHover(null); setStep(next);
    if (next !== 2) setYear(null);
    if (next === 1 && price < Math.min(...pStars)) at(1900, () => animatePrice(START_PRICE, CONTRACT_PRICE));
    if (next >= 2 && price < Math.max(...pStars)) setPrice(CONTRACT_PRICE);
    if (next === 2) setYear(replay[0]);
    if (next === 3) reveal();
    if (next === 5) replaySeason();
  }, [price, animatePrice, reveal, replaySeason]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      if (tag === 'INPUT' && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')) return;
      if (e.key === 'Escape') { setMethod(false); return; }
      if (method) return;
      if (e.key === ' ' || e.key === 'PageDown') { e.preventDefault(); go(step + (e.shiftKey ? -1 : 1)); }
      if (e.key === 'PageUp') { e.preventDefault(); go(step - 1); }
      if (e.key === 'ArrowRight') { stop(); setPrice((p) => Math.min(MAX, p + 10)); }
      if (e.key === 'ArrowLeft') { stop(); setPrice((p) => Math.max(MIN, p - 10)); }
      if (e.key === 'm') setMethod(true);
      if (step === 2 && (e.key === '1' || e.key === '2')) setYear(replay[+e.key - 1]);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [go, step, method]);
  useEffect(() => stop, []);

  const MR = MAILLON.resultats[maillonV];
  const MU = MR.un_sur_cinq;
  const conf = MAILLON.confusions[maillonV];
  const vus = (codes: string[]) => codes.reduce((a, c) => ({ n: a.n + (conf.rappel_par_code[c]?.n ?? 0), vus: a.vus + (conf.rappel_par_code[c]?.vus ?? 0) }), { n: 0, vus: 0 });
  const FEV = vus(['FVL', 'FVP']), POIS = vus(['PHI', 'PPR']);
  const POIS_CONNUS = MAILLON.parcelles.filter((q) => q.connu && (q.code === 'PHI' || q.code === 'PPR')).length;
  const fauxCodes = Object.keys(conf.faux_positifs_par_code).slice(0, 3).map((c) => (CODE_LABELS[c] ?? `code ${c}`).toLowerCase());
  const S = MAILLON.resultats.saison, A = MAILLON.resultats.avant_recolte;
  const RELATIF = `Sur la saison complète, comparer chaque parcelle au reste de la zone le même jour fait passer le taux retrouvé de ${pct(S.transfert.rappel)} à ${pct(S.transfert_relatif.rappel)}${A.transfert_relatif.rappel > A.transfert.rappel ? '' : ' ; au 10 juin, il n’apporte rien'}. C’est un essai choisi après coup, à confirmer sur d’autres années.`;
  const FAUSSES = fauxCodes.map((c) => (/^[aeéèiouy]/.test(c) ? `de l’${c}` : FEMININ.test(c) ? `de la ${c}` : `du ${c}`)).join(', ').replace(/, ([^,]*)$/, ' et $1');

  const mpc = conf.rappel_par_code.MPC;
  const VOIT = [
    `Sur la carte, ${FEV.vus} féveroles sur ${FEV.n} sont retrouvées`
      + (POIS.n === 0 ? '.' : FEV.vus / FEV.n - POIS.vus / POIS.n > 0.2
        ? `, mais seulement ${POIS.vus} pois sur ${POIS.n} : le carré connu n’en contient que ${POIS_CONNUS}.`
        : `, et ${POIS.vus} pois sur ${POIS.n}.`),
    mpc && mpc.vus === 0 ? 'Les mélanges de céréales et de légumineuses passent pour des céréales.' : '',
    FAUSSES ? `Les fausses alertes viennent surtout ${FAUSSES}.` : '',
    'LEC' in M25.legumineuses_par_code ? '' : `Cette zone ne compte aucune lentille d’au moins 1 ha en ${MAILLON.campagne} : le modèle repère la famille des légumineuses à graines, pas l’espèce.`,
  ].filter(Boolean).join(' ');

  const haT = useTween(stats.ha);
  const rel = reliabilityAt(price);

  return (
    <div className="app">
      <header className="masthead">
        <div className="wordmark">Le Contrat qui Tient<span>Hack the Fork 2026 · Track 3</span></div>
        <nav className="steps" aria-label="Étapes">
          {STEPS.map((s, i) => (
            <button key={s} className={i === step ? 'on' : i < step ? 'done' : ''} onClick={() => go(i)} aria-current={i === step ? 'step' : undefined}>
              <span className="n">{i + 1}</span>{s}
            </button>
          ))}
        </nav>
        <button className="link" onClick={() => setMethod(true)}>Méthode et sources</button>
      </header>

      <main className="map">
        <MapScene step={step} price={price} year={step === 2 ? year : null} selectKm={step === 4 ? target.km : null} onHover={setHover}
          geo={step === 6 ? SITE_SCENARIO : geo} onPickSite={step === 1 || step === 4 ? (s) => { moveSite(s); setBest(null); } : undefined}
          season={step === 5 ? seasonDay : null} focus={focus} maillon={step === 6 ? maillonV : null} />
        <div className="map-caption">
          {step === 0
            ? <><b>Surface en lentille par département, 2025</b><span>Agreste, Statistique agricole annuelle</span></>
            : step === 5
              ? <><b>{SUIVI.length} parcelles de lentille déclarées en {SAISON.annee}, près du site</b><span>NDVI Sentinel-2 L2A (Copernicus), replay de la saison {SAISON.annee}</span></>
              : step === 6
                ? <><b>{fmt(M25.n_parcelles_zone)} parcelles d’au moins 1 ha sur {MAILLON.zoneKm} × {MAILLON.zoneKm} km autour du site, {MAILLON.campagne}</b><span>Sentinel-2 L2A (Copernicus) ; RPG {MAILLON.campagne}, IGN. Premier des cinq tirages de carrés connus.</span></>
                : <><b>{fmt(meta.n_candidates)} parcelles de blé tendre d’hiver en Île-de-France</b><span>Registre parcellaire graphique 2025, IGN</span></>}
        </div>
        {step === 2 && year && <div className="map-year" key={year.annee}>{year.annee}</div>}
        <div className="map-legend">
          {step === 0 ? (
            <div className="ramp"><span>0 ha</span><i /><span>{fmt(Math.max(...Object.values(surf)))} ha</span></div>
          ) : step === 5 ? (
            <div className="ramp ndvi"><span>sol nu</span><i /><span>végétation dense</span><span className="ramp-site"><span className="sw site" />Site de collecte</span></div>
          ) : step === 6 ? (
            <ul>
              <li><i className="sw lentil" />Légumineuse repérée</li>
              <li><i className="sw slate" />Légumineuse manquée</li>
              <li><i className="sw wheat" />Fausse alerte</li>
              <li><i className="sw wheat-dim" />Autre culture</li>
              <li><i className="sw known" />Carré connu du collecteur</li>
              <li><i className="sw site" />Site de collecte fictif</li>
            </ul>
          ) : (
            <ul>
              <li><i className={step === 4 ? 'sw wheat-dim' : 'sw wheat'} />Blé tendre d’hiver</li>
              <li><i className="sw lentil" />{step === 4 ? `Parcelles du contrat de ${fmt(VOLUME)} t` : 'Bascule en lentille'}</li>
              {step === 2 && <li><i className="sw fail" />Contrat non tenu</li>}
              <li><i className="sw slate" />Lentille déjà cultivée</li>
              <li><i className="sw site" />{geo === SITE_SCENARIO ? 'Site de collecte fictif' : 'Site de collecte déplacé'}</li>
            </ul>
          )}
        </div>
        {(step === 1 || step === 4) && <p className="map-hint">Cliquez sur la carte pour déplacer le site de collecte</p>}
        {hover && (
          <div className="map-tip">
            {hover.kind === 'dep' ? (
              <><b>{hover.name}</b>{fmt(hover.surface)} ha de lentilles en 2025</>
            ) : hover.kind === 'maillon' ? (
              <>
                <b>{CODE_LABELS[hover.p.code] ?? `Autre culture (code ${hover.p.code})`}, {dec(hover.p.surface)} ha</b>
                {MAILLON_CAT[hover.cat]}
                {!hover.p.connu && hover.p.p[maillonV] !== null && <> Probabilité de légumineuse : {dec(hover.p.p[maillonV]!, 2)}.</>}
              </>
            ) : (
              <>
                <b>{hover.p.culture === 'ble' ? 'Blé tendre d’hiver' : 'Lentille déjà cultivée'}, {DEP_NAMES[hover.p.dep]}</b>
                {dec(hover.p.surface)} ha, à {fmt(geo.dist[hover.i])} km du site. Bascule à {fmt(geo.pRendu[hover.i])} €/t rendu.
              </>
            )}
          </div>
        )}
      </main>

      <aside className="column">
        <div className="column-body" key={step}>
          <p className="kicker">{step + 1} / {STEPS.length} · {STEPS[step]}</p>

          {step === 0 && (
            <>
              <h1>La France importe {fmt(Math.round(L25.importations_t / 1000) * 1000)} tonnes de lentilles par an.</h1>
              <p className="lead">Les agriculteurs en sèment peu. Le rendement de la lentille varie deux fois plus que celui du blé : une mauvaise année efface la marge, et le blé reste la valeur sûre.</p>
              <div className="block">
                <div className="figures">
                  <Figure value={fmt(L25.importations_t)} unit="t" label="importées en 2025" />
                  <Figure value={fmt(L25.production_t)} unit="t" label="produites en 2025" />
                  <Figure value={<>0,20<span className="vs">/</span>0,09</>} label="variabilité du rendement, lentille / blé" />
                </div>
                <Source k="mesure">Eurostat Comext, NC8 0713 40 ; Agreste, Statistique agricole annuelle 2010–2025, 2025 provisoire. Variabilité : coefficient de variation du rendement national.</Source>
              </div>
              <div className="block">
                <h3>Rendement national, en indice (100 = moyenne 2010–2025)</h3>
                <YieldsChart />
                <Source k="mesure">Agreste. 2016 : récolte de blé catastrophique. 2020 : la lentille perd plus d’un tiers de son rendement.</Source>
              </div>
              <p className="body">Sur la carte, les surfaces en lentille en 2025. L’Île-de-France, cerclée de noir, en cultive {fmt(IDF_LENTIL_HA)} ha, quand la Seine-et-Marne compte à elle seule {fmt(116585)} ha de blé tendre d’hiver.</p>
            </>
          )}

          {step === 1 && (
            <>
              <h1>À quel prix la lentille bat-elle le blé 8 années sur 10 ?</h1>
              <p className="lead">Faites varier le prix garanti. Une parcelle de blé bascule quand ce prix, transport déduit, couvre le risque de la lentille dans son département.</p>
              <div className="block control">
                <label htmlFor="price">Prix garanti, rendu au site acheteur</label>
                <div className="readout">
                  <output htmlFor="price">{fmt(price)}<span className="unit">€/t</span></output>
                  <p><b>{dec(rel * 10, 1)} années sur 10</b> où la lentille rapporte au moins autant que le blé en Seine‑et‑Marne</p>
                </div>
                <div className="range">
                  <input id="price" type="range" min={MIN} max={MAX} step={5} value={price} style={{ ['--fill' as any]: pos(price) }}
                    onChange={(e) => { stop(); setPrice(+e.target.value); }} />
                  <div className="range-marks" aria-hidden="true">
                    <span className="mk-market" style={{ left: pos(MARKET.min), width: `calc(${pos(MARKET.max)} - ${pos(MARKET.min)})` }} />
                    <span className="mk-label" style={{ left: pos(MARKET_MID) }}>réf. 2012–2016</span>
                    <span className="mk-tick" style={{ left: pos(D77.p_star) }} />
                    <span className="mk-label" style={{ left: pos(D77.p_star) }}>8 sur 10</span>
                  </div>
                </div>
              </div>
              <div className="block">
                <div className="figures two">
                  <Figure value={fmt(haT)} unit="ha" label={`de blé basculent à ce prix (${fmt(stats.n)} parcelles)`} />
                  <Figure value={fmt(stats.tonnes)} unit="t" label="de lentilles si toutes ces parcelles signaient" />
                </div>
              </div>
              <div className="block">
                <h3>Ce que le prix achète</h3>
                <PriceChart price={price} min={MIN} max={MAX} supply={supply} />
                <Source k="modele">20 000 années rejouées : météo et prix du blé de 2010 à 2025. Référence historique du prix de la lentille : Eurostat, {MARKET.annees[0]}–{MARKET.annees[1]}.</Source>
              </div>
              <p className="pull">À la référence historique de {fmt(MARKET.min)} à {fmt(MARKET.max)} €/t, la lentille ne gagne que {dec(REL_MARKET * 10, 1)} années sur 10. Pour 8 sur 10, il faut {fmt(D77.p_star)} €/t en Seine-et-Marne.</p>
              <div className="block">
                <h3>Les contrats d’aujourd’hui, face au blé francilien</h3>
                <table className="list models">
                  <thead><tr><th>Contrat</th><th className="num">Années gagnantes</th></tr></thead>
                  <tbody>
                    {CONTRATS.existants.map((c) => (
                      <tr key={c.id}><td>{c.nom}<span>{c.detail}</span></td><td className="num">{dec(c.simulation.protection * 10, 1)} sur 10</td></tr>
                    ))}
                  </tbody>
                </table>
                <Source k="modele">Mêmes années simulées, Seine-et-Marne. Prix Unéal (12/12/2023) et barème NatUp 2023–2024 (Union Agricole, 18/09/2023) publiés ; proposition du dossier pilote supposée. Ces contrats partagent aussi le risque par les volumes et la qualité : seule la protection face au blé est mesurée ici.</Source>
              </div>
              <div className="block">
                <h3>Prix plancher par département</h3>
                <table className="list">
                  <tbody>
                    {thresholds.par_departement.map((d) => (
                      <tr key={d.dep}><td>{DEP_NAMES[d.dep]}</td><td className="num">{fmt(d.p_star)} €/t</td></tr>
                    ))}
                  </tbody>
                </table>
                <Source k="modele">Quantile 80 % du prix d’équilibre lentille / blé. Niveau de rendement de la lentille emprunté aux départements producteurs voisins.{IC77 && <> Incertitude sur le prix de la Seine-et-Marne : de {fmt(IC77[0])} à {fmt(IC77[1])} €/t, en rééchantillonnant les années.</>}</Source>
              </div>
              <button className="link" onClick={() => animatePrice(START_PRICE, CONTRACT_PRICE)}>Rejouer la bascule</button>
            </>
          )}

          {step === 2 && (
            <>
              <h1>Et si la récolte tourne mal ?</h1>
              <p className="lead">On rejoue deux années réelles sur les parcelles sous contrat à {fmt(price)} €/t. Le contrat tient si la lentille rapporte au moins autant que le blé, avec les rendements et le prix du blé de l’année.</p>
              <div className="tabs" role="tablist">
                {replay.map((r, i) => (
                  <button key={r.annee} role="tab" aria-selected={year?.annee === r.annee} className={year?.annee === r.annee ? 'on' : ''} onClick={() => { stop(); setYear(r); }}>
                    <b>{r.annee}</b>{i === 0 ? 'Le blé s’effondre' : 'La lentille s’effondre'}
                  </button>
                ))}
              </div>
              {year && (
                <>
                  <div className="block">
                    <div className="figures">
                      <Figure value={signedPct(year.par_departement['77'].choc_ble)} label="rendement du blé en Seine-et-Marne" />
                      <Figure value={signedPct(year.choc_lentille_national)} label="rendement de la lentille en France" />
                      <Figure value={fmt(year.prix_ble)} unit="€/t" label="prix du blé de l’année" />
                    </div>
                    <Source k="mesure">Agreste, écart à la moyenne des cinq années précédentes ; Eurostat, indice des prix du blé tendre.</Source>
                  </div>
                  <div className="block">
                    <h3>Marge par hectare en Seine-et-Marne, {year.annee}</h3>
                    <MarginBars
                      lentil={price * year.par_departement['77'].rendement_lentille_tha * (1 - H.qualite) - H.chargesLentille + H.aide + H.rotation}
                      wheat={year.prix_ble * year.par_departement['77'].rendement_ble_tha - H.chargesBle} />
                    <Source k="modele">Au prix garanti, transport non déduit, sur les tonnes acceptées au tri ({pct(1 - H.qualite)} de la récolte) ; bénéfice de rotation de {fmt(H.rotation)} €/ha compris ; rendement et prix du blé de l’année mesurés.</Source>
                  </div>
                  <div className="block verdict">
                    <div className="verdict-v">{stats.n ? pct(stats.kept / stats.n) : '—'}</div>
                    <p>des {fmt(stats.n)} parcelles sous contrat auraient rapporté au moins autant qu’en blé.</p>
                  </div>
                  <p className="body">
                    {year.annee === 2016
                      ? 'En 2016, la lentille sous contrat aurait protégé l’exploitation : la marge du blé s’effondre avec son rendement, alors que le prix garanti de la lentille ne bouge pas.'
                      : `En 2020, la lentille perd plus d’un tiers de son rendement. ${stats.n && stats.kept / stats.n >= 0.8 ? 'À ce prix, le contrat encaisse le choc en Île-de-France.' : 'À ce prix, le contrat cède sur une partie des parcelles.'} Dans les départements producteurs, le backtest montre qu’il n’a tenu que dans ${pct(BT2020.taux_tenus ?? 0)} des cas cette année-là.`}
                  </p>
                  <Source k="modele">Rendement de la lentille en Île-de-France : choc national appliqué au rendement moyen simulé.</Source>
                </>
              )}
            </>
          )}

          {step === 3 && (
            <>
              <h1>Le modèle tient-il sur des années qu’il n’a jamais vues ?</h1>
              <p className="lead">Le modèle d’apprentissage relie la météo de l’année au rendement. Pour chaque année de 2019 à 2025, il n’apprend que des années précédentes et fixe son prix ; on le compare ensuite à la récolte réelle.</p>
              <div className="block">
                <h3>Rendement relatif de la lentille : intervalle prédit à 80 %, puis réel</h3>
                <BacktestReveal shown={shown} />
                <p className="chart-key"><i className="k-int" />intervalle prédit <i className="k-ok" />réel, dans l’intervalle <i className="k-ko" />réel, en dehors</p>
              </div>
              <div className="block">
                <div className="figures">
                  <Figure value={pct(G.taux_tenus)} label={`des contrats ont tenu, pour ${pct(backtest.fiabilite_visee)} visés`} />
                  <Figure value={pct(G.couverture_M1)} label="des récoltes dans l’intervalle à 80 %" />
                  <Figure value={`±${Math.round(G.erreur_mediane_M1 * 100)} %`} label="erreur médiane sur le rendement d’une année" />
                </div>
                <table className="years">
                  <thead><tr><th />{backtest.annees.map((y) => <th key={y.annee}>{y.annee}</th>)}</tr></thead>
                  <tbody>
                    <tr><td>Contrats tenus</td>{backtest.annees.map((y, i) => <td key={y.annee} className={i < shown ? ((y.taux_tenus ?? 0) >= 0.8 ? '' : 'bad') : 'hide'}>{i < shown ? pct(y.taux_tenus ?? 0) : '·'}</td>)}</tr>
                    <tr><td>Prix du blé, €/t</td>{backtest.annees.map((y) => <td key={y.annee}>{fmt(y.prix_ble)}</td>)}</tr>
                  </tbody>
                </table>
                <Source k="modele">Backtest glissant sur {G.n_cas} cas département × année. Aucune année test n’a servi à l’entraînement, au réglage ni au regroupement des séries.</Source>
              </div>
              <p className="body">L’objectif est d’être proche de {pct(backtest.fiabilite_visee)}, pas de 100 % : au-dessus, l’acheteur paie une protection inutile ; en dessous, la promesse faite à l’agriculteur est rompue. Les contrats cèdent surtout en 2020 et 2021, deux effondrements de la lentille, puis en 2022, quand le prix du blé flambe.</p>
              <div className="block">
                <h3>Ce que le modèle apporte au prix</h3>
                <table className="list models">
                  <thead><tr><th>Façon de fixer le prix</th><th className="num">Contrats tenus</th></tr></thead>
                  <tbody>
                    <tr><td>Prix calculé sur les moyennes<span>référence naïve, sans modèle</span></td><td className="num bad">{pct(G.taux_tenus_moyenne)}</td></tr>
                    <tr><td>Distribution calibrée, sans météo<span>tendance seule</span></td><td className="num">{pct(G.taux_tenus_M0)}</td></tr>
                    <tr className="hl"><td>Régression quantile avec météo<span>modèle d’apprentissage retenu avant tout résultat</span></td><td className="num">{pct(G.taux_tenus)}</td></tr>
                    <tr><td>LightGBM avec météo<span>gradient boosting</span></td><td className="num">{pct(G.taux_tenus_M2)}</td></tr>
                  </tbody>
                </table>
                <p className="body small">Un prix calculé sur les rendements et les prix moyens n’aurait tenu que {pct(G.taux_tenus_moyenne)} des contrats : la moyenne ignore la mauvaise année. Une distribution calibrée approche la promesse de 8 sur 10, et la météo y ajoute un peu. LightGBM, plus précis sur l’année moyenne, sous-estime les mauvaises années.</p>
                <Source k="modele">Backtest glissant 2019–2025 sur {G.n_cas} cas, 80 % visés. Précision et prix 2026 de chaque modèle dans Méthode et sources.</Source>
              </div>
              <div className="block">
                <h3>Ce que le modèle a appris de la météo</h3>
                <div className="bars imp">
                  {CHALLENGER.importances_q50.map((f) => (
                    <div key={f.variable} className="bar-row">
                      <span className="bar-l">{FEATURE_LABELS[f.variable] ?? f.variable}</span>
                      <span className="bar-track"><span className={`bar ${f.variable === 'tendance' ? 'neutral' : 'lentil'}`} style={{ width: `${(f.part / CHALLENGER.importances_q50[0].part) * 100}%` }} /></span>
                      <b className="bar-v">{pct(f.part)}</b>
                    </div>
                  ))}
                </div>
                <Source k="modele">Part de chaque variable dans l’apprentissage de LightGBM (gain, rendement médian). Météo journalière NASA POWER 2010–2025, 43 départements, en écart à la climatologie 2010–2018.</Source>
              </div>
              <button className="link" onClick={reveal}>Rejouer la révélation</button>
            </>
          )}

          {step === 4 && (
            <>
              <h1>La proposition faite à l’agriculteur</h1>
              <div className="tabs" role="tablist" aria-label="Volume du contrat">
                {(['pilote', 'ambition'] as const).map((k) => (
                  <button key={k} role="tab" aria-selected={volumeKey === k} className={volumeKey === k ? 'on' : ''} onClick={() => setVolumeKey(k)}>
                    <b>{fmt(H.volumes[k])} t</b>{k === 'pilote' ? 'Pilote, une campagne' : 'Ambition de bassin'}
                  </button>
                ))}
              </div>
              <div className="block contract">
                <p className="contract-title">Proposition de contrat, campagne {meta.campagne}</p>
                <dl>
                  <dt>Objet</dt><dd>Achat de lentilles pour l’alimentation humaine, sur trois campagnes.</dd>
                  <dt>Prix garanti</dt><dd><b>{fmt(C_PALIERS.paliers![0])} €/t</b> pour la première tonne acceptée par hectare, <b>{fmt(C_PALIERS.paliers![1])} €/t</b> pour la deuxième, <b>{fmt(C_PALIERS.paliers![2])} €/t</b> au-delà. Départ ferme en Seine-et-Marne, sur les tonnes acceptées au tri pour l’alimentation humaine.</dd>
                  <dt>Ce qu’il garantit</dt><dd>Une marge au moins égale à celle du blé dans {pct(H.tau)} des années simulées : la protection d’un prix unique de {fmt(D77.p_star)} €/t, pour {saving(C_PALIERS.simulation.cout_moyen_t, C_UNIQUE.simulation.cout_moyen_t)} % de moins en moyenne.</dd>
                  <dt>Ce qu’il ne garantit pas</dt><dd>Une récolte effondrée réduit la marge : {dec(D77.rendement_lentille_q10_tha, 2)} t/ha ou moins une année sur dix. Les lots refusés au tri ne sont pas payés au prix garanti.</dd>
                  <dt>Volume visé</dt><dd>{target.reached
                    ? <><b>{fmt(VOLUME)} t</b> acceptées, soit {pctFine(VOLUME / L25.importations_t)} des importations de 2025, sur {fmt(target.ha)} ha : les {fmt(target.n)} parcelles éligibles les plus proches du site, à moins de {fmt(target.km)} km.</>
                    : <>Le prix est trop bas pour réunir {fmt(VOLUME)} t. Remontez-le à l’étape 2.</>}</dd>
                </dl>
                <Source k="modele">Barème calibré sur les mêmes années simulées que le prix plancher : la première tonne est recalculée, les deux suivantes reprennent la proposition du dossier pilote. Texte assemblé à partir des chiffres calculés ; volumes : hypothèses de l’équipe.</Source>
              </div>
              <div className="block">
                <h3>Où placer le site de collecte ?</h3>
                <p className="body small">Cliquez sur la carte pour déplacer le site : les parcelles retenues, leurs distances et le coût de collecte se recalculent.</p>
                <div className="figures two">
                  <Figure value={dec(target.meanKm, 1)} unit="km" label={`distance moyenne des parcelles du contrat de ${fmt(VOLUME)}\u00a0t`} />
                  <Figure value={dec(H.forfait + H.kappa * target.meanKm, 1)} unit="€/t" label="coût moyen de collecte par tonne acceptée" />
                </div>
                <div className="actions">
                  <button className="link" onClick={findBest} disabled={busy}>{busy ? 'Calcul…' : `Meilleur emplacement pour ${fmt(VOLUME)}\u00a0t`}</button>
                  {geo !== SITE_SCENARIO && <button className="link" onClick={() => { setGeo(SITE_SCENARIO); setBest(null); }}>Revenir au site du scénario</button>}
                </div>
                {best && best.volume === VOLUME && geo.site === best.site && (
                  <p className="body small">Point de la grille qui minimise la distance moyenne pour {fmt(VOLUME)}&nbsp;t : {dec(H.kappa * (targetScenario.meanKm - target.meanKm), 1)} €/t de collecte en moins qu’au site du scénario. Le gain reste faible face à un prix garanti de plus de 1 000 €/t : le site se choisit d’abord pour la logistique.</p>
                )}
                <Source k="suppose">Forfait de {fmt(H.forfait)} €/t et {dec(H.kappa, 2)} €/t/km ; distance routière approchée par la distance à vol d’oiseau × {dec(H.detour, 1)}. Emplacements candidats sur une grille, à confronter aux sites existants (silos, zones d’activité).</Source>
              </div>
              <div className="block">
                <h3>Impact du contrat</h3>
                <div className="figures">
                  <Figure value={fmt(VOLUME * H.impact.proteines)} unit="t" label="de protéines végétales" />
                  <Figure value={fmt((target.ha * H.impact.azote) / 1000)} unit="t" label="d’azote minéral non apporté" />
                  <Figure value={fmt(target.ha * H.impact.co2e)} unit="t CO₂e" label="d’émissions directes évitées" />
                </div>
                <Source k="source">Par campagne, sur les {fmt(target.ha)} ha de blé remplacés. Protéines : 25 % du grain (Terres Inovia / Terres Univia, récolte 2024). Azote : 180 kg N/ha sur blé en Île-de-France (Agreste 2021). N₂O direct : GIEC 2019 et PRG100 de l’AR6 ; hors fabrication des engrais.</Source>
              </div>
              {lettre.source === 'llm' && lettre.texte && (
                <div className="block">
                  <h3>Lettre d’accompagnement</h3>
                  <p className="body letter">{lettre.texte}</p>
                  <Source k="modele">Rédigée par un LLM ({lettre.modele}) à partir des chiffres ci-dessus. Chaque nombre du texte a été vérifié contre les chiffres fournis.</Source>
                </div>
              )}
              <div className="block">
                <h3>Le prix de la sécurité</h3>
                <p className="body small">Prix plancher en Seine-et-Marne selon le nombre d’années gagnantes visé. Garantir 8 années sur 10 coûte {dec(D77.p_star / MARKET_MID, 1)} fois la référence historique 2012–2016.</p>
                <SecurityChart />
                <Source k="modele">Même simulation, quantile variable.</Source>
              </div>
              <div className="block">
                <h3>Trois façons de garantir 8 années sur 10</h3>
                <table className="list models contracts">
                  <thead><tr><th>Contrat</th><th className="num">Coût moyen</th><th className="num">Année faible</th><th className="num">Backtest</th></tr></thead>
                  <tbody>
                    <tr><td>Prix unique<span>{fmt(C_UNIQUE.prix!)} €/t sur toutes les tonnes</span></td><td className="num">{fmt(C_UNIQUE.simulation.cout_moyen_t)}</td><td className="num">{fmt(C_UNIQUE.simulation.cout_t_annee_faible)}</td><td className="num">{pct(C_BT.unique.taux_tenus)}</td></tr>
                    <tr className="hl"><td>Barème par tranches<span>{fmt(C_PALIERS.paliers![0])} €/t la première tonne par hectare, puis {fmt(C_PALIERS.paliers![1])} et {fmt(C_PALIERS.paliers![2])}</span></td><td className="num">{fmt(C_PALIERS.simulation.cout_moyen_t)}</td><td className="num">{fmt(C_PALIERS.simulation.cout_t_annee_faible)}</td><td className="num">{pct(C_BT.paliers.taux_tenus)}</td></tr>
                    <tr><td>Prix de base et prime à l’hectare<span>{fmt(C_PRIME.prix!)} €/t et {fmt(C_PRIME.prime_ha!)} €/ha, versés même sans récolte</span></td><td className="num">{fmt(C_PRIME.simulation.cout_moyen_t)}</td><td className="num">{fmt(C_PRIME.simulation.cout_t_annee_faible)}</td><td className={`num${C_BT.prime_ha.taux_tenus < H.tau ? ' bad' : ''}`}>{pct(C_BT.prime_ha.taux_tenus)}</td></tr>
                  </tbody>
                </table>
                <p className="body small">Le barème par tranches paie cher les premières tonnes, celles qui manquent les mauvaises années, et moins le surplus des bonnes : même protection, {saving(C_PALIERS.simulation.cout_moyen_t, C_UNIQUE.simulation.cout_moyen_t)} % de moins en moyenne. Sur 2019–2025, il tient autant de contrats que le prix unique, pour un coût réalisé inférieur de {saving(C_BT.paliers.cout_moyen_t, C_BT.unique.cout_moyen_t)} %. La prime à l’hectare coûte encore moins, mais l’acheteur la paie même quand la récolte manque, et elle a cédé quand le blé a flambé : {pct(C_2022.prime_ha)} des contrats tenus en 2022.</p>
                <Source k="modele">Seine-et-Marne, mêmes années simulées. Coût moyen : sommes versées par tonne acceptée, en €/t, hors collecte et tri. Année faible : {dec(CONTRATS.yFaible, 2)} t/ha acceptées, une année sur dix. Backtest : chaque forme recalibrée sur les seules années passées, {G.n_cas} cas.</Source>
              </div>
              <div className="block">
                <h3>Ce qui fait bouger le prix plancher</h3>
                <Sensitivity />
                <Source k="modele">Aide couplée sourcée ; charges arrondies depuis les guides Terres Inovia ; bonus de rotation et part refusée supposés. Détail dans Méthode et sources.</Source>
              </div>
              <div className="block">
                <h3>Là où la lentille tient le mieux</h3>
                <table className="list">
                  <tbody>
                    {meta.france.slice(0, 5).map((d) => (
                      <tr key={d.dep}><td>{d.nom}<span>lentille {dec(d.rendement_lentille_qha)} q/ha, blé {dec(d.rendement_ble_qha, 0)} q/ha{d.avec?.length ? `, estimée avec ${d.avec.join(', ')}` : ''}</span></td><td className="num">{fmt(d.p_star)} €/t</td></tr>
                    ))}
                  </tbody>
                </table>
                <Source k="modele">Même calcul, avec les rendements propres à chaque département producteur et les charges franciliennes partout : un classement des rendements, pas des économies locales. Le prix plancher baisse là où le blé rend moins.</Source>
              </div>
              <div className="block">
                <h3>Le même moteur, quatre autres légumineuses</h3>
                <table className="list models contracts">
                  <thead><tr><th>Culture</th><th className="num">Plancher</th><th className="num">Prix fixe</th><th className="num">Indexé</th></tr></thead>
                  <tbody>
                    {CULTURES.map((c) => (
                      <tr key={c.id} className={c.id === 'lentille' ? 'hl' : ''}>
                        <td>{c.nom}<span>{c.n_series} séries Agreste{c.id === 'haricot' ? ', scénario irrigué' : ''}</span></td>
                        <td className="num">{fmt(c.p_star['77'])}</td>
                        <td className={`num${(c.backtest.taux_tenus ?? 0) < H.tau ? ' bad' : ''}`}>{pct(c.backtest.taux_tenus ?? 0)}</td>
                        <td className={`num${(c.backtest.taux_tenus_indexe ?? 0) < H.tau - 0.005 ? ' bad' : ''}`}>{pct(c.backtest.taux_tenus_indexe ?? 0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="body small">Pour la lentille, un prix fixe tient {pct(CULTURES[0].backtest.taux_tenus ?? 0)} des contrats et l’indexation l’améliore un peu. Pour les quatre autres, le plancher indexé sur le blé tient {pct(Math.min(...CULTURES.slice(1).map((c) => c.backtest.taux_tenus_indexe ?? 0)))} à {pct(Math.max(...CULTURES.slice(1).map((c) => c.backtest.taux_tenus_indexe ?? 0)))} des contrats dans ce backtest, davantage que le prix fixe. Cela motive une forme de contrat propre à chaque culture. Le pois et la féverole demandent {fmt(CULTURES.find((c) => c.id === 'pois')!.p_star['77'])} et {fmt(CULTURES.find((c) => c.id === 'feverole')!.p_star['77'])} €/t pour rivaliser avec le blé 8 années sur 10, contre 200 à 260 €/t dans le référentiel de plan d’entreprise CRIT 2025.</p>
                <p className="body small">Repères de prix : pois chiche standard payé 600 à 620 €/t à un producteur Cavac pour la récolte 2025 ; haricot à 1 200 €/t au centre du scénario 900 à 1 500. Le repère haricot de 1 188 €/t vient d’un barème d’indemnisation, pas d’une offre d’achat.</p>
                <Source k="modele">Prix plancher pour 8 années sur 10 en Seine-et-Marne, en €/t ; contrats tenus en backtest 2019–2025 sur les départements producteurs, recalibrés sur les seules années passées. Même modèle du blé ; séries Agreste et météo NASA POWER propres à chaque culture. Charges calées sur les guides Terres Inovia pois chiche 2026, pois 2025 et féverole 2024 ; haricot : budget reconstruit incluant l’eau et l’énergie, hors mécanisation et récolte. Aide indicative Telepac 2026. Prix : témoignage Réussir du 27 juin 2026, CRIT Grand Est 2025 et scénario haricot documenté dans la revue filière.</Source>
              </div>
            </>
          )}

          {step === 5 && (
            <>
              <h1>Les parcelles sous contrat poussent-elles bien ?</h1>
              <p className="lead">Prototype de suivi en saison, rejoué sur {SAISON.annee} : les {SUIVI.length} parcelles de lentille déclarées cette année-là les plus proches du site, vues par Sentinel-2 tous les quelques jours.</p>
              <div className="block">
                <h3>Indice de végétation (NDVI), mars à mi-août {SAISON.annee}</h3>
                <SeasonChart day={seasonDay} focus={focus} />
                <div className="range season">
                  <input type="range" min={0} max={SAISON.jours} step={1} value={seasonDay} aria-label="Jour de la saison"
                    style={{ ['--fill' as any]: `${(seasonDay / SAISON.jours) * 100}%` }} onChange={(e) => { stop(); setSeasonDay(+e.target.value); }} />
                </div>
                <p className="chart-key"><i className="k-med" />médiane du groupe <i className="k-conf" />conforme <i className="k-warn" />à surveiller <i className="k-late" />en retard</p>
                <Source k="mesure">Sentinel-2 L2A (Copernicus), catalogue Earth Search : {fmt(SAISON.nImages)} images. NDVI médian des pixels de 10 m classés végétation ou sol nu, parcelle réduite de 10 m ; une date compte si {pct(SAISON.partValide)} des pixels sont valides.</Source>
              </div>
              <div className="block">
                <h3>Le point au moment de la floraison</h3>
                <table className="list models suivi">
                  <thead><tr><th>Parcelle</th><th className="num">Écart au groupe</th><th className="num">Images utiles</th></tr></thead>
                  <tbody>
                    {[...SUIVI].sort((a, b) => a.ecart - b.ecart).map((p) => (
                      <tr key={p.id} onMouseEnter={() => setFocus(p.id)} onMouseLeave={() => setFocus(null)} className={focus === p.id ? 'hl' : ''}>
                        <td><b className={`tag ${p.statut}`}>{p.lettre}</b>{STATUT_LABEL[p.statut]}<span>{dec(p.surface)} ha, à {fmt(p.distKm)} km du site</span></td>
                        <td className={`num${p.statut === 'en_retard' ? ' bad' : ''}`}>{Math.abs(p.ecart) < 0.005 ? '0,00' : `${p.ecart > 0 ? '+' : '−'}${dec(Math.abs(p.ecart), 2)}`}</td>
                        <td className="num">{p.datesValides} sur {p.datesVues}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="body small">{seasonSummary()} Le suivi ne remplace pas la visite : il dit où aller voir, et à quel moment.</p>
                <Source k="suppose">Écart moyen de NDVI à la médiane du groupe, du 1er mai au 30 juin. À surveiller sous {dec(SAISON.seuils.surveiller, 2)}, en retard sous {dec(SAISON.seuils.retard, 2)} : seuils de l’équipe, à caler sur des rendements de parcelles.</Source>
              </div>
              <button className="link" onClick={replaySeason}>Rejouer la saison</button>
            </>
          )}

          {step === 6 && (
            <>
              <h1>Les légumineuses du bassin, un an avant le RPG</h1>
              <p className="lead">Le RPG d’une campagne n’est publié que l’année suivante. Sur {MAILLON.zoneKm} km de côté autour du site, un collecteur qui connaît les parcelles d’un carré de {MAILLON.blocKm} km sur cinq, celles de ses adhérents par exemple, cherche les légumineuses des autres carrés sur les images Sentinel-2 de {MAILLON.campagne}.</p>
              <div className="tabs" role="tablist" aria-label="Images utilisées">
                {MAILLON_TABS.map((t) => (
                  <button key={t.v} role="tab" aria-selected={maillonV === t.v} className={maillonV === t.v ? 'on' : ''} onClick={() => setMaillonV(t.v)}>
                    <b>{t.date}</b>{t.label}
                  </button>
                ))}
              </div>
              <div className="block">
                <div className="figures two">
                  <Figure value={pct(MU.moyenne.rappel)} label="des légumineuses des autres carrés sont retrouvées" />
                  <Figure value={pct(MU.moyenne.precision)} label="des parcelles signalées sont bien des légumineuses" />
                </div>
                <Source k="modele">Images Sentinel-2 jusqu’au {MAILLON_TABS.find((t) => t.v === maillonV)!.date} {MAILLON.campagne}, {M25.versions[maillonV].n_dates} dates utiles. Moyenne de cinq tirages : un carré sur cinq connu à chaque fois, jugement sur les quatre autres. Légumineuses retrouvées : de {pct(MU.min.rappel)} à {pct(MU.max.rappel)} selon le tirage.</Source>
              </div>
              <div className="block">
                <h3>Ce que le modèle connaît de {MAILLON.campagne}</h3>
                <table className="list models">
                  <thead><tr><th>Exemples d’apprentissage</th><th className="num">Retrouvées</th><th className="num">Justes</th></tr></thead>
                  <tbody>
                    <tr className="hl"><td>Un carré sur cinq<span>parcelles connues du collecteur</span></td><td className="num">{pct(MU.moyenne.rappel)}</td><td className="num">{pct(MU.moyenne.precision)}</td></tr>
                    <tr><td>Quatre carrés sur cinq<span>validation croisée par carrés de {MAILLON.blocKm} km</span></td><td className="num">{pct(MR.blocs.rappel)}</td><td className="num">{pct(MR.blocs.precision)}</td></tr>
                    <tr><td>Aucun : modèle appris sur {MAILLON.apprentissage}<span>avec le RPG {MAILLON.apprentissage}, appliqué aux images {MAILLON.campagne}</span></td><td className="num bad">{pct(MR.transfert.rappel)}</td><td className="num bad">{pct(MR.transfert.precision)}</td></tr>
                  </tbody>
                </table>
                <p className="body small">D’une année sur l’autre, le modèle ne tient pas encore. Le printemps {MAILLON.apprentissage} a été trop nuageux : {fmt(M24.versions.saison.dates_par_parcelle_mediane)} dates utiles par parcelle en médiane, contre {fmt(M25.versions.saison.dates_par_parcelle_mediane)} en {MAILLON.campagne}. La signature a aussi changé. En {MAILLON.apprentissage}, le NDVI du blé passe sous 0,5 {quand(M24.maturite_ndvi_05.BTH)} et celui des féveroles d’hiver {quand(M24.maturite_ndvi_05.FVL)} ; en {MAILLON.campagne}, {quand(M25.maturite_ndvi_05.BTH)} et {quand(M25.maturite_ndvi_05.FVL)}{ECART25 !== null ? `, à ${ECART25} jours d’écart` : ''}. {RELATIF}</p>
                <Source k="modele">Retrouvées : part des légumineuses du RPG {MAILLON.campagne} signalées. Justes : part des parcelles signalées qui sont des légumineuses. Seuil de probabilité {dec(MAILLON.seuil, 1)}, LightGBM sur le NDVI et le NDMI par période de 10 jours.</Source>
              </div>
              <div className="block">
                <h3>Ce qu’il voit, ce qu’il manque</h3>
                <p className="body small">{VOIT}</p>
                <Source k="mesure">Sentinel-2 L2A (Copernicus), catalogue Earth Search : {fmt(M24.n_images)} dates utiles en {MAILLON.apprentissage}, {fmt(M25.n_images)} en {MAILLON.campagne}, du 1er avril au 31 juillet ; pixels classés végétation ou sol nu, parcelle réduite de 10 m. Étiquettes : RPG {MAILLON.apprentissage} et {MAILLON.campagne} (IGN), groupes protéagineux et légumineuses à grains ; libellés de la notice Telepac 2025.</Source>
              </div>
            </>
          )}
        </div>

        <footer className="column-foot">
          <button className="link" onClick={() => go(step - 1)} disabled={step === 0}>← Précédent</button>
          {step < STEPS.length - 1
            ? <button className="primary" onClick={() => go(step + 1)}>{STEPS[step + 1]} →</button>
            : <button className="primary" onClick={() => setMethod(true)}>Méthode et sources →</button>}
        </footer>
      </aside>

      {method && <div className="scrim" onClick={() => setMethod(false)} />}
      {method && <Method onClose={() => setMethod(false)} />}
    </div>
  );
}
