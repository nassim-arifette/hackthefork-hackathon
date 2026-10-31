import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import MapScene, { type Hover } from './components/MapScene';
import Method from './components/Method';
import { BacktestReveal, MarginBars, PriceChart, SecurityChart, Sensitivity, YieldsChart } from './components/charts';
import { Figure, Source } from './components/ui';
import {
  backtest, CHALLENGER, D77, DEP_NAMES, dec, FEATURE_LABELS, fmt, H, held, lettre, MARKET, meta, parcels, pct, reliabilityAt, replay,
  signedPct, thresholds, type ReplayYear,
} from './data';
import { useTween } from './useTween';

const STEPS = ['Le verrou', 'Le prix', 'L’épreuve', 'La preuve', 'Le contrat'];
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
const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
const pos = (p: number) => `${((p - MIN) / (MAX - MIN)) * 100}%`;

export default function App() {
  const [step, setStep] = useState(0);
  const [price, setPrice] = useState(START_PRICE);
  const [year, setYear] = useState<ReplayYear | null>(null);
  const [shown, setShown] = useState(0);
  const [hover, setHover] = useState<Hover>(null);
  const [method, setMethod] = useState(false);
  const [volumeKey, setVolumeKey] = useState<'pilote' | 'ambition'>('pilote');
  const VOLUME = H.volumes[volumeKey];
  const timers = useRef<number[]>([]);

  const stop = () => { timers.current.forEach(clearTimeout); timers.current = []; };
  const at = (ms: number, fn: () => void) => { timers.current.push(window.setTimeout(fn, reduce ? 0 : ms)); };

  const stats = useMemo(() => {
    let tonnes = 0, ha = 0, n = 0, kept = 0;
    for (const p of parcels) {
      if (p.culture !== 'ble' || price < p.pRendu) continue;
      tonnes += p.tonnes; ha += p.surface; n++;
      if (year && held(p, price, year)) kept++;
    }
    return { tonnes, ha, n, kept };
  }, [price, year]);

  // Volume visé : on retient les parcelles éligibles les plus proches du site acheteur.
  const target = useMemo(() => {
    const elig = parcels.filter((p) => p.culture === 'ble' && price >= p.pRendu).sort((a, b) => a.dist - b.dist);
    let t = 0, ha = 0, n = 0, km = 0;
    for (const p of elig) {
      if (t >= VOLUME) break;
      t += p.tonnes; ha += p.surface; n++; km = p.dist;
    }
    return { ha, n, km, reached: t >= VOLUME };
  }, [price, VOLUME]);

  const animatePrice = useCallback((from: number, to: number, ms = 5600) => {
    stop();
    const n = Math.max(1, Math.round((to - from) / 5));
    for (let i = 0; i <= n; i++) at((ms * i) / n, () => setPrice(Math.round(from + ((to - from) * i) / n)));
  }, []);

  const reveal = useCallback(() => {
    stop(); setShown(0);
    backtest.annees.forEach((_, i) => at(400 + i * 650, () => setShown(i + 1)));
  }, []);

  const go = useCallback((s: number) => {
    const next = Math.max(0, Math.min(STEPS.length - 1, s));
    stop(); setHover(null); setStep(next);
    if (next !== 2) setYear(null);
    if (next === 1 && price < Math.min(...pStars)) at(1900, () => animatePrice(START_PRICE, CONTRACT_PRICE));
    if (next >= 2 && price < Math.max(...pStars)) setPrice(CONTRACT_PRICE);
    if (next === 2) setYear(replay[0]);
    if (next === 3) reveal();
  }, [price, animatePrice, reveal]);

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
        <MapScene step={step} price={price} year={step === 2 ? year : null} selectKm={step === 4 ? target.km : null} onHover={setHover} />
        <div className="map-caption">
          {step === 0
            ? <><b>Surface en lentille par département, 2025</b><span>Agreste, Statistique agricole annuelle</span></>
            : <><b>{fmt(meta.n_candidates)} parcelles de blé tendre d’hiver en Île-de-France</b><span>Registre parcellaire graphique 2025, IGN</span></>}
        </div>
        {step === 2 && year && <div className="map-year" key={year.annee}>{year.annee}</div>}
        <div className="map-legend">
          {step === 0 ? (
            <div className="ramp"><span>0 ha</span><i /><span>{fmt(Math.max(...Object.values(surf)))} ha</span></div>
          ) : (
            <ul>
              <li><i className={step === 4 ? 'sw wheat-dim' : 'sw wheat'} />Blé tendre d’hiver</li>
              <li><i className="sw lentil" />{step === 4 ? `Parcelles du contrat de ${fmt(VOLUME)} t` : 'Bascule en lentille'}</li>
              {step === 2 && <li><i className="sw fail" />Contrat non tenu</li>}
              <li><i className="sw slate" />Lentille déjà cultivée</li>
              <li><i className="sw site" />Site acheteur fictif</li>
            </ul>
          )}
        </div>
        {hover && (
          <div className="map-tip">
            {hover.kind === 'dep' ? (
              <><b>{hover.name}</b>{fmt(hover.surface)} ha de lentilles en 2025</>
            ) : (
              <>
                <b>{hover.p.culture === 'ble' ? 'Blé tendre d’hiver' : 'Lentille déjà cultivée'}, {DEP_NAMES[hover.p.dep]}</b>
                {dec(hover.p.surface)} ha, à {fmt(hover.p.dist)} km du site. Bascule à {fmt(hover.p.pRendu)} €/t rendu.
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
                <PriceChart price={price} min={MIN} max={MAX} />
                <Source k="modele">20 000 années rejouées : météo et prix du blé de 2010 à 2025. Référence historique du prix de la lentille : Eurostat, {MARKET.annees[0]}–{MARKET.annees[1]}.</Source>
              </div>
              <p className="pull">À la référence historique de {fmt(MARKET.min)} à {fmt(MARKET.max)} €/t, la lentille ne gagne que {dec(REL_MARKET * 10, 1)} années sur 10. Pour 8 sur 10, il faut {fmt(D77.p_star)} €/t en Seine-et-Marne.</p>
              <div className="block">
                <h3>Les contrats récents, pour comparer</h3>
                <table className="list">
                  <tbody>
                    <tr><td>Unéal, avec Vivien Paille<span>lentilles valorisées, décembre 2023</span></td><td className="num">900 €/t</td></tr>
                    <tr><td>NatUp, contrat triennal<span>première tonne par hectare, septembre 2025</span></td><td className="num">1 000 €</td></tr>
                  </tbody>
                </table>
                <Source k="source">Communiqués Unéal (12/12/2023) et NatUp (18/09/2025). Ces contrats partagent déjà une part du risque ; l’outil mesure la protection qu’ils offrent.</Source>
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
                <Source k="modele">Backtest glissant sur {G.n_cas} cas département × année. Aucune année test n’a servi à l’entraînement ni au réglage.</Source>
              </div>
              <p className="body">Les contrats cèdent en 2020 et 2021 : deux effondrements que le modèle n’avait jamais vus.</p>
              <div className="block">
                <h3>Ce que le modèle apporte au prix</h3>
                <table className="list models">
                  <thead><tr><th>Façon de fixer le prix</th><th className="num">Contrats tenus</th></tr></thead>
                  <tbody>
                    <tr><td>Prix calculé sur les moyennes<span>référence naïve, sans modèle</span></td><td className="num bad">{pct(G.taux_tenus_moyenne)}</td></tr>
                    <tr><td>Distribution calibrée, sans météo<span>tendance seule</span></td><td className="num">{pct(G.taux_tenus_M0)}</td></tr>
                    <tr className="hl"><td>Régression quantile avec météo<span>modèle d’apprentissage retenu avant tout résultat</span></td><td className="num">{pct(G.taux_tenus)}</td></tr>
                    <tr><td>LightGBM avec météo<span>gradient boosting</span></td><td className="num bad">{pct(G.taux_tenus_M2)}</td></tr>
                  </tbody>
                </table>
                <p className="body small">Un prix calculé sur les rendements et les prix moyens n’aurait tenu que {pct(G.taux_tenus_moyenne)} des contrats : la moyenne ignore la mauvaise année. Une distribution calibrée dépasse 8 sur 10, et la météo y ajoute encore des points. LightGBM, plus précis sur l’année moyenne, sous-estime les mauvaises années.</p>
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
                  <dt>Prix plancher</dt><dd><b>{fmt(D77.p_star)} €/t</b> départ ferme en Seine-et-Marne, payé sur les tonnes acceptées au tri pour l’alimentation humaine.</dd>
                  <dt>Ce qu’il garantit</dt><dd>Une marge au moins égale à celle du blé dans {pct(H.tau)} des années simulées.</dd>
                  <dt>Ce qu’il ne garantit pas</dt><dd>Une récolte effondrée réduit la marge : {dec(D77.rendement_lentille_q10_tha, 2)} t/ha ou moins une année sur dix. Les lots refusés au tri ne sont pas payés au prix garanti.</dd>
                  <dt>Volume visé</dt><dd>{target.reached
                    ? <><b>{fmt(VOLUME)} t</b> acceptées, soit {pct(VOLUME / L25.importations_t)} des importations de 2025, sur {fmt(target.ha)} ha : les {fmt(target.n)} parcelles éligibles les plus proches du site, à moins de {fmt(target.km)} km.</>
                    : <>Le prix est trop bas pour réunir {fmt(VOLUME)} t. Remontez-le à l’étape 2.</>}</dd>
                </dl>
                <Source k="modele">Texte assemblé à partir des chiffres calculés, sans aucun chiffre ajouté. Volumes : hypothèses de l’équipe.</Source>
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
