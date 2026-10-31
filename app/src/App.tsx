import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import MapScene, { type Hover } from './components/MapScene';
import Method from './components/Method';
import { BacktestReveal, MarginBars, PriceChart, SecurityChart, Sensitivity, YieldsChart } from './components/charts';
import { Figure, Source } from './components/ui';
import {
  backtest, BUYER_DEFAULTS, CHALLENGER, D77, DEP_NAMES, dec, farmPrice, FEATURE_LABELS, fmt, H, held, MAIN_MODEL, MARKET, meta, parcels, pct, REFERENCE_DISTANCE, reliabilityAt, replay,
  signedPct, thresholds, type ReplayYear,
} from './data';
import { useTween } from './useTween';

const STEPS = ['Le verrou', 'Le prix', 'L’épreuve', 'La preuve', 'Le contrat'];
const pStars = thresholds.par_departement.map((d) => d.p_star);
const MIN = 600;
const MAX = Math.ceil(Math.max(3000, ...pStars.map((p) => p + Math.max(...parcels.map((p) => p.dist)) * H.kappa)) * 1.15 / 500) * 500;
const G = backtest.global as typeof backtest.global & { erreur_mediane_auto?: number };
const L25 = meta.lentille_2025;
const surf = meta.surface_lentille_par_dep_2025 as Record<string, number>;
const IDF_LENTIL_HA = ['77', '78', '91', '95'].reduce((a, d) => a + (surf[d] ?? 0), 0);
const CONTRACT_PRICE = Math.ceil((Math.max(...pStars) + 30) / 10) * 10;
const VOLUME = (meta.hypotheses as any).volume_vise_t.valeur as number;
const ECON = (backtest as any).economie as Record<string, { taux_tenus: number; prix_median_eur_t: number; manque_moyen_eur_ha: number; cout_achat_moyen_eur_ha: number }> | undefined;
const METHOD_NAMES: Record<string, string> = { moyenne: 'Moyennes passées', historique: 'Quantile historique apparié', M0: 'M0 · Tendance sans météo', M1: 'M1 · Régression quantile météo', M2: 'M2 · LightGBM', M3: 'M3 · Ensemble de quantiles', auto: 'Sélection temporelle automatique' };
const PRICE_FOR_VOLUME = (() => {
  let tonnes = 0;
  for (const p of parcels.filter((p) => p.culture === 'ble').sort((a, b) => a.pRendu - b.pRendu)) {
    tonnes += p.tonnes;
    if (tonnes >= VOLUME) return p.pRendu;
  }
  return Infinity;
})();
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
  const [buyer, setBuyer] = useState(BUYER_DEFAULTS);
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
    const selected = new Set<string>();
    for (const p of elig) {
      if (t >= VOLUME) break;
      t += p.tonnes; ha += p.surface; n++; km = p.dist; selected.add(p.id);
    }
    return { ha, n, km, tonnes: t, selected, reached: t >= VOLUME };
  }, [price]);

  const targetKept = useMemo(() => year ? parcels.filter((p) => target.selected.has(p.id) && held(p, price, year)).length : 0, [target, year, price]);
  const buyerCeiling = buyer.resale * (1 - buyer.loss) - buyer.sorting - buyer.processing - buyer.other - buyer.margin;
  const canAgree = buyerCeiling >= PRICE_FOR_VOLUME;
  const offerFeasible = target.reached && price <= buyerCeiling;

  const animatePrice = useCallback((from: number, to: number, ms = 5600) => {
    stop();
    const n = Math.max(1, Math.round(Math.abs(to - from) / 5));
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
    if (next === 2) setYear(replay[0]);
    if (next === 3) reveal();
  }, [reveal]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA' || tag === 'BUTTON') return;
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
        <MapScene step={step} price={price} year={step === 2 ? year : null} selectedIds={step === 4 || step === 2 ? target.selected : null} onHover={setHover} />
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
              <p className="lead">Faites varier l’offre hypothétique de l’acheteur. Une parcelle devient éligible quand ce prix, transport déduit, atteint le seuil simulé de son département.</p>
              <div className="block control">
                <label htmlFor="price">Prix proposé par l’acheteur, rendu au site</label>
                <div className="readout">
                  <output htmlFor="price">{fmt(price)}<span className="unit">€/t</span></output>
                  <p><b>{dec(rel * 10, 1)} années sur 10</b> dans les simulations pour une parcelle de Seine‑et‑Marne à {fmt(REFERENCE_DISTANCE)} km du site</p>
                </div>
                <div className="range">
                  <input id="price" type="range" min={MIN} max={MAX} step={5} value={price} style={{ ['--fill' as any]: pos(price) }}
                    onChange={(e) => { stop(); setPrice(+e.target.value); }} />
                  <div className="range-marks" aria-hidden="true">
                    <span className="mk-tick" style={{ left: pos(D77.p_star + H.kappa * REFERENCE_DISTANCE) }} />
                    <span className="mk-label" style={{ left: pos(D77.p_star + H.kappa * REFERENCE_DISTANCE) }}>8 sur 10</span>
                  </div>
                </div>
                <p className="body small">Scénario hypothétique : {fmt(farmPrice(price, REFERENCE_DISTANCE))} €/t départ ferme après {dec(H.kappa * REFERENCE_DISTANCE)} €/t de transport pour ce trajet. Aide non confirmée exclue du scénario principal.</p>
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
                <Source k="modele">20 000 scénarios simulés à partir des années 2010–2025. Prix du blé de référence reconstruit à partir d’Eurostat et d’Agreste. Modèle sélectionné avant calibration : {MAIN_MODEL}.</Source>
              </div>
              <p className="pull">Référence historique nominale {MARKET.annees[0]}–{MARKET.annees[1]} : {fmt(MARKET.min)}–{fmt(MARKET.max)} €/t. Elle n’est pas représentative d’une cotation actuelle. Le prix proposé ci-dessus est une hypothèse de négociation.</p>
              <div className="block">
                <h3>Prix plancher départ ferme par département</h3>
                <table className="list">
                  <tbody>
                    {thresholds.par_departement.map((d) => (
                      <tr key={d.dep}><td>{DEP_NAMES[d.dep]}</td><td className="num">{fmt(d.p_star)} €/t</td></tr>
                    ))}
                  </tbody>
                </table>
                <Source k="modele">Quantile 80 % du prix d’équilibre lentille / blé. Niveau de rendement de la lentille emprunté aux départements producteurs voisins.{IC77 && <> Sensibilité aux années rejouées, modèles figés (10–90 %), Seine-et-Marne : {fmt(IC77[0])}–{fmt(IC77[1])} €/t. Elle exclut l’erreur de réestimation.</>}</Source>
              </div>
              <button className="link" onClick={() => animatePrice(START_PRICE, CONTRACT_PRICE)}>Rejouer la bascule</button>
            </>
          )}

          {step === 2 && (
            <>
              <h1>Et si la récolte tourne mal ?</h1>
              <p className="lead">Deux scénarios de stress appliquent des chocs d’années passées aux {fmt(target.n)} parcelles sélectionnées pour le même contrat à {fmt(price)} €/t rendu. Le transport est déduit parcelle par parcelle. C’est une reconstitution sous les hypothèses économiques affichées.</p>
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
                      <Figure value={fmt(year.prix_ble)} unit="€/t" label="prix du blé de référence reconstruit" />
                    </div>
                    <Source k="mesure">Agreste, écart à la moyenne des cinq années précédentes ; Eurostat, indice des prix du blé tendre.</Source>
                  </div>
                  <div className="block">
                    <h3>Marge par hectare à {fmt(REFERENCE_DISTANCE)} km du site, Seine-et-Marne, {year.annee}</h3>
                    <MarginBars
                      lentil={farmPrice(price, REFERENCE_DISTANCE) * year.par_departement['77'].rendement_lentille_tha - H.chargesLentille + H.aide + H.rotation}
                      wheat={year.prix_ble * year.par_departement['77'].rendement_ble_tha - H.chargesBle} />
                    <Source k="modele">Transport déduit sur le trajet de référence ; charges constantes et aide non confirmée exclue. Rendement du blé observé, prix de référence reconstruit à partir d’Eurostat et d’Agreste.</Source>
                  </div>
                  <div className="block verdict">
                    <div className="verdict-v">{target.n ? pct(targetKept / target.n) : '—'}</div>
                    <p>des {fmt(target.n)} parcelles sélectionnées auraient rapporté au moins autant qu’en blé avec ces hypothèses.</p>
                  </div>
                  <p className="body">{target.n ? `Sur les parcelles sélectionnées, ${fmt(target.n - targetKept)} auraient présenté un manque à gagner face au blé dans cette reconstitution.` : 'Aucune parcelle n’est éligible au prix proposé. Modifiez le prix à l’étape 2.'} Le volume attendu est {fmt(target.tonnes)} t ; la récolte réalisée reste incertaine.</p>
                  <Source k="modele">Scénario de stress, distinct du backtest : choc national passé de la lentille appliqué au rendement moyen du modèle actuel en Île-de-France.</Source>
                </>
              )}
            </>
          )}

          {step === 3 && (
            <>
              <h1>Le modèle tient-il sur des années qu’il n’a jamais vues ?</h1>
              <p className="lead">Pour chaque année de 2019 à 2025, la procédure apprend et fixe son prix avec les années antérieures. Les marges sont ensuite reconstituées sur la récolte test. Le diagnostic conditionnel de rendement utilise séparément la météo test observée rétrospectivement.</p>
              <div className="block">
                <h3>Rendement normalisé par département : intervalle visé à 80 % et observation</h3>
                <BacktestReveal shown={shown} />
                <p className="chart-key"><i className="k-int" />intervalle prédit <i className="k-ok" />réel, dans l’intervalle <i className="k-ko" />réel, en dehors</p>
              </div>
              <div className="block">
                <div className="figures">
                  <Figure value={pct(G.taux_tenus_auto)} label={`des cas de la sélection automatique atteignent la marge du blé, pour ${pct(backtest.fiabilite_visee)} visés`} />
                  <Figure value={pct(G.couverture_auto)} label="des récoltes dans l’intervalle automatique visé à 80 %" />
                  <Figure value={dec(G.erreur_mediane_auto ?? G.erreur_mediane_M1, 3)} label="erreur absolue médiane sur le rendement normalisé" />
                </div>
                <table className="years">
                  <thead><tr><th />{backtest.annees.map((y) => <th key={y.annee}>{y.annee}</th>)}</tr></thead>
                  <tbody>
                    <tr><td>Contrats tenus</td>{backtest.annees.map((y, i) => <td key={y.annee} className={i < shown ? ((y.taux_tenus_auto ?? 0) >= 0.8 ? '' : 'bad') : 'hide'}>{i < shown ? pct(y.taux_tenus_auto ?? 0) : '·'}</td>)}</tr>
                    <tr><td>Prix du blé, €/t</td>{backtest.annees.map((y) => <td key={y.annee}>{fmt(y.prix_ble)}</td>)}</tr>
                  </tbody>
                </table>
                <Source k="modele">Backtest glissant sur {G.n_cas} cas département × année. Les transformations, la sélection et la calibration utilisent les années antérieures. Ce résultat ne constitue pas une garantie individuelle pour une exploitation.</Source>
              </div>
              <p className="body">{G.taux_tenus_auto < backtest.fiabilite_visee && <b>La sélection automatique n’atteint pas l’objectif de {pct(backtest.fiabilite_visee)} sur le backtest : {pct(G.taux_tenus_auto)} des cas atteignent la marge du blé. </b>}La couverture d’un intervalle et le succès économique répondent à deux questions différentes. Une méthode peut protéger davantage simplement en demandant un prix plus élevé.</p>
              <div className="block">
                <h3>Prix payé et pertes résiduelles</h3>
                <div className="table-scroll"><table className="list models economics">
                  <thead><tr><th>Méthode</th><th className="num">Succès</th><th className="num">Prix médian<br />€/t</th><th className="num">Manque moyen<br />€/ha</th><th className="num">Achat moyen<br />€/ha</th></tr></thead>
                  <tbody>{ECON && ['moyenne', 'historique', 'M0', 'M1', 'M2', 'M3', 'auto'].filter((k) => ECON[k]).map((k) => (
                    <tr key={k} className={k === 'auto' ? 'hl' : ''}><td>{METHOD_NAMES[k]}</td><td className="num">{pct(ECON[k].taux_tenus)}</td><td className="num">{fmt(ECON[k].prix_median_eur_t)}</td><td className="num">{fmt(ECON[k].manque_moyen_eur_ha)}</td><td className="num">{fmt(ECON[k].cout_achat_moyen_eur_ha)}</td></tr>
                  ))}</tbody>
                </table></div>
                <p className="body small">Les méthodes quantiles visent une protection de {pct(backtest.fiabilite_visee)}, sans nécessairement l’atteindre hors échantillon. Le prix fondé sur les moyennes n’a pas de cible de protection. Le manque est la perte de marge face au blé, ramenée à tous les cas, y compris ceux sans perte. Le coût d’achat est le prix multiplié par le rendement réalisé. La météo doit justifier son coût face aux références simples.</p>
                <Source k="modele">Reconstitution sous hypothèses économiques fixes sur {G.n_cas} cas. Prix départ ferme, aide non confirmée exclue. M0–M3 désignent le modèle lentille ; le modèle du blé est commun, sélectionné automatiquement. La référence historique sans météo conserve les années lentille, blé et prix appariées. Ces taux ne sont pas directement comparables à ceux des anciennes versions.</Source>
              </div>
              <div className="block">
                <h3>Variables utilisées par le challenger LightGBM</h3>
                <div className="bars imp">
                  {CHALLENGER.importances_q50.map((f) => (
                    <div key={f.variable} className="bar-row">
                      <span className="bar-l">{FEATURE_LABELS[f.variable] ?? f.variable}</span>
                      <span className="bar-track"><span className={`bar ${f.variable === 'tendance' ? 'neutral' : 'lentil'}`} style={{ width: `${(f.part / CHALLENGER.importances_q50[0].part) * 100}%` }} /></span>
                      <b className="bar-v">{pct(f.part)}</b>
                    </div>
                  ))}
                </div>
                <Source k="modele">Part de chaque variable dans l’apprentissage de LightGBM (gain, rendement médian). Météo journalière NASA POWER. Transformations estimées sur l’apprentissage seul. Ces importances ne mesurent pas des effets causaux.</Source>
              </div>
              <button className="link" onClick={reveal}>Rejouer la révélation</button>
            </>
          )}

          {step === 4 && (
            <>
              <h1>Un contrat soutenable pour les deux parties ?</h1>
              <div className="block buyer">
                <h3>Plafond économique de l’acheteur</h3>
                <p className="body small">Hypothèses modifiables, sans valeur de cotation. La revente concerne une tonne commercialisable ; les coûts et la marge minimale sont exprimés par tonne de récolte livrée.</p>
                <div className="buyer-inputs">
                  {([
                    ['resale', 'Prix de revente', '€/t commercialisable', 1],
                    ['loss', 'Pertes au tri', '%', 0.01],
                    ['sorting', 'Coût du tri', '€/t livrée', 1],
                    ['processing', 'Transformation', '€/t livrée', 1],
                    ['other', 'Autres coûts acheteur', '€/t livrée', 1],
                    ['margin', 'Marge minimale', '€/t livrée', 1],
                  ] as const).map(([key, label, unit, increment]) => <label key={key}>{label}<span><input type="number" min={0} max={key === 'loss' ? 100 : undefined} step={key === 'loss' ? 1 : increment} value={key === 'loss' ? Math.round(buyer[key] * 100) : buyer[key]} onChange={(e) => setBuyer((b) => ({ ...b, [key]: key === 'loss' ? Math.min(1, Math.max(0, Number(e.target.value) / 100)) : Math.max(0, Number(e.target.value)) }))} />{unit}</span></label>)}
                </div>
                <div className="figures two">
                  <Figure value={Number.isFinite(PRICE_FOR_VOLUME) ? fmt(PRICE_FOR_VOLUME) : '—'} unit="€/t" label={`prix rendu minimal pour mobiliser ${fmt(VOLUME)} t attendues`} />
                  <Figure value={fmt(buyerCeiling)} unit="€/t" label="prix rendu maximal supportable par l’acheteur" />
                </div>
                <p className={`agreement ${canAgree ? 'possible' : 'impossible'}`}><b>{canAgree ? 'Accord possible dans ce scénario' : 'Accord impossible dans ce scénario'}</b><br />{canAgree ? `Une plage de négociation existe entre ${fmt(PRICE_FOR_VOLUME)} et ${fmt(buyerCeiling)} €/t rendu.` : 'Le plafond acheteur ne finance pas le prix requis pour le volume attendu.'}</p>
                <Source k="suppose">Plafond = revente × (1 − pertes au tri) − tri − transformation − autres coûts − marge minimale. Ce calcul ne valide ni les débouchés ni les coûts réels de la coopérative.</Source>
              </div>
              <div className="block contract">
                <p className="contract-title">Proposition hypothétique, campagne {meta.campagne}</p>
                <label className="offer-control">Prix proposé, €/t rendu au site<input type="number" min={MIN} max={MAX} step={5} value={price} onChange={(e) => { stop(); setPrice(Math.min(MAX, Math.max(MIN, Number(e.target.value)))); }} /></label>
                <dl>
                  <dt>Objet et durée</dt><dd>Achat de lentilles pour l’alimentation humaine, une seule campagne : {meta.campagne}.</dd>
                  <dt>Territoire</dt><dd>Parcelles de blé sélectionnées en Île-de-France, les plus proches du site acheteur fictif.</dd>
                  <dt>Prix proposé</dt><dd><b>{fmt(price)} €/t rendu au site</b>. Le revenu départ ferme est ce prix moins {dec(H.kappa, 2)} €/t/km de transport, selon la distance de chaque parcelle.</dd>
                  <dt>Objectif producteur</dt><dd>Atteindre la marge du blé dans {pct(H.tau)} des scénarios simulés pour chaque parcelle retenue ; aucune garantie individuelle de rendement ou de marge.</dd>
                  <dt>Volume attendu</dt><dd>{target.reached
                    ? <><b>{fmt(target.tonnes)} t</b> attendues pour {fmt(VOLUME)} t visées, sur {fmt(target.ha)} ha : {fmt(target.n)} parcelles, jusqu’à {fmt(target.km)} km du site. L’arrondi aux parcelles entières peut dépasser l’objectif.</>
                    : <>{fmt(target.tonnes)} t attendues pour {fmt(VOLUME)} t visées. Le prix proposé ne mobilise pas assez de parcelles.</>}</dd>
                  <dt>Coût d’achat attendu</dt><dd>{fmt(price * target.tonnes)} € pour le volume sélectionné, avant tri et transformation.</dd>
                  <dt>Viabilité de cette offre</dt><dd><b>{offerFeasible ? 'Compatible avec les deux objectifs affichés' : 'Offre à réviser'}</b>. {!target.reached ? 'Volume attendu insuffisant. ' : ''}{price > buyerCeiling ? 'Le prix dépasse le plafond acheteur.' : 'Prix compatible avec la marge minimale acheteur sous ces hypothèses.'}</dd>
                </dl>
                <Source k="modele">Même prix, sélection, transport et campagne que les étapes précédentes. Rendements attendus simulés ; volume non garanti. Aide principale : {fmt(H.aide)} €/ha.</Source>
              </div>
              <div className="block">
                <h3>Le prix de la sécurité</h3>
                <p className="body small">Prix plancher départ ferme en Seine-et-Marne selon la protection visée dans les simulations. La référence nominale 2012–2016 ne décrit pas les conditions du marché actuel.</p>
                <SecurityChart />
                <Source k="modele">Même simulation, quantile variable.</Source>
              </div>
              <div className="block">
                <h3>Ce qui fait bouger le prix plancher</h3>
                <Sensitivity />
                <Source k="modele">Aide principale nulle ; scénario avec 122 €/ha sous réserve d’éligibilité. Charges de référence et bonus de rotation affichés dans Méthode et sources.</Source>
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
                <Source k="modele">Même calcul, avec les rendements propres à chaque département producteur. Le prix plancher baisse là où le blé rend moins.</Source>
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
