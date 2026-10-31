import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import MapScene, { PSTAR_RANGE, type Camera, type FranceMode, type Hover } from './components/MapScene';
import Method from './components/Method';
import { BacktestReveal, MarginBars, PriceChart, SeasonChart, SecurityChart, Sensitivity } from './components/charts';
import { Bowls, ContractsRow, Filiere, Gauge, HarvestBars, YearsIcons } from './components/pitch';
import { Figure, Source } from './components/ui';
import {
  backtest, bestSite, CHALLENGER, CODE_LABELS, CONTRATS, CULTURES, D77, DEP_NAMES, dec, FEATURE_LABELS, fmt, H, held, lettre, MAILLON, MARKET, meta,
  NAF_LABELS, parcels, pct, pctFine, PITCH, reliabilityAt, replay, SAISON, signedPct, siteGeo, SITE_SCENARIO, SITES, SUIVI, supplyCurve, targetParcels, thresholds,
  truckTrips, type MaillonCat, type MaillonVersion, type ReplayYear, type Statut, type TruckTrip,
} from './data';
import { useTween } from './useTween';

// Le parcours de présentation : six écrans, 4 minutes.
type MainId = 'constat' | 'pari' | 'filiere' | 'prix' | 'preuve' | 'impact';
type AnnexId = 'a_prix' | 'a_epreuve' | 'a_preuve' | 'a_contrat' | 'a_saison' | 'a_ciel';
type ViewId = MainId | AnnexId;
const MAIN: { id: MainId; label: string }[] = [
  { id: 'constat', label: 'Le constat' },
  { id: 'pari', label: 'Le pari' },
  { id: 'filiere', label: 'Le contrat' },
  { id: 'prix', label: 'Le prix' },
  { id: 'preuve', label: 'La preuve' },
  { id: 'impact', label: 'L’impact' },
];
// Les écrans détaillés, gardés pour les questions du jury ; `legacy` reprend leur ancien numéro d'étape.
const ANNEXES: { id: AnnexId; label: string; legacy: number }[] = [
  { id: 'a_prix', label: 'Le prix, en détail', legacy: 1 },
  { id: 'a_epreuve', label: 'Deux mauvaises années, rejouées', legacy: 2 },
  { id: 'a_preuve', label: 'Le test, en détail', legacy: 3 },
  { id: 'a_contrat', label: 'La proposition de contrat', legacy: 4 },
  { id: 'a_saison', label: 'La saison, vue par satellite', legacy: 5 },
  { id: 'a_ciel', label: 'Vu du ciel', legacy: 6 },
];

const pStars = thresholds.par_departement.map((d) => d.p_star);
const MIN = 600;
const MAX = 2000;
const G = backtest.global;
const L25 = meta.lentille_2025;
const surf = meta.surface_lentille_par_dep_2025 as Record<string, number>;
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

// Chiffres du parcours, tous lus dans les exports du pipeline.
const VP = H.volumes.pilote;
const VA = H.volumes.ambition;
const UNEAL = CONTRATS.existants.find((c) => c.id === 'uneal_2023') as any;
const UNEAL_PRICE = (UNEAL?.prix ?? START_PRICE) as number;
const UNEAL_LOSSES = 10 - Math.round(((UNEAL?.simulation?.protection as number | undefined) ?? reliabilityAt(UNEAL_PRICE)) * 10);
const wins = (p: number) => Math.round(reliabilityAt(p) * 10);
const round1000 = (x: number) => Math.round(x / 1000) * 1000;
const keur = (x: number) => `${fmt(x / 1000)}\u00a0k€`;
const IDX = CONTRATS.indexe;
const IDX_BT = CULTURES.find((c) => c.id === 'lentille')!.backtest.taux_tenus_indexe ?? 0;
const IDX_200 = IDX.plancher_par_prix_ble.find((r) => r.prix_ble === 200)!.plancher;
const FIXE_PAR_BLE = thresholds.sensibilite.prix_ble_fixe as { x: number; p_star: number }[];
// Mobilisation : part des parcelles éligibles qui signent réellement (hypothèse d'illustration).
const ADOPTION = 0.1;
const BT_CONTRATS: { id: string; label: string }[] = [
  { id: 'uneal_2023', label: 'Unéal 2023, 900 €/t' },
  { id: 'natup_2023', label: 'NatUp 2023–2024, 900 / 700 / 600' },
  { id: 'proposition_2027', label: 'Proposition du dossier pilote' },
  { id: 'unique', label: 'Prix unique calibré' },
  { id: 'paliers', label: 'Barème par tranches calibré' },
  { id: 'prime_ha', label: 'Prix de base et prime à l’hectare' },
];
const BT_ANNEES = [2020, 2021, 2022];
const ASSUR70 = CONTRATS.assurance.niveaux.find((n) => n.seuil === 0.7)!;
const FR_SORTED = [...(meta.france as { dep: string; nom: string; p_star: number }[])].sort((a, b) => a.p_star - b.p_star);
const btC = (a: number) => (backtest.annees.find((y) => y.annee === a) as any).contrats as Record<string, number>;
const frDate = (iso: string) => new Date(`${iso}T12:00:00`).toLocaleDateString('fr-FR');
const MAX_2020_21 = Math.max(...[2020, 2021].flatMap((a) => Object.values(btC(a))));
const FIXES_2022 = ['uneal_2023', 'natup_2023', 'proposition_2027'].map((k) => btC(2022)[k]);

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
  const idx = targetParcels(geo, price, volume);
  let t = 0, ha = 0, km = 0, tkm = 0;
  for (const i of idx) { t += parcels[i].tonnes; ha += parcels[i].surface; km = geo.dist[i]; tkm += parcels[i].tonnes * geo.dist[i]; }
  return { idx, ha, n: idx.length, km, meanKm: t ? tkm / t : 0, reached: t >= volume };
}
const pos = (p: number) => `${((p - MIN) / (MAX - MIN)) * 100}%`;

interface MapPlan {
  camera: Camera; radiusKm: number; showParcels: boolean; franceMode: FranceMode; btYear: number | null; depLabels: boolean;
  selectKm: number | null; silo: boolean; trucks: { key: string; trips: TruckTrip[] } | null; boats: boolean; price: number;
}

export default function App() {
  const [view, setView] = useState<ViewId>('constat');
  const [lastMain, setLastMain] = useState<MainId>('constat');
  const [annexOpen, setAnnexOpen] = useState(false);
  const [price, setPrice] = useState(START_PRICE);
  const [year, setYear] = useState<ReplayYear | null>(null);
  const [shown, setShown] = useState(0);
  const [seasonDay, setSeasonDay] = useState(SAISON.jours);
  const [focus, setFocus] = useState<string | null>(null);
  const [hover, setHover] = useState<Hover>(null);
  const [method, setMethod] = useState(false);
  const [volumeKey, setVolumeKey] = useState<'pilote' | 'ambition'>('pilote');
  const [maillonV, setMaillonV] = useState<MaillonVersion>('saison');
  const [btYear, setBtYear] = useState<number | null>(null);
  const [btShown, setBtShown] = useState(0);
  const [delivered, setDelivered] = useState(0);
  const [impactView, setImpactView] = useState<'bassin' | 'france'>('bassin');
  // Les camions partent une fois le prix posé, pas pendant que le curseur s'anime.
  const [priceAnim, setPriceAnim] = useState(false);
  const VOLUME = H.volumes[volumeKey];
  // Site de collecte : déplaçable d'un clic sur la carte dans les annexes « Le prix » et « La proposition ».
  const [geo, setGeo] = useState(SITE_SCENARIO);
  const [best, setBest] = useState<{ volume: number; site: [number, number] } | null>(null);
  // Site déplacé sur le meilleur établissement existant (Sirene) pour ce volume.
  const [bestReal, setBestReal] = useState<{ key: 'pilote' | 'ambition'; site: [number, number] } | null>(null);
  const moveSite = useCallback((site: [number, number]) => setGeo(siteGeo(site)), []);
  const supply = useMemo(() => supplyCurve(geo), [geo]);
  const timers = useRef<number[]>([]);
  const onDelivered = useCallback((f: number) => setDelivered(f), []);

  // Parcours de présentation : le texte de l'écran se réduit pour tenir sans défiler (projecteur 720p,
  // zoom système), jusqu'à 72 % ; les annexes, plus longues, gardent le défilement.
  const colRef = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => {
    const col = colRef.current;
    if (!col) return;
    const isAnnex = ANNEXES.some((a) => a.id === view);
    const fit = () => {
      col.style.setProperty('--fit', '1');
      if (isAnnex || window.innerWidth <= 900) return;
      // Les graphiques gardent leur hauteur (elle suit la largeur) : on réduit par étapes.
      let z = 1;
      for (let k = 0; k < 6 && z > 0.72; k++) {
        const need = col.scrollHeight, avail = col.clientHeight;
        if (need <= avail + 1) break;
        z = Math.max(0.72, Math.floor(z * (avail / need) * 100) / 100);
        col.style.setProperty('--fit', String(z));
      }
    };
    fit();
    const ts = [120, 700, 1600].map((ms) => window.setTimeout(fit, ms));
    document.fonts?.ready.then(fit);
    window.addEventListener('resize', fit);
    return () => { ts.forEach((x) => window.clearTimeout(x)); window.removeEventListener('resize', fit); };
  }, [view, impactView]);

  const mainIdx = MAIN.findIndex((m) => m.id === view);
  const annex = ANNEXES.find((a) => a.id === view);
  const annexIdx = annex ? ANNEXES.indexOf(annex) : -1;
  const legacy = annex ? annex.legacy : -1;

  const stop = () => { timers.current.forEach(clearTimeout); timers.current = []; setPriceAnim(false); };
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
  // Parcours : le pilote à l'écran « Le prix », l'ambition de bassin à l'écran « L'impact ».
  const targetP = useMemo(() => selectTarget(geo, price, VP), [price, geo]);
  const finalP = useMemo(() => selectTarget(geo, CONTRACT_PRICE, VP), [geo]);
  const targetA = useMemo(() => selectTarget(geo, CONTRACT_PRICE, VA), [geo]);
  const keyP = targetP.reached && !priceAnim ? `p-${targetP.n}-${targetP.km.toFixed(2)}-${geo.site.join(',')}` : null;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const tripsP = useMemo(() => (keyP ? { key: keyP, trips: truckTrips(targetP.idx, geo) } : null), [keyP]);
  const tripsA = useMemo(() => ({ key: `a-${targetA.n}-${geo.site.join(',')}`, trips: truckTrips(targetA.idx, geo) }), [targetA, geo]);

  const [busy, setBusy] = useState(false);
  const findBest = () => {
    setBusy(true);
    // Laisse le navigateur afficher « Calcul… » avant la recherche sur la grille.
    window.setTimeout(() => { const b = bestSite(VOLUME); moveSite(b.site); setBest({ volume: VOLUME, site: b.site }); setBusy(false); }, 30);
  };

  const animatePrice = useCallback((from: number, to: number, ms = 5600) => {
    stop(); setPriceAnim(true);
    const n = Math.max(1, Math.round((to - from) / 5));
    for (let i = 0; i <= n; i++) at((ms * i) / n, () => setPrice(Math.round(from + ((to - from) * i) / n)));
    at(ms + 50, () => setPriceAnim(false));
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

  const replayBacktest = useCallback(() => {
    stop(); setBtShown(0); setBtYear(null);
    // La première année se colore pendant le vol de la caméra : la carte n'est jamais vide.
    backtest.annees.forEach((y, i) => at(350 + i * 1250, () => { setBtYear(y.annee); setBtShown(i + 1); }));
  }, []);

  const replayPrice = useCallback(() => {
    stop(); setDelivered(0); setPrice(START_PRICE);
    at(1500, () => animatePrice(START_PRICE, CONTRACT_PRICE, 4200));
  }, [animatePrice]);

  const go = useCallback((v: ViewId) => {
    stop(); setHover(null); setAnnexOpen(false); setView(v);
    const lg = ANNEXES.find((a) => a.id === v)?.legacy ?? -1;
    if (lg < 0) setLastMain(v as MainId);
    if (lg !== 2) setYear(null);
    if (v === 'prix') replayPrice();
    if (v === 'impact') setImpactView('bassin');
    if ((v === 'preuve' || v === 'impact') && price < CONTRACT_PRICE) setPrice(CONTRACT_PRICE);
    if (v === 'preuve') replayBacktest();
    if (lg === 1 && price < Math.min(...pStars)) at(1900, () => animatePrice(START_PRICE, CONTRACT_PRICE));
    if (lg >= 2 && price < Math.max(...pStars)) setPrice(CONTRACT_PRICE);
    if (lg === 2) setYear(replay[0]);
    if (lg === 3) reveal();
    if (lg === 5) replaySeason();
  }, [price, animatePrice, reveal, replaySeason, replayBacktest, replayPrice]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      if (tag === 'INPUT' && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')) return;
      if (e.key === 'Escape') { setMethod(false); setAnnexOpen(false); return; }
      if (method) return;
      const move = (d: number) => {
        if (annex) {
          const k = annexIdx + d;
          go(k >= 0 && k < ANNEXES.length ? ANNEXES[k].id : lastMain);
        } else {
          const k = mainIdx + d;
          if (k >= 0 && k < MAIN.length) go(MAIN[k].id);
        }
      };
      if (e.key === ' ' || e.key === 'PageDown') { e.preventDefault(); move(e.shiftKey ? -1 : 1); }
      if (e.key === 'PageUp') { e.preventDefault(); move(-1); }
      if (e.key === 'ArrowRight') { stop(); setPrice((p) => Math.min(MAX, p + 10)); }
      if (e.key === 'ArrowLeft') { stop(); setPrice((p) => Math.max(MIN, p - 10)); }
      if (e.key === 'm') setMethod(true);
      // Écran 6 : F bascule entre le bassin et la carte de France.
      if ((e.key === 'f' || e.key === 'F') && view === 'impact') setImpactView((v) => (v === 'france' ? 'bassin' : 'france'));
      if (legacy === 2 && (e.key === '1' || e.key === '2')) setYear(replay[+e.key - 1]);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [go, method, annex, annexIdx, mainIdx, lastMain, legacy, view]);
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
  const w = wins(price);
  const onImpact = view === 'impact';
  const haA = useTween(onImpact ? targetA.ha : 0, 1500);
  const protA = useTween(onImpact ? VA * H.impact.proteines : 0, 1500);
  const azoteA = useTween(onImpact ? (targetA.ha * H.impact.azote) / 1000 : 0, 1500);
  const deliveredT = useTween(view === 'prix' && keyP ? delivered * VP : 0, 300);

  // Ce que montre la carte, écran par écran ; les annexes gardent le comportement des anciennes étapes.
  const base: MapPlan = {
    camera: 'idf', radiusKm: 6, showParcels: true, franceMode: 'surface', btYear: null, depLabels: false,
    selectKm: null, silo: false, trucks: null, boats: false, price,
  };
  const mp: MapPlan = view === 'constat' ? { ...base, camera: 'france', showParcels: false, boats: true }
    : view === 'pari' ? { ...base, price: 0 }
    : view === 'filiere' ? { ...base, camera: 'site', radiusKm: 14, price: 0, silo: true }
    : view === 'prix' ? { ...base, camera: 'site', radiusKm: Math.max(2.5, finalP.km * 1.3), selectKm: targetP.km, silo: true, trucks: tripsP }
    : view === 'preuve' ? { ...base, camera: 'france', showParcels: false, franceMode: 'backtest', btYear }
    : view === 'impact' && impactView === 'france' ? { ...base, camera: 'france', showParcels: false, franceMode: 'pstar' }
    : view === 'impact' ? { ...base, camera: 'site', radiusKm: Math.max(4, targetA.km * 1.05), selectKm: targetA.km, silo: true, trucks: tripsA, price: CONTRACT_PRICE }
    : { ...base, camera: legacy === 5 ? 'suivi' : legacy === 6 ? 'ciel' : 'idf', depLabels: legacy === 1, selectKm: legacy === 4 ? target.km : null };

  return (
    <div className="app">
      <header className="masthead">
        <div className="wordmark">Le Contrat qui Tient<span>Hack the Fork 2026 · Track 3</span></div>
        <nav className="steps" aria-label="Étapes">
          {MAIN.map((s, i) => (
            <button key={s.id} className={s.id === view ? 'on' : !annex && i < mainIdx ? 'done' : ''} onClick={() => go(s.id)} aria-current={s.id === view ? 'step' : undefined}>
              <span className="n">{i + 1}</span>{s.label}
            </button>
          ))}
        </nav>
        <div className="annex">
          <button className={`link${annex ? ' on' : ''}`} onClick={() => setAnnexOpen((o) => !o)} aria-expanded={annexOpen} aria-haspopup="menu">Annexes</button>
          {annexOpen && (
            <div className="annex-menu" role="menu">
              <p>Pour les questions du jury</p>
              {ANNEXES.map((a) => (
                <button key={a.id} role="menuitem" className={a.id === view ? 'on' : ''} onClick={() => go(a.id)}>{a.label}</button>
              ))}
            </div>
          )}
        </div>
        <button className="link" onClick={() => setMethod(true)}>Méthode et sources</button>
      </header>

      <main className="map">
        <MapScene camera={mp.camera} radiusKm={mp.radiusKm} showParcels={mp.showParcels} franceMode={mp.franceMode} btYear={mp.btYear}
          depLabels={mp.depLabels} price={mp.price} year={legacy === 2 ? year : null} selectKm={mp.selectKm} onHover={setHover}
          geo={legacy === 6 ? SITE_SCENARIO : geo} onPickSite={legacy === 1 || legacy === 4 ? (s) => { moveSite(s); setBest(null); setBestReal(null); } : undefined}
          sites={legacy === 4 || legacy === 6}
          season={legacy === 5 ? seasonDay : null} focus={focus} maillon={legacy === 6 ? maillonV : null}
          silo={mp.silo} trucks={mp.trucks} boats={mp.boats} onDelivered={onDelivered} />
        <div className="map-caption">
          {view === 'constat' ? <><b>Où poussent les lentilles françaises, 2025</b><span>Agreste, Statistique agricole annuelle ; cargos : illustration des importations</span></>
            : view === 'pari' ? <><b>{fmt(meta.n_candidates)} parcelles de blé tendre d’hiver en Île-de-France</b><span>Registre parcellaire graphique 2025, IGN</span></>
            : view === 'filiere' ? <><b>Le silo de la coopérative, au milieu des parcelles de blé</b><span>Site de collecte fictif, en Seine-et-Marne ; registre parcellaire 2025, IGN</span></>
            : view === 'prix' ? <><b>{targetP.reached ? `${fmt(targetP.n)} parcelles retenues pour ${fmt(VP)}\u00a0t, à moins de ${fmt(Math.max(1, targetP.km))}\u00a0km du silo` : targetP.n ? `${fmt(targetP.n)} parcelles acceptent ce prix\u00a0: pas encore ${fmt(VP)}\u00a0t` : 'À ce prix, aucune parcelle de blé ne bascule'}</b><span>Registre parcellaire 2025, IGN ; trajets schématiques</span></>
            : view === 'preuve' ? <><b>Départements producteurs testés{btYear ? `, ${btYear}` : ''}</b><span>Contrats tenus au prix fixé par le modèle, appris sur les seules années précédentes</span></>
            : view === 'impact' && impactView === 'france' ? <><b>Prix garanti nécessaire pour 8 années sur 10, par département producteur</b><span>Modèle : même calcul qu’en Seine-et-Marne, avec les rendements de chaque département</span></>
            : view === 'impact' ? <><b>{fmt(VA)} t sur les {fmt(targetA.n)} parcelles les plus proches du silo</b><span>Registre parcellaire 2025, IGN ; trajets schématiques</span></>
            : legacy === 5 ? <><b>{SUIVI.length} parcelles de lentille déclarées en {SAISON.annee}, près du site</b><span>NDVI Sentinel-2 L2A (Copernicus), replay de la saison {SAISON.annee}</span></>
            : legacy === 6 ? <><b>{fmt(M25.n_parcelles_zone)} parcelles d’au moins 1 ha sur {MAILLON.zoneKm} × {MAILLON.zoneKm} km autour du site, {MAILLON.campagne}</b><span>Sentinel-2 L2A (Copernicus) ; RPG {MAILLON.campagne}, IGN. Premier des cinq tirages de carrés connus.</span></>
            : <><b>{fmt(meta.n_candidates)} parcelles de blé tendre d’hiver en Île-de-France</b><span>Registre parcellaire graphique 2025, IGN</span></>}
        </div>
        {legacy === 2 && year && <div className="map-year" key={year.annee}>{year.annee}</div>}
        {view === 'preuve' && btYear && <div className="map-year" key={btYear}>{btYear}</div>}
        <div className="map-legend">
          {view === 'constat' ? (
            <ul>
              <li><span className="ramp"><span>lentille : 0 ha</span><i /><span>{fmt(Math.max(...Object.values(surf)))} ha par département</span></span></li>
              <li><i className="sw ink" />Cargo : importations, illustration</li>
            </ul>
          ) : view === 'pari' || view === 'filiere' ? (
            <ul>
              <li><i className="sw wheat" />Blé tendre d’hiver</li>
              <li><i className="sw slate" />Lentille déjà cultivée</li>
              {view === 'filiere' && <li><i className="sw ink" />Silo de la coopérative, fictif</li>}
            </ul>
          ) : view === 'impact' && impactView === 'france' ? (
            <ul>
              <li><span className="ramp pstar"><span>{fmt(PSTAR_RANGE[0])} €/t</span><i /><span>{fmt(PSTAR_RANGE[1])} €/t</span></span></li>
              <li><i className="sw pstar-pale" />Même rendement publié qu’un voisin</li>
              <li><i className="sw land" />Département non classé</li>
            </ul>
          ) : view === 'prix' || view === 'impact' ? (
            <ul>
              <li><i className="sw wheat-dim" />Blé tendre d’hiver</li>
              <li><i className="sw lentil" />Parcelles du contrat</li>
              <li><i className="sw truck" />Camion de lentilles, trajet schématique</li>
              <li><i className="sw ink" />Silo de la coopérative, fictif</li>
            </ul>
          ) : view === 'preuve' ? (
            <ul>
              <li><i className="sw lentil" />Contrat tenu</li>
              <li><i className="sw fail" />Contrat rompu</li>
              <li><i className="sw land" />Département non testé</li>
            </ul>
          ) : legacy === 5 ? (
            <div className="ramp ndvi"><span>sol nu</span><i /><span>végétation dense</span><span className="ramp-site"><span className="sw site" />Site de collecte</span></div>
          ) : legacy === 6 ? (
            <ul>
              <li><i className="sw lentil" />Légumineuse repérée</li>
              <li><i className="sw slate" />Légumineuse manquée</li>
              <li><i className="sw wheat" />Fausse alerte</li>
              <li><i className="sw wheat-dim" />Autre culture</li>
              <li><i className="sw known" />Carré connu du collecteur</li>
              <li><i className="sw site" />Site de collecte fictif</li>
              <li><i className="sw coop" />Coopérative existante</li>
              <li><i className="sw negoce" />Négociant existant</li>
            </ul>
          ) : (
            <ul>
              <li><i className={legacy === 4 ? 'sw wheat-dim' : 'sw wheat'} />Blé tendre d’hiver</li>
              <li><i className="sw lentil" />{legacy === 4 ? `Parcelles du contrat de ${fmt(VOLUME)} t` : 'Bascule en lentille'}</li>
              {legacy === 2 && <li><i className="sw fail" />Contrat non tenu</li>}
              <li><i className="sw slate" />Lentille déjà cultivée</li>
              <li><i className="sw site" />{geo === SITE_SCENARIO ? 'Site de collecte fictif' : 'Site de collecte déplacé'}</li>
              {legacy === 4 && <li><i className="sw coop" />Coopérative existante</li>}
              {legacy === 4 && <li><i className="sw negoce" />Négociant existant</li>}
            </ul>
          )}
        </div>
        {(legacy === 1 || legacy === 4) && <p className="map-hint">{legacy === 4 ? 'Cliquez sur la carte, ou sur un site existant, pour y placer la collecte' : 'Cliquez sur la carte pour déplacer le site de collecte'}</p>}
        {hover && (
          <div className="map-tip">
            {hover.kind === 'dep' ? (
              hover.pStar !== undefined
                ? <><b>{hover.name}</b>{fmt(hover.pStar)} €/t pour que la lentille batte le blé 8 années sur 10</>
                : hover.pstarMode && hover.avec
                  ? <><b>{hover.name}</b>Agreste publie le même rendement qu’en {hover.avec.rep} : prix calculé là-bas, {fmt(hover.avec.p)} €/t</>
                  : hover.pstarMode
                    ? <><b>{hover.name}</b>Non classé : moins de 50 ha de lentilles, ou rendement non mesuré</>
                    : <><b>{hover.name}</b>{fmt(hover.surface)} ha de lentilles en 2025</>
            ) : hover.kind === 'site' ? (
              <>
                <b>{hover.s.entreprise}</b>
                {hover.s.commune}, {hover.s.coop ? 'coopérative' : 'négociant'} ({NAF_LABELS[hover.s.naf] ?? hover.s.naf}).
                {legacy !== 6 && <> Pour {fmt(VOLUME)}&nbsp;t, parcelles de blé à {dec(hover.s.km[volumeKey], 1)} km en moyenne. Cliquez pour y placer la collecte.</>}
              </>
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
        <div className="column-body" key={view} ref={colRef}>
          <p className="kicker">{annex ? `Annexe · ${annex.label}` : `${mainIdx + 1} / ${MAIN.length} · ${MAIN[mainIdx].label}`}</p>

          {view === 'constat' && (
            <>
              <h1>Près d’une lentille sur deux mangée en France vient de l’étranger.</h1>
              <div className="block">
                <Bowls imported={Math.round(PITCH.partImportee * 10)} />
                <p className="picto-key"><span><i className="k-fr" />lentilles cultivées en France</span><span><i className="k-imp" />lentilles importées</span></p>
              </div>
              <div className="block">
                <div className="figures two">
                  <Figure value={fmt(round1000(PITCH.conso))} unit="t" label="de lentilles mangées en France chaque année" />
                  <Figure value={pct(PITCH.partImportee)} label={`importées, soit ${fmt(round1000(L25.importations_t))} t en 2025`} />
                </div>
                <Source k="mesure">Calcul sur 2025 : production Agreste ({fmt(L25.production_t)} t) + importations ({fmt(L25.importations_t)} t) − exportations ({fmt(L25.exportations_t)} t), Eurostat Comext ; stocks non comptés.</Source>
              </div>
              <p className="lead">Les champs français pourraient les produire. Pourquoi les agriculteurs n’en sèment-ils pas davantage ?</p>
            </>
          )}

          {view === 'pari' && (
            <>
              <h1>Avec le blé, l’agriculteur sait ce qu’il va gagner. Avec la lentille, non.</h1>
              <div className="block">
                <h3>Récolte par hectare en France, écart à une année moyenne</h3>
                <HarvestBars />
                <Source k="mesure">Agreste, rendements nationaux 2010–2025.</Source>
              </div>
              <div className="block">
                <div className="figures two">
                  <Figure value={`${dec(PITCH.rapportVariabilite, 0)} fois`} label="plus de variations pour la lentille que pour le blé" />
                  <Figure value={signedPct(PITCH.lentille2020)} label="récolte de lentille en 2020, face aux cinq années précédentes" />
                </div>
              </div>
              <p className="lead">Une mauvaise année de lentille efface sa marge. Rester au blé est le choix raisonnable.</p>
            </>
          )}

          {view === 'filiere' && (
            <>
              <h1>Un contrat peut retirer le risque. Encore faut-il le bon prix.</h1>
              <div className="block"><Filiere /></div>
              <p className="lead">La coopérative est l’entreprise des agriculteurs : elle collecte, trie, stocke et revend leurs récoltes. Avant les semis, elle peut leur garantir un prix minimum par tonne.</p>
              <div className="dilemma">
                <div><b>Prix trop bas</b>Les mauvaises années, l’agriculteur gagne moins qu’avec le blé. Il ne recommence pas.</div>
                <div><b>Prix trop haut</b>La coopérative perd de l’argent et ne peut plus vendre face aux importations.</div>
              </div>
            </>
          )}

          {view === 'prix' && (
            <>
              <h1>Le prix qui fait semer</h1>
              <div className="block control">
                <label htmlFor="price-main">Prix garanti, livré au silo</label>
                <div className="readout">
                  <output htmlFor="price-main">{fmt(price)}<span className="unit">€/t</span></output>
                  <p><b>{w} années sur 10</b>où la lentille rapporte au moins autant que le blé</p>
                </div>
                <div className="range">
                  <input id="price-main" type="range" min={MIN} max={MAX} step={5} value={price} style={{ ['--fill' as any]: pos(price) }}
                    onChange={(e) => { stop(); setPrice(+e.target.value); }} />
                  <div className="range-marks" aria-hidden="true">
                    <span className="mk-tick neutral" style={{ left: pos(UNEAL_PRICE) }} />
                    <span className="mk-label" style={{ left: pos(UNEAL_PRICE) }}>Unéal 2023</span>
                    <span className="mk-tick" style={{ left: pos(D77.p_star) }} />
                    <span className="mk-label" style={{ left: pos(D77.p_star) }}>8 sur 10</span>
                  </div>
                </div>
              </div>
              <div className="block">
                <YearsIcons wins={w} />
                <p className="picto-key"><span><i className="k-win" />la lentille rapporte au moins autant que le blé</span><span><i className="k-loss" />elle rapporte moins</span></p>
              </div>
              <div className="block">
                <div className="figures two">
                  <Figure value={fmt(deliveredT)} unit="t" label={`livrées au silo, pour ${fmt(VP)} t visées`} />
                  <Figure value={fmt(targetP.n)} unit="parcelles" label={targetP.n ? `${fmt(targetP.ha)} ha, à moins de ${fmt(Math.max(1, targetP.km))} km du silo` : 'aucune ne bascule à ce prix'} />
                </div>
              </div>
              <p className="body">À {fmt(UNEAL_PRICE)} €/t, le prix payé par Unéal en 2023, la lentille rapporte moins que le blé {UNEAL_LOSSES} années sur 10. Pour 8 sur 10, il faut {fmt(D77.p_star)} €/t en Seine-et-Marne. Payer plus cher la première tonne ({fmt(C_PALIERS.paliers![0])} €/t, puis {fmt(C_PALIERS.paliers![1])} et {fmt(C_PALIERS.paliers![2])}) protège autant, pour {saving(C_PALIERS.simulation.cout_moyen_t, C_UNIQUE.simulation.cout_moyen_t)} % de moins.</p>
              <Source k="modele">20 000 années simulées avec la météo et le prix du blé de 2010 à 2025. Parcelles du registre parcellaire 2025 ; silo fictif ; trajets schématiques.</Source>
              <button className="link" onClick={replayPrice}>Rejouer</button>
            </>
          )}

          {view === 'preuve' && (
            <>
              <h1>Testé sur des années que le modèle n’avait jamais vues</h1>
              <div className="block">
                <ContractsRow label="Prix fixé sur la moyenne, sans modèle" held={Math.round(G.taux_tenus_moyenne * 10)} value={pct(G.taux_tenus_moyenne)} />
                <ContractsRow label="Notre modèle" held={Math.round(G.taux_tenus * 10)} value={pct(G.taux_tenus)} delay={1500} />
                <Source k="modele">Contrats tenus, ramenés à 10 contrats : {G.n_cas} cas département × année, de 2019 à 2025, dans les départements producteurs.</Source>
              </div>
              <div className="block">
                <h3>Année par année, avec notre modèle</h3>
                <div className="chips">
                  {backtest.annees.map((y, i) => (
                    <div key={y.annee} className={`chip${i < btShown ? ' on' : ''}${(y.taux_tenus ?? 0) >= H.tau ? ' ok' : ' ko'}${y.annee === btYear ? ' cur' : ''}`}>
                      <b>{i < btShown ? pct(y.taux_tenus ?? 0) : '·'}</b><span>{y.annee}</span>
                    </div>
                  ))}
                </div>
              </div>
              <p className="body">Chaque année, le modèle n’apprend que sur les années d’avant, fixe le prix, puis on regarde la vraie récolte. Il relie la météo à la récolte et prévoit les mauvaises années, pas la moyenne. Sur une seule année, son erreur typique est de {Math.round(G.erreur_mediane_M1 * 100)} % : la promesse est de 8 années sur 10, pas de 10.</p>
              <Source k="modele">Régression quantile avec la météo NASA POWER, choisie avant tout résultat. LightGBM, plus précis sur l’année moyenne, ne tient que {pct(G.taux_tenus_M2)} des contrats.</Source>
              <button className="link" onClick={replayBacktest}>Rejouer</button>
            </>
          )}

          {view === 'impact' && (
            <>
              <h1>{fmt(VA)} tonnes produites ici, soit {pct(VA / L25.importations_t)} des importations</h1>
              <div className="tabs" role="tablist" aria-label="Échelle">
                <button role="tab" aria-selected={impactView === 'bassin'} className={impactView === 'bassin' ? 'on' : ''} onClick={() => setImpactView('bassin')}><b>Ce bassin</b>{fmt(VA)} t autour du silo</button>
                <button role="tab" aria-selected={impactView === 'france'} className={impactView === 'france' ? 'on' : ''} onClick={() => setImpactView('france')}><b>La France</b>{fmt(FR_SORTED.length)} départements producteurs</button>
              </div>
              {impactView === 'france' && (
                <p className="body">Le même calcul donne le prix de chaque département producteur : de {fmt(FR_SORTED[0].p_star)} €/t ({FR_SORTED[0].nom}) à {fmt(FR_SORTED[FR_SORTED.length - 1].p_star)} €/t ({FR_SORTED[FR_SORTED.length - 1].nom}). Là où le blé rend peu, la lentille gagne à moindre prix.</p>
              )}
              <div className="block">
                <Gauge value={VA / L25.importations_t} label={<>Part des {fmt(round1000(L25.importations_t))} t importées en 2025 que remplacerait le contrat</>} />
              </div>
              <div className="block">
                <div className="figures">
                  <Figure value={fmt(haA)} unit="ha" label="de blé passés à la lentille" />
                  <Figure value={fmt(protA)} unit="t" label="de protéines végétales" />
                  <Figure value={fmt(azoteA)} unit="t" label="d’azote minéral évité" />
                </div>
                <Source k="source">Par campagne. Protéines : 25 % du grain (Terres Inovia / Terres Univia). Azote : 180 kg N/ha sur blé en Île-de-France (Agreste 2021) ; {fmt(targetA.ha * H.impact.co2e)} t CO₂e d’émissions directes évitées (GIEC 2019, PRG100 de l’AR6).</Source>
              </div>
              <div className="block">
                <h3>Qui paie, et la suite</h3>
                <ul className="next-steps">
                  <li><b>Les coopératives et les conditionneurs</b>, à chaque campagne : ce prix se fixe tous les ans. {fmt(SITES.marche.cooperatives + SITES.marche.unions)} coopératives et unions font le commerce des grains en France.</li>
                  <li><b>Un pilote de {fmt(VP)} t</b> avec une coopérative, sur les parcelles les plus proches de son silo.</li>
                  <li><b>Le pois chiche, le haricot et les autres régions</b> : le même moteur, culture par culture et département par département.</li>
                  <li><b>Les assureurs</b> : avec la même distribution de récolte, une assurance rendement à {pct(ASSUR70.seuil)} coûte {fmt(ASSUR70.prime_pure_eur_ha)} €/ha de prime pure en Seine-et-Marne ; le sinistre survient {fmt(ASSUR70.frequence_sinistre * 10)} années sur 10.</li>
                </ul>
                <Source k="mesure">{fmt(SITES.marche.cooperatives)} coopératives agricoles et {fmt(SITES.marche.unions)} unions actives en NAF 46.21Z, Sirene (Insee), {frDate(SITES.marche.date_extraction)}.</Source>
                <Source k="modele">Prime pure hors chargements ; récolte à {fmt(CONTRATS.assurance.prix_assure_eur_t)} €/t, {dec(CONTRATS.assurance.rendement_moyen_tha, 2)} t/ha en moyenne simulée.</Source>
              </div>
            </>
          )}

          {legacy === 1 && (
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
                <div className="figures">
                  <Figure value={fmt(haT)} unit="ha" label={`de blé basculent à ce prix (${fmt(stats.n)} parcelles)`} />
                  <Figure value={fmt(stats.tonnes)} unit="t" label="de lentilles si toutes ces parcelles signaient" />
                  <Figure value={fmt(stats.tonnes * ADOPTION)} unit="t" label={`si ${fmt(ADOPTION * 100)}\u00a0% seulement signent`} />
                </div>
                <Source k="suppose">Mobilisation de {fmt(ADOPTION * 100)} % des parcelles éligibles : hypothèse d’illustration ; les parcelles éligibles et leurs tonnes sont des sorties du modèle.</Source>
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

          {legacy === 2 && (
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
                    <p className="body small">Dont {fmt(H.rotation)} €/ha de bénéfice de rotation, gagné sur le blé de l’année suivante. Sur la campagne seule, la lentille sous contrat dégage {fmt(price * year.par_departement['77'].rendement_lentille_tha * (1 - H.qualite) - H.chargesLentille + H.aide)} €/ha ; le bénéfice de rotation n’est compté qu’une fois.</p>
                    <Source k="modele">Au prix garanti, transport non déduit, sur les tonnes acceptées au tri ({pct(1 - H.qualite)} de la récolte) ; bénéfice de rotation de {fmt(H.rotation)} €/ha compris dans la barre ; rendement et prix du blé de l’année mesurés.</Source>
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

          {legacy === 3 && (
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

          {legacy === 4 && (
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
                    : <>Le prix est trop bas pour réunir {fmt(VOLUME)} t. Remontez-le dans l’annexe « Le prix, en détail ».</>}</dd>
                </dl>
                <Source k="modele">Barème calibré sur les mêmes années simulées que le prix plancher : la première tonne est recalculée, les deux suivantes reprennent la proposition du dossier pilote. Texte assemblé à partir des chiffres calculés ; volumes : hypothèses de l’équipe.</Source>
              </div>
              <div className="block">
                <h3>Où placer le site de collecte ?</h3>
                <p className="body small">Cliquez sur la carte, ou sur un établissement existant, pour déplacer le site : les parcelles retenues, leurs distances et le coût de collecte se recalculent.</p>
                <div className="figures two">
                  <Figure value={dec(target.meanKm, 1)} unit="km" label={`distance moyenne des parcelles du contrat de ${fmt(VOLUME)}\u00a0t`} />
                  <Figure value={dec(H.forfait + H.kappa * target.meanKm, 1)} unit="€/t" label="coût moyen de collecte par tonne acceptée" />
                </div>
                <div className="actions">
                  <button className="link" onClick={findBest} disabled={busy}>{busy ? 'Calcul…' : `Meilleur emplacement pour ${fmt(VOLUME)}\u00a0t`}</button>
                  <button className="link" onClick={() => { const b = SITES.liste[SITES.meilleur[volumeKey].index]; const s: [number, number] = [b.lon, b.lat]; moveSite(s); setBest(null); setBestReal({ key: volumeKey, site: s }); }}>{`Meilleur site existant pour ${fmt(VOLUME)}\u00a0t`}</button>
                  {geo !== SITE_SCENARIO && <button className="link" onClick={() => { setGeo(SITE_SCENARIO); setBest(null); setBestReal(null); }}>Revenir au site du scénario</button>}
                </div>
                {best && best.volume === VOLUME && geo.site === best.site && (
                  <p className="body small">Point de la grille qui minimise la distance moyenne pour {fmt(VOLUME)}&nbsp;t : {dec(H.kappa * (targetScenario.meanKm - target.meanKm), 1)} €/t de collecte en moins qu’au site du scénario. Le gain reste faible face à un prix garanti de plus de 1 000 €/t : le site se choisit d’abord pour la logistique.</p>
                )}
                {bestReal && bestReal.key === volumeKey && geo.site === bestReal.site && (
                  <p className="body small">Établissement existant le plus proche des parcelles de blé pour {fmt(VOLUME)}&nbsp;t : {SITES.meilleur[volumeKey].entreprise}, à {SITES.meilleur[volumeKey].commune}. La collecte y coûte {dec(Math.abs(H.kappa * (targetScenario.meanKm - target.meanKm)), 1)} €/t {targetScenario.meanKm >= target.meanKm ? 'de moins' : 'de plus'} qu’au site du scénario. Le contrat peut s’appuyer sur un établissement qui travaille déjà le grain ; sa capacité reste à vérifier.</p>
                )}
                <p className="body small">{fmt(SITES.n)} établissements de collecte ou de stockage de grains, dont {fmt(SITES.nCoop)} de coopératives, sont actifs à moins de 15&nbsp;km des parcelles franciliennes (points sur la carte).</p>
                <Source k="suppose">Forfait de {fmt(H.forfait)} €/t et {dec(H.kappa, 2)} €/t/km ; distance routière approchée par la distance à vol d’oiseau × {dec(H.detour, 1)}. Emplacements candidats : une grille de points, et les établissements de la base Sirene (Insee, extraction du {frDate(SITES.date)}) des entreprises du commerce de grains (NAF 46.21Z), codés commerce de grains ou entreposage. Sirene ne distingue pas un silo d’un bureau : capacités à vérifier.</Source>
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
                <h3>Quatre façons de garantir 8 années sur 10</h3>
                <table className="list models contracts">
                  <thead><tr><th>Contrat</th><th className="num">Coût moyen</th><th className="num">Année faible</th><th className="num">Backtest</th></tr></thead>
                  <tbody>
                    <tr><td>Prix unique<span>{fmt(C_UNIQUE.prix!)} €/t sur toutes les tonnes</span></td><td className="num">{fmt(C_UNIQUE.simulation.cout_moyen_t)}</td><td className="num">{fmt(C_UNIQUE.simulation.cout_t_annee_faible)}</td><td className="num">{pct(C_BT.unique.taux_tenus)}</td></tr>
                    <tr className="hl"><td>Barème par tranches<span>{fmt(C_PALIERS.paliers![0])} €/t la première tonne par hectare, puis {fmt(C_PALIERS.paliers![1])} et {fmt(C_PALIERS.paliers![2])}</span></td><td className="num">{fmt(C_PALIERS.simulation.cout_moyen_t)}</td><td className="num">{fmt(C_PALIERS.simulation.cout_t_annee_faible)}</td><td className="num">{pct(C_BT.paliers.taux_tenus)}</td></tr>
                    <tr><td>Indexé sur le blé<span>{dec(IDX.m, 2)} × le prix du blé de la récolte, soit {fmt(IDX_200)} €/t avec un blé à 200 €/t</span></td><td className="num">{fmt(IDX.simulation.cout_moyen_t)}</td><td className="num">{fmt(IDX.simulation.cout_t_annee_faible)}</td><td className="num">{pct(IDX_BT)}</td></tr>
                    <tr><td>Prix de base et prime à l’hectare<span>{fmt(C_PRIME.prix!)} €/t et {fmt(C_PRIME.prime_ha!)} €/ha, versés même sans récolte</span></td><td className="num">{fmt(C_PRIME.simulation.cout_moyen_t)}</td><td className="num">{fmt(C_PRIME.simulation.cout_t_annee_faible)}</td><td className={`num${C_BT.prime_ha.taux_tenus < H.tau ? ' bad' : ''}`}>{pct(C_BT.prime_ha.taux_tenus)}</td></tr>
                  </tbody>
                </table>
                <p className="body small">Le barème par tranches paie cher les premières tonnes, celles qui manquent les mauvaises années, et moins le surplus des bonnes : même protection, {saving(C_PALIERS.simulation.cout_moyen_t, C_UNIQUE.simulation.cout_moyen_t)} % de moins en moyenne. Sur 2019–2025, il tient autant de contrats que le prix unique, pour un coût réalisé inférieur de {saving(C_BT.paliers.cout_moyen_t, C_BT.unique.cout_moyen_t)} %. La prime à l’hectare coûte encore moins, mais l’acheteur la paie même quand la récolte manque, et elle a cédé quand le blé a flambé : {pct(C_2022.prime_ha)} des contrats tenus en 2022.</p>
                <Source k="modele">Seine-et-Marne, mêmes années simulées. Coût moyen : sommes versées par tonne acceptée, en €/t, hors collecte et tri. Année faible : {dec(CONTRATS.yFaible, 2)} t/ha acceptées, une année sur dix. Backtest : chaque forme recalibrée sur les seules années passées, {G.n_cas} cas.</Source>
              </div>
              <div className="block">
                <h3>Les mauvaises années, contrat par contrat</h3>
                <table className="list models contracts">
                  <thead><tr><th>Contrat</th>{BT_ANNEES.map((a) => <th key={a} className="num">{a}</th>)}<th className="num">2019–2025</th></tr></thead>
                  <tbody>
                    {BT_CONTRATS.map((c) => (
                      <tr key={c.id} className={c.id === 'paliers' ? 'hl' : ''}>
                        <td>{c.label}</td>
                        {BT_ANNEES.map((a) => {
                          const v = btC(a)[c.id];
                          return <td key={a} className={`num${v < H.tau ? ' bad' : ''}`}>{pct(v)}</td>;
                        })}
                        <td className={`num${C_BT[c.id].taux_tenus < H.tau - 0.005 ? ' bad' : ''}`}>{pct(C_BT[c.id].taux_tenus)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="body small">En 2020 et 2021, la lentille s’effondre : aucun contrat ne dépasse {pct(MAX_2020_21)}. En 2022, le blé flambe : les barèmes publiés et la proposition du dossier pilote tombent entre {pct(Math.min(...FIXES_2022))} et {pct(Math.max(...FIXES_2022))}, quand le prix unique et le barème par tranches calibrés en tiennent {pct(btC(2022).paliers)} ; la prime à l’hectare, {pct(btC(2022).prime_ha)}.</p>
                <Source k="modele">Part des contrats tenus dans le backtest strict, chaque contrat calibré sur les seules années passées ; départements producteurs.</Source>
              </div>
              <div className="block">
                <h3>Le budget de l’acheteur, contrat de {fmt(VOLUME)} t</h3>
                <table className="list models contracts">
                  <thead><tr><th>Par campagne</th><th className="num">Prix unique</th><th className="num">Tranches</th><th className="num">Indexé</th></tr></thead>
                  <tbody>
                    {(() => {
                      const recues = VOLUME / (1 - H.qualite);
                      const tri = recues * CONTRATS.couts.tri_eur_t_brute;
                      const collecte = recues * (CONTRATS.couts.collecte_fixe_eur_t_brute + CONTRATS.couts.collecte_eur_t_brute_km * target.meanKm);
                      const achat = [C_UNIQUE.simulation.cout_moyen_t, C_PALIERS.simulation.cout_moyen_t, IDX.simulation.cout_moyen_t].map((c) => c * VOLUME);
                      return (
                        <>
                          <tr><td>Achat des lentilles<span>moyenne des années simulées</span></td>{achat.map((a, i) => <td key={i} className="num">{keur(a)}</td>)}</tr>
                          <tr><td>Tri<span>{fmt(CONTRATS.couts.tri_eur_t_brute)} €/t reçue, {fmt(recues)} t reçues</span></td>{achat.map((_, i) => <td key={i} className="num">{keur(tri)}</td>)}</tr>
                          <tr><td>Collecte<span>{fmt(CONTRATS.couts.collecte_fixe_eur_t_brute)} €/t + {dec(CONTRATS.couts.collecte_eur_t_brute_km, 2)} €/t/km, {dec(target.meanKm, 1)} km en moyenne</span></td>{achat.map((_, i) => <td key={i} className="num">{keur(collecte)}</td>)}</tr>
                          <tr className="hl"><td>Total<span>par tonne acceptée</span></td>{achat.map((a, i) => <td key={i} className="num">{keur(a + tri + collecte)}<span>{fmt((a + tri + collecte) / VOLUME)} €/t</span></td>)}</tr>
                        </>
                      );
                    })()}
                  </tbody>
                </table>
                <Source k="suppose">Achat : modèle, mêmes années simulées. Tri et collecte : conventions du contrat synthétique, hypothèses sans devis (tri optique d’après Bio Hauts-de-France, 100 à 300 €/t à tester) ; séchage, stockage et conditionnement exclus.</Source>
              </div>
              <div className="block">
                <h3>Si le prix du blé change</h3>
                <table className="list models contracts">
                  <thead><tr><th>Prix du blé</th>{IDX.plancher_par_prix_ble.map((r) => <th key={r.prix_ble} className="num">{fmt(r.prix_ble)} €/t</th>)}</tr></thead>
                  <tbody>
                    <tr><td>Prix fixe nécessaire<span>pour 8 années sur 10</span></td>{IDX.plancher_par_prix_ble.map((r) => <td key={r.prix_ble} className="num">{fmt(FIXE_PAR_BLE.find((f) => f.x === r.prix_ble)?.p_star ?? 0)}</td>)}</tr>
                    <tr className="hl"><td>Plancher indexé<span>{dec(IDX.m, 2)} × le prix du blé</span></td>{IDX.plancher_par_prix_ble.map((r) => <td key={r.prix_ble} className="num">{fmt(r.plancher)}</td>)}</tr>
                    <tr><td>Achat indexé<span>{fmt(VOLUME)} t par campagne</span></td>{IDX.plancher_par_prix_ble.map((r) => <td key={r.prix_ble} className="num">{keur(r.plancher * VOLUME)}</td>)}</tr>
                  </tbody>
                </table>
                <p className="body small">Un prix fixe ne tient sa promesse que si le prix du blé reste dans la moyenne : à {fmt(FIXE_PAR_BLE[FIXE_PAR_BLE.length - 1].x)} €/t de blé, il faudrait {fmt(FIXE_PAR_BLE[FIXE_PAR_BLE.length - 1].p_star)} €/t. Le plancher indexé suit le blé et reste proche du prix nécessaire ; l’acheteur porte alors le risque de prix, de {keur(IDX.plancher_par_prix_ble[0].plancher * VOLUME)} à {keur(IDX.plancher_par_prix_ble[IDX.plancher_par_prix_ble.length - 1].plancher * VOLUME)} d’achat selon l’année.</p>
                <Source k="modele">Prix fixe nécessaire : même simulation, prix du blé imposé. Plancher indexé : coefficient calibré sur les années simulées, prix du blé de la récolte.</Source>
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
                <p className="body small">Pour la lentille, un prix fixe tient {pct(CULTURES[0].backtest.taux_tenus ?? 0)} des contrats et l’indexation l’améliore un peu. Pour les quatre autres, le plancher indexé sur le blé tient {pct(Math.min(...CULTURES.slice(1).map((c) => c.backtest.taux_tenus_indexe ?? 0)))} à {pct(Math.max(...CULTURES.slice(1).map((c) => c.backtest.taux_tenus_indexe ?? 0)))} des contrats dans ce backtest, davantage que le prix fixe. Cela motive une forme de contrat propre à chaque culture. Le pois et la féverole demandent {fmt(CULTURES.find((c) => c.id === 'pois')!.p_star['77'])} et {fmt(CULTURES.find((c) => c.id === 'feverole')!.p_star['77'])} €/t pour rivaliser avec le blé 8 années sur 10, contre 200 à 260 €/t dans le référentiel de plan d’entreprise CRIT 2025, un prix de marché courant. Le projet vise leurs débouchés humains (protéines de pois, farine de féverole), pour lesquels la revue filière retient une variante à 280 et 290 €/t.</p>
                <p className="body small">Repères de prix : pois chiche standard payé 600 à 620 €/t à un producteur Cavac pour la récolte 2025 ; haricot à 1 200 €/t au centre du scénario 900 à 1 500. Le repère haricot de 1 188 €/t vient d’un barème d’indemnisation, pas d’une offre d’achat.</p>
                <Source k="modele">Prix plancher pour 8 années sur 10 en Seine-et-Marne, en €/t ; contrats tenus en backtest 2019–2025 sur les départements producteurs, recalibrés sur les seules années passées. Même modèle du blé ; séries Agreste et météo NASA POWER propres à chaque culture. Charges calées sur les guides Terres Inovia pois chiche 2026, pois 2025 et féverole 2024 ; haricot : budget reconstruit incluant l’eau et l’énergie, hors mécanisation et récolte. Aide indicative Telepac 2026. Prix : témoignage Réussir du 27 juin 2026, CRIT Grand Est 2025 et scénario haricot documenté dans la revue filière.</Source>
              </div>
            </>
          )}

          {legacy === 5 && (
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

          {legacy === 6 && (
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
              <div className="block">
                <h3>Et pour la collecte ?</h3>
                <p className="body small">Les {fmt(SITES.maillon.n_parcelles)} parcelles de légumineuses déclarées en {MAILLON.campagne} dans la zone ({fmt(SITES.maillon.surface_ha)} ha) sont en moyenne à {dec(SITES.maillon.km_moyen_pondere_surface, 1)} km par la route d’un établissement de collecte de grains existant, la plus éloignée à {dec(SITES.maillon.km_max, 1)} km. Le repérage dit où chercher les tonnes, et quel site les collecterait.</p>
                <Source k="mesure">RPG {MAILLON.campagne} (IGN) et base Sirene (Insee, extraction du {frDate(SITES.date)}) : établissements des entreprises du commerce de grains, codés commerce de grains ou entreposage. Distance routière approchée : vol d’oiseau × {dec(H.detour, 1)}, moyenne pondérée par la surface.</Source>
              </div>
            </>
          )}

        </div>

        <footer className="column-foot">
          {annex ? (
            <>
              <button className="link" onClick={() => go(lastMain)}>← Retour au parcours</button>
              {annexIdx < ANNEXES.length - 1
                ? <button className="primary" onClick={() => go(ANNEXES[annexIdx + 1].id)}>{ANNEXES[annexIdx + 1].label} →</button>
                : <button className="primary" onClick={() => setMethod(true)}>Méthode et sources →</button>}
            </>
          ) : (
            <>
              <button className="link" onClick={() => go(MAIN[Math.max(0, mainIdx - 1)].id)} disabled={mainIdx === 0}>← Précédent</button>
              {mainIdx < MAIN.length - 1
                ? <button className="primary" onClick={() => go(MAIN[mainIdx + 1].id)}>{MAIN[mainIdx + 1].label} →</button>
                : <button className="primary" onClick={() => setMethod(true)}>Méthode et sources →</button>}
            </>
          )}
        </footer>
      </aside>

      {annexOpen && <div className="scrim clear" onClick={() => setAnnexOpen(false)} />}
      {method && <div className="scrim" onClick={() => setMethod(false)} />}
      {method && <Method onClose={() => setMethod(false)} />}
    </div>
  );
}
