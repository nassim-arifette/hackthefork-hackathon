import { useState } from 'react';
import { backtest, dec, HYPOTHESES, MAIN_MODEL, meta, pct, thresholds } from '../data';
import { statusText } from './ui';

const NAMES: Record<string, string> = {
  charges_ble_eur_ha: 'Charges opérationnelles du blé', charges_lentille_eur_ha: 'Charges opérationnelles de la lentille',
  aide_couplee_eur_ha: 'Aide retenue dans le scénario principal', aide_couplee_scenario_eur_ha: 'Aide conditionnelle, hors scénario principal', aide_couplee_conditionnelle_eur_ha: 'Aide conditionnelle, hors scénario principal',
  bonus_rotation_eur_ha: 'Bonus de rotation', cout_transport_eur_t_km: 'Coût du transport', facteur_detour_route: 'Détour routier',
  fiabilite_visee: 'Protection visée', volume_vise_t: 'Volume attendu visé', site_acheteur: 'Site acheteur fictif',
  prix_revente_eur_t: 'Revente hypothétique', pertes_tri_fraction: 'Part perdue au tri', cout_tri_eur_t: 'Coût du tri',
  cout_transformation_eur_t: 'Transformation', cout_acheteur_autres_eur_t: 'Autres coûts acheteur', marge_min_acheteur_eur_t: 'Marge minimale acheteur',
};
const UNITS: Record<string, string> = {
  charges_ble_eur_ha: '€/ha', charges_lentille_eur_ha: '€/ha', aide_couplee_eur_ha: '€/ha', aide_couplee_scenario_eur_ha: '€/ha', aide_couplee_conditionnelle_eur_ha: '€/ha',
  bonus_rotation_eur_ha: '€/ha', cout_transport_eur_t_km: '€/t/km', volume_vise_t: 't',
  prix_revente_eur_t: '€/t commercialisable', cout_tri_eur_t: '€/t livrée', cout_transformation_eur_t: '€/t livrée',
  cout_acheteur_autres_eur_t: '€/t livrée', marge_min_acheteur_eur_t: '€/t livrée',
};
const FEATURES: Record<string, string> = {
  tendance: 'Tendance, par décennie', pluie_mj_anom: 'Pluie de mars à juillet', pluie_avj_anom: 'Pluie d’avril à juin',
  j30_jj_anom: 'Jours au-dessus de 30 °C en juin-juillet', gel_tardif_anom: 'Gelées tardives',
  pluie_recolte_anom: 'Pluie à la récolte', tmax_mj_anom: 'Température maximale',
};
const VOISINS: Record<string, string> = { '10': 'Aube', '51': 'Marne', '89': 'Yonne', '28': 'Eure-et-Loir', '45': 'Loiret' };
const MODELS: Record<string, string> = { M0: 'Tendance sans météo', M1: 'Régression quantile météo', M2: 'LightGBM quantile', M3: 'Ensemble de quantiles', auto: 'Sélection temporelle automatique' };

function value(k: string, v: unknown): string {
  if (k === 'fiabilite_visee' || k === 'pertes_tri_fraction') return pct(Number(v));
  if (k === 'site_acheteur') return 'Fictif, en Seine-et-Marne';
  if (typeof v !== 'number') return String(v);
  return `${v.toLocaleString('fr-FR')}${UNITS[k] ? ` ${UNITS[k]}` : ''}`;
}

export default function Method({ onClose }: { onClose: () => void }) {
  const [target, setTarget] = useState(0.8);
  const frontier = (backtest as any).frontiere_prix_protection as { methode: string; tau: number; taux_tenus: number; prix_median_eur_t: number; manque_moyen_eur_ha: number; manque_moyen_si_echec_eur_ha: number; cout_achat_moyen_eur_ha: number; taux_tenus_ic95_bootstrap_annees: number[] }[] | undefined;
  const targetOptions = [...new Set(frontier?.map((row) => row.tau) ?? [])].sort((a, b) => a - b);
  const G = backtest.global as Record<string, number>;
  const strategies = (meta as any).strategies_77 as Record<string, number>;
  const panel = (meta as any).panel_lentille;
  const retained = panel.series_retenues ?? panel.series_independantes;
  const coefs = meta.coefficients_M1_lentille as Record<string, Record<string, number>>;
  const distribution = (thresholds.sensibilite as any).distribution as { queue: string; dependance: string; p_star: number }[] | undefined;
  const tailNames: Record<string, string> = { linear: 'Queues linéaires', bounded: 'Queues bornées', stress: 'Queue basse stressée' };
  const dependenceNames: Record<string, string> = { independent: 'résidus indépendants', positive: 'dépendance positive', negative: 'dépendance négative' };
  const interval = (thresholds.par_departement.find((d) => d.dep === '77') as any)?.p_star_ic80 as number[] | undefined;
  return (
    <div className="sheet" role="dialog" aria-modal="true" aria-labelledby="method-title">
      <div className="sheet-head"><h2 id="method-title">Méthode et sources</h2><button className="link" onClick={onClose}>Fermer</button></div>
      <div className="sheet-body">
        <section>
          <h3>Un protocole temporel, puis une décision économique</h3>
          <ol>
            <li><b>Apprentissage.</b> Les niveaux départementaux, le regroupement heuristique des séries et les transformations météo sont estimés dans le découpage d’apprentissage. Le rendement normalisé est le rendement divisé par le niveau départemental estimé.</li>
            <li><b>Sélection.</b> Les candidats sont comparés sur des années de validation antérieures aux années réservées à la calibration. La sélection ne consulte ni la calibration ni l’année test. Modèle de prix sélectionné pour {meta.campagne} : {MAIN_MODEL}.</li>
            <li><b>Calibration.</b> Le prédicteur est figé avant de mesurer ses erreurs sur les années de calibration. Il n’est pas réentraîné ensuite. Les bornes calibrées servent à évaluer la couverture d’un intervalle ; elles ne définissent pas les quantiles de la distribution simulée.</li>
            <li><b>Simulation et prix.</b> La météo passée et le prix du blé de la même année sont rejoués. Le prix plancher est le quantile des prix d’équilibre pour la protection visée. Les hypothèses sur les queues et la dépendance des rendements influencent cette décision.</li>
          </ol>
          <p className="formula">P* = quantile visé de (prix du blé × rendement du blé − charges du blé + charges de la lentille − aide − bonus de rotation) ÷ rendement de la lentille</p>
          <p>Le découpage temporel réduit les fuites de données. Il ne rend pas les départements ni les années indépendants et ne suffit pas à garantir une couverture future de 80 %.</p>
        </section>
        <section>
          <h3>Comparaison des prédicteurs</h3>
          <div className="table-scroll"><table className="tbl">
            <thead><tr><th>Modèle</th><th className="num">Perte quantile</th><th className="num">Couverture</th><th className="num">P* {meta.campagne}, 77</th></tr></thead>
            <tbody>{Object.entries(MODELS).filter(([key]) => G[`pinball_${key}`] !== undefined).map(([key, label]) => <tr key={key} className={key === 'auto' ? 'hl' : ''}>
              <td>{key} · {label}</td><td className="num">{dec(G[`pinball_${key}`], 4)}</td><td className="num">{pct(G[`couverture_${key}`])}</td><td className="num">{strategies?.[key] !== undefined ? `${Math.round(strategies[key]).toLocaleString('fr-FR')} €/t` : '—'}</td>
            </tr>)}</tbody>
          </table></div>
          <p className="note">{backtest.protocole} La perte quantile mesure les quantiles bruts ; la couverture mesure les intervalles après calibration. Le modèle de rendement est évalué avec la météo de l’année test observée rétrospectivement. Le prix économique est décidé avec les années passées uniquement.</p>
          <p>Le succès économique doit être comparé au prix payé, au manque de marge résiduel et au coût d’achat. La sélection minimise une perte prédictive en validation interne ; elle ne prouve pas une supériorité économique. Un taux plus élevé peut résulter d’un prix plus coûteux. Les résultats dépendent du périmètre de données et ne sont pas directement comparables aux versions antérieures.</p>
        </section>
        {frontier && <section>
          <h3>Comparer prix et protection observée</h3>
          <label className="department-select">Protection visée pour cette comparaison<select value={target} onChange={(e) => setTarget(Number(e.target.value))}>{targetOptions.map((tau) => <option key={tau} value={tau}>{pct(tau)} visés dans les simulations</option>)}</select></label>
          <div className="table-scroll"><table className="tbl"><thead><tr><th>Méthode lentille</th><th className="num">Succès observé</th><th className="num">Prix médian €/t</th><th className="num">Manque moyen €/ha</th><th className="num">Manque si échec €/ha</th><th className="num">Achat moyen €/ha</th></tr></thead><tbody>{frontier.filter((row) => Math.abs(row.tau - target) < 1e-8).map((row) => <tr key={row.methode} className={row.methode === 'auto' ? 'hl' : ''}>
            <td>{row.methode === 'historique' ? 'Historique apparié sans météo' : `${row.methode} · ${MODELS[row.methode] ?? row.methode}`}</td>
            <td className="num">{dec(row.taux_tenus * 100, 1)} %<br /><small>{row.taux_tenus_ic95_bootstrap_annees.map((v) => dec(v * 100, 1)).join('–')} %</small></td>
            <td className="num">{Math.round(row.prix_median_eur_t).toLocaleString('fr-FR')}</td><td className="num">{Math.round(row.manque_moyen_eur_ha).toLocaleString('fr-FR')}</td><td className="num">{Math.round(row.manque_moyen_si_echec_eur_ha).toLocaleString('fr-FR')}</td><td className="num">{Math.round(row.cout_achat_moyen_eur_ha).toLocaleString('fr-FR')}</td>
          </tr>)}</tbody></table></div>
          <p>Une cible identique ne donne pas une protection observée identique. Comparez aussi les prix lorsque les succès observés sont proches. Cette grille descriptive ne sert pas à choisir le modèle ou le contrat après consultation des années test.</p>
          <p className="note">Sous le succès : intervalle descriptif à 95 % par rééchantillonnage des années test, avec seulement {G.n_annees} années. Prix départ ferme, charges fixes et aide principale nulle. M0–M3 et auto désignent le modèle lentille ; le modèle du blé est commun, sélectionné automatiquement. La référence historique utilise les récoltes et prix passés appariés.</p>
        </section>}
        <section>
          <h3>Coefficients du candidat M1</h3>
          <table className="tbl"><thead><tr><th>Variable</th><th className="num">Coefficient médian</th></tr></thead><tbody>
            {Object.entries(coefs.q50).filter(([k]) => k !== 'constante').map(([k, v]) => <tr key={k}><td>{FEATURES[k] ?? k}</td><td className="num">{v > 0 ? '+' : ''}{dec(v, 3)}</td></tr>)}
          </tbody></table>
          <p className="note">Unités de rendement normalisé par unité de variable transformée. Le modèle décrit des associations ; ces coefficients ne prouvent pas des effets causaux.</p>
        </section>
        <section>
          <h3>Hypothèses du scénario de référence</h3>
          <p>L’aide dont l’éligibilité n’est pas confirmée vaut zéro dans le scénario principal. Les 122 €/ha ne sont utilisés que dans une sensibilité conditionnelle. Les hypothèses acheteur ci-dessous sont les valeurs initiales ; les champs de l’étape 5 permettent de les modifier pour la négociation affichée.</p>
          <table className="tbl hyp"><tbody>{Object.entries(HYPOTHESES).map(([k, v]) => <tr key={k}>
            <td><b>{NAMES[k] ?? k}</b><span>{v.url ? <a href={v.url} target="_blank" rel="noreferrer">{v.source}</a> : v.source}</span></td>
            <td className="num">{value(k, v.valeur)}<span>{statusText(v.etiquette)}</span></td>
          </tr>)}</tbody></table>
        </section>
        <section>
          <h3>Données et statut des références</h3>
          <ul>
            <li><b>Agreste, Statistique agricole annuelle 2010–2025.</b> Surfaces et rendements départementaux ; 2025 provisoire.</li>
            <li><b>IGN, Registre parcellaire graphique 2025.</b> {meta.n_parcelles.toLocaleString('fr-FR')} parcelles de blé tendre d’hiver et de lentille en Île-de-France. La sélection de parcelles ne prédit pas leur rendement individuel.</li>
            <li><b>NASA POWER.</b> Météo journalière au centroïde départemental, résumée en six variables agronomiques.</li>
            <li><b>Blé.</b> Prix de référence reconstruit à partir d’Eurostat et d’Agreste : indice Eurostat ancré à 178,8 €/t en 2019 sur une référence rendu Rouen de campagne 2019–2020. Ce n’est pas le prix effectivement payé à chaque exploitation.</li>
            <li><b>Lentille.</b> Référence historique nominale 2012–2016, non représentative d’une cotation actuelle. Le prix proposé par l’acheteur est explicitement hypothétique.</li>
          </ul>
        </section>
        {distribution && <section>
          <h3>Sensibilité de la distribution simulée</h3>
          <table className="tbl"><thead><tr><th>Hypothèse de simulation</th><th className="num">P* 77, départ ferme</th></tr></thead><tbody>{distribution.map((d) => <tr key={`${d.queue}-${d.dependance}`}><td>{tailNames[d.queue] ?? d.queue}, {dependenceNames[d.dependance] ?? d.dependance}</td><td className="num">{Math.round(d.p_star).toLocaleString('fr-FR')} €/t</td></tr>)}</tbody></table>
          <p>Le scénario principal tire les résidus de lentille et de blé indépendamment, conditionnellement à l’année météo commune. Les autres dépendances sont des tests de sensibilité, pas des estimations. La calibration d’un intervalle ne valide ni ces queues ni ces dépendances.</p>
        </section>}
        <section>
          <h3>Références méthodologiques</h3>
          <ul>
            <li><a href="https://arxiv.org/abs/1905.03222" target="_blank" rel="noreferrer">Romano, Patterson et Candès (2019), Conformalized Quantile Regression.</a> Séparation du prédicteur et des données de calibration.</li>
            <li><a href="https://proceedings.mlr.press/v139/xu21h.html" target="_blank" rel="noreferrer">Xu et Xie (2021), Conformal Prediction Interval for Dynamic Time-Series.</a> Les dépendances temporelles demandent des hypothèses et une évaluation adaptées. EnbPI n’est pas revendiqué comme implémenté ici.</li>
          </ul>
        </section>
        <section>
          <h3>Limites à garder visibles</h3>
          <ul>
            <li>{panel.departements_mesures} départements mesurés, {retained} séries retenues après regroupement heuristique. Ce regroupement ne démontre pas leur indépendance statistique.</li>
            <li>Rendements départementaux : l’incertitude d’une exploitation ou d’une parcelle peut être plus forte.</li>
            <li>Niveau lentille en Île-de-France transféré des voisins ({meta.voisins_lentille.map((d: string) => VOISINS[d] ?? d).join(', ')}), soit {dec(meta.niveau_lentille_idf_qha)} q/ha.</li>
            {interval && <li>Sensibilité aux années rejouées, modèles figés (10–90 %), Seine-et-Marne : {interval.map((v) => Math.round(v).toLocaleString('fr-FR')).join('–')} €/t. Elle exclut l’erreur de réestimation du modèle et ne constitue pas un intervalle de confiance complet.</li>}
            <li>{G.n_annees} années test seulement. Les observations départementales d’une même année sont liées ; le nombre de cas ne vaut pas le nombre de réplications indépendantes.</li>
            <li>Reconstitution sous charges et hypothèses affichées, pas observation des marges historiques réelles des exploitations.</li>
            <li>Une distribution simulée et ses queues restent des hypothèses distinctes de la couverture d’un intervalle. Une mauvaise récolte peut faire monter fortement le prix requis.</li>
            <li>Une seule campagne cible est simulée. Ni le prix proposé ni un objectif de volume ne garantissent la récolte, la marge ou l’existence d’un débouché rentable.</li>
          </ul>
        </section>
      </div>
    </div>
  );
}
