import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import ParcelMap, { held, type Replay } from './components/ParcelMap';
import { BacktestReveal, SecurityChart, SupplyChart } from './components/Charts';
import { backtest, DEP_NAMES, fmt, H, meta, parcels, pct, replay, thresholds, type Parcel } from './data';

const pStars = thresholds.par_departement.map((d) => d.p_star);
const MIN = Math.floor((Math.min(...pStars) - 150) / 50) * 50;
const MAX = Math.ceil((Math.max(...pStars) + 250) / 50) * 50;
const START = MIN + 50;
const G = backtest.global;

function Badge({ k }: { k: 'mesure' | 'source' | 'suppose' | 'synthetique' | 'modele' }) {
  const txt = { mesure: 'mesuré', source: 'sourcé', suppose: 'supposé', synthetique: 'synthétique', modele: 'modèle' }[k];
  return <span className={`badge b-${k}`}>{txt}</span>;
}

export default function App() {
  const [price, setPrice] = useState(START);
  const [year, setYear] = useState<Replay | null>(null);
  const [shown, setShown] = useState(backtest.annees.length);
  const [hover, setHover] = useState<Parcel | null>(null);
  const timers = useRef<number[]>([]);

  const stop = () => { timers.current.forEach(clearTimeout); timers.current = []; };
  const at = (ms: number, fn: () => void) => timers.current.push(window.setTimeout(fn, ms));

  const stats = useMemo(() => {
    let tonnes = 0, ha = 0, n = 0, kept = 0;
    for (const p of parcels) {
      if (p.culture !== 'ble' || price < p.pRendu) continue;
      tonnes += p.tonnes; ha += p.surface; n++;
      if (year && held(p, price, year)) kept++;
    }
    return { tonnes, ha, n, kept };
  }, [price, year]);

  const demo = useCallback(() => {
    stop(); setYear(null); setPrice(START); setShown(0);
    const steps = Math.round((MAX - 200 - START) / 5);
    for (let i = 1; i <= steps; i++) at(400 + i * 55, () => setPrice(START + i * 5));
    let t = 400 + steps * 55 + 1500;
    at(t, () => setYear(replay[0])); t += 4500;
    at(t, () => setYear(replay[1])); t += 4500;
    at(t, () => setYear(null)); t += 600;
    backtest.annees.forEach((_, i) => at(t + i * 700, () => setShown(i + 1)));
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement).tagName === 'INPUT') return;
      if (e.key === 'ArrowRight') { stop(); setPrice((p) => Math.min(MAX, p + 10)); }
      if (e.key === 'ArrowLeft') { stop(); setPrice((p) => Math.max(MIN, p - 10)); }
      if (e.key === '1') { stop(); setYear(replay[0]); }
      if (e.key === '2') { stop(); setYear(replay[1]); }
      if (e.key === '0' || e.key === 'r') { stop(); setYear(null); }
      if (e.key === ' ') { e.preventDefault(); demo(); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [demo]);
  useEffect(() => stop, []);

  const d77 = thresholds.par_departement.find((d) => d.dep === '77')!;
  const fiab77 = d77.fiabilite_par_prix.reduce((a, r) => (r.prix <= price ? r : a), d77.fiabilite_par_prix[0]);
  const replayText = year && (() => {
    const share = stats.n ? stats.kept / stats.n : 0;
    const b = year.choc_ble_national, l = year.choc_lentille_national;
    const lead = year.annee === 2016 ? 'Le blé s’effondre' : 'La lentille s’effondre';
    return { lead, b, l, share };
  })();

  return (
    <div className="app">
      <main className="scene">
        <ParcelMap price={price} year={year} onHover={setHover} />
        <div className="tag">Île-de-France · parcelles de blé tendre d’hiver, RPG 2025 <Badge k="mesure" /></div>
        <div className={`year ${year ? 'on' : ''}`}>{year?.annee ?? ''}</div>
        {hover && (
          <div className="hover">
            <b>{hover.culture === 'ble' ? 'Blé tendre d’hiver' : 'Lentille déjà déclarée'}</b> · {DEP_NAMES[hover.dep]}<br />
            {hover.surface.toLocaleString('fr-FR')} ha · {fmt(hover.dist)} km du site<br />
            bascule à {fmt(hover.pRendu)} €/t rendu
          </div>
        )}
        <div className="keys">← → prix · 1 / 2 replay · 0 aujourd’hui · espace démo</div>
      </main>

      <aside>
        <header>
          <div className="eyebrow">Hack the Fork 2026 · Track 3</div>
          <h1>Le Contrat qui Tient</h1>
          <p className="pitch">À quel prix plancher un contrat lentille rapporte-t-il autant que le blé {Math.round(H.tau * 10)} années sur 10 ? Et quelles parcelles basculent à ce prix ?</p>
        </header>

        <section>
          <div className="big">{fmt(stats.tonnes)} t<small>de lentilles sécurisables · {fmt(stats.n)} parcelles · {fmt(stats.ha)} ha <Badge k="modele" /></small></div>
          <div className="slider">
            <label htmlFor="price">Prix proposé, rendu site acheteur <output>{fmt(price)} €/t</output></label>
            <input id="price" type="range" min={MIN} max={MAX} step={5} value={price}
              onChange={(e) => { stop(); setPrice(+e.target.value); }} />
            <div className="hint">À ce prix, en Seine-et-Marne, la lentille bat le blé dans <b>{pct(fiab77.fiabilite)}</b> des années simulées.</div>
          </div>
          <div className="chart"><div className="cap">Courbe d’offre · tonnes selon le prix rendu</div><SupplyChart price={price} min={MIN} max={MAX} /></div>
          <div className="row">
            <button className="btn primary" onClick={demo}>▶ Démo auto</button>
            {replay.map((r) => (
              <button key={r.annee} className={`btn ${year?.annee === r.annee ? 'on' : ''}`} onClick={() => { stop(); setYear(r); }}>Rejouer {r.annee}</button>
            ))}
            <button className={`btn ${!year ? 'on' : ''}`} onClick={() => { stop(); setYear(null); }}>Aujourd’hui</button>
          </div>
          <div className="readout">
            {replayText ? (
              <>
                <b>{year!.annee} · {replayText.lead}</b>
                <p>Au niveau national : blé {pct(replayText.b)}, lentille {pct(replayText.l)} <Badge k="mesure" /></p>
                {stats.n ? <p>Sur les parcelles sous contrat, le contrat tient sur <b>{pct(replayText.share)}</b> d’entre elles cette année-là <Badge k="modele" /></p>
                  : <p>Montez le prix : aucune parcelle n’est encore sous contrat.</p>}
              </>
            ) : (
              <>
                <b>Prix plancher calculé, campagne {meta.campagne}</b>
                <p>{thresholds.par_departement.map((d) => `${DEP_NAMES[d.dep]} ${fmt(d.p_star)} €/t`).join(' · ')} <Badge k="modele" /></p>
              </>
            )}
          </div>
        </section>

        <section>
          <h2>La preuve : des années jamais vues</h2>
          <p className="small">Pour chaque année de 2019 à 2025, le modèle n’est entraîné que sur les années précédentes. Rendement lentille relatif moyen : intervalle prédit à 80 % (bande), puis réel (point).</p>
          <div className="chart"><BacktestReveal shown={shown} /></div>
          <div className="row"><button className="btn" onClick={() => { stop(); setShown(0); backtest.annees.forEach((_, i) => at(300 + i * 700, () => setShown(i + 1))); }}>Révéler année par année</button></div>
          <div className="kpis">
            <div className="kpi"><span>{pct(G.taux_tenus)}</span><em>contrats tenus, pour {pct(backtest.fiabilite_visee)} visés ({G.n_cas} cas)</em></div>
            <div className="kpi"><span>{pct(G.couverture_M1)}</span><em>couverture de l’intervalle à 80 %</em></div>
            <div className="kpi"><span>{G.gain_pinball_M1_vs_M0 > 0 ? '+' : ''}{(G.gain_pinball_M1_vs_M0 * 100).toFixed(1)} %</span><em>précision vs baseline naïve</em></div>
          </div>
          <table className="years">
            <thead><tr><th>Année</th>{backtest.annees.map((y) => <th key={y.annee}>{y.annee}</th>)}</tr></thead>
            <tbody><tr><td>Tenus</td>{backtest.annees.map((y, i) => <td key={y.annee} className={i < shown ? (y.taux_tenus! >= 0.8 ? 'good' : 'bad') : 'hide'}>{i < shown ? pct(y.taux_tenus!) : '·'}</td>)}</tr></tbody>
          </table>
          <p className="small honest">À dire au jury : la fiabilité globale est atteinte, mais les contrats cèdent en 2020 et 2021, deux années d’effondrement que le modèle n’avait jamais vues. La régression quantile météo ne bat pas la baseline en précision ; elle est mieux calibrée ({pct(G.couverture_M1)} contre {pct(G.couverture_M0)}). Le challenger LightGBM gagne {(G.gain_pinball_M2_vs_M0 * 100).toFixed(1)} %.</p>
        </section>

        <section>
          <h2>Le prix de la sécurité</h2>
          <p className="small">Prix plancher en Seine-et-Marne selon la fiabilité visée.</p>
          <div className="chart"><SecurityChart /></div>
        </section>

        <section>
          <h2>Proposition de contrat</h2>
          <div className="contract">
            <p><b>Objet.</b> Achat de lentilles pour l’alimentation humaine, sur 3 campagnes à partir de {meta.campagne}.</p>
            <p><b>Prix plancher.</b> {fmt(d77.p_star)} €/t départ ferme en Seine-et-Marne, ajusté du transport jusqu’au site.</p>
            <p><b>Ce que garantit le prix.</b> Dans {pct(H.tau)} des années simulées, la marge lentille égale ou dépasse celle du blé.</p>
            <p><b>Ce qu’il ne garantit pas.</b> Une mauvaise récolte réduit la marge malgré le prix : un rendement de {d77.rendement_lentille_q10_tha.toLocaleString('fr-FR')} t/ha survient une année sur dix.</p>
            <p><b>Volume visé.</b> {fmt(stats.tonnes)} t sur {fmt(stats.ha)} ha au prix affiché.</p>
          </div>
          <p className="small">Texte généré par gabarit à partir des chiffres calculés. Version rédigée par LLM (Bedrock) prévue, sans aucun chiffre ajouté.</p>
        </section>

        <section>
          <h2>Hypothèses</h2>
          <ul className="hyp">
            {Object.entries(meta.hypotheses).map(([k, v]: [string, any]) => (
              <li key={k}><span>{k.replace(/_/g, ' ')}</span><b>{Array.isArray(v.valeur) ? v.valeur.join(', ') : v.valeur}</b><Badge k={v.etiquette} /><em>{v.source}</em></li>
            ))}
          </ul>
          <p className="small">Le niveau de rendement lentille francilien ({meta.niveau_lentille_idf_qha.toLocaleString('fr-FR')} q/ha) est celui des départements producteurs voisins ({meta.voisins_lentille.join(', ')}) : l’Île-de-France cultive trop peu de lentilles pour l’estimer seule.</p>
        </section>

        <footer className="small">
          Sources : Agreste SAA 2010–2025, RPG 2025 (IGN), NASA POWER. Code et méthode : github.com/nassim-arifette/hackthefork-hackathon
        </footer>
      </aside>
    </div>
  );
}
