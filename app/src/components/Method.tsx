import { backtest, HYPOTHESES, meta, pct, thresholds } from '../data';
import { statusText } from './ui';

const NAMES: Record<string, string> = {
  charges_ble_eur_ha: 'Charges opérationnelles du blé',
  charges_lentille_eur_ha: 'Charges opérationnelles de la lentille',
  aide_couplee_eur_ha: 'Aide couplée aux légumineuses',
  bonus_rotation_eur_ha: 'Bénéfice de rotation pour le blé suivant',
  part_non_valorisee: 'Part de la récolte refusée au tri',
  cout_transport_eur_t_km: 'Coût du transport',
  forfait_collecte_eur_t: 'Forfait de collecte',
  facteur_detour_route: 'Détour routier',
  fiabilite_visee: 'Fiabilité visée',
  volume_pilote_t: 'Volume du pilote',
  volume_vise_t: 'Volume de l’ambition de bassin',
  proteines_part: 'Protéines dans le grain',
  azote_ble_kg_ha: 'Azote minéral apporté au blé',
  co2e_t_par_ha: 'Émissions directes de l’azote évité',
  site_acheteur: 'Site de collecte',
};
const HIDDEN = new Set(['scenario_historique']);
const PERCENT = new Set(['part_non_valorisee', 'proteines_part']);
const UNITS: Record<string, string> = {
  charges_ble_eur_ha: '€/ha', charges_lentille_eur_ha: '€/ha', aide_couplee_eur_ha: '€/ha',
  bonus_rotation_eur_ha: '€/ha', cout_transport_eur_t_km: '€/t/km', volume_vise_t: 't', volume_pilote_t: 't',
  forfait_collecte_eur_t: '€/t', azote_ble_kg_ha: 'kg N/ha', co2e_t_par_ha: 't CO₂e/ha',
};

const FEATURES: Record<string, string> = {
  tendance: 'Tendance, par décennie',
  pluie_mj_anom: 'Pluie de mars à juillet',
  pluie_avj_anom: 'Pluie d’avril à juin',
  j30_jj_anom: 'Jours au-dessus de 30 °C en juin et juillet',
  gel_tardif_anom: 'Gelées tardives, d’avril à mi-mai',
  pluie_recolte_anom: 'Pluie à la récolte, de mi-juillet à mi-août',
  tmax_mj_anom: 'Température maximale de mai à juillet',
};

const VOISINS: Record<string, string> = { '10': 'Aube', '51': 'Marne', '89': 'Yonne', '28': 'Eure-et-Loir', '45': 'Loiret' };

function value(k: string, v: any): string {
  if (k === 'fiabilite_visee') return '8 années sur 10';
  if (k === 'site_acheteur') return 'fictif, en Seine-et-Marne';
  if (PERCENT.has(k)) return `${Math.round(Number(v) * 100)} %`;
  const n = Number(v).toLocaleString('fr-FR');
  return UNITS[k] ? `${n} ${UNITS[k]}` : n;
}

export default function Method({ onClose }: { onClose: () => void }) {
  const G = backtest.global as Record<string, number>;
  const STRAT = (meta as any).strategies_77 as { moyenne: number; M0: number; M1: number; M2: number };
  const coefs = meta.coefficients_M1_lentille as Record<string, Record<string, number>>;
  return (
    <div className="sheet" role="dialog" aria-modal="true" aria-labelledby="method-title">
      <div className="sheet-head">
        <h2 id="method-title">Méthode et sources</h2>
        <button className="link" onClick={onClose}>Fermer</button>
      </div>
      <div className="sheet-body">
        <section>
          <h3>Le calcul, en quatre étapes</h3>
          <ol>
            <li><b>Rendement relatif.</b> Pour chaque département, le rendement de l’année divisé par son rendement moyen. Les {(meta as any).panel_lentille.series_independantes} séries indépendantes de rendement de lentille deviennent comparables, et le modèle peut s’appliquer à l’Île-de-France, qui en cultive trop peu pour être estimée seule.</li>
            <li><b>Régression quantile.</b> Les quantiles 10, 50 et 90 % du rendement relatif sont estimés à partir d’une tendance et de six écarts météo (NASA POWER). L’intervalle est ensuite calibré par conformal sur les trois dernières années d’entraînement, pour couvrir réellement 80 % des cas.</li>
            <li><b>Monte-Carlo.</b> 20 000 années sont rejouées. Chacune reprend une année réelle de 2010 à 2025, avec sa météo et son prix du blé, puis tire un rendement de lentille et un rendement de blé dans leurs distributions.</li>
            <li><b>Prix plancher.</b> Dans chaque année simulée, on calcule le prix d’équilibre où la lentille rapporte autant que le blé. Le prix plancher est le quantile 80 % de ces prix.</li>
          </ol>
          <p className="formula">P* = quantile 80 % de (prix du blé × rendement du blé − charges du blé + charges de la lentille − aide − bénéfice de rotation) ÷ tonnes de lentille acceptées au tri</p>
          <p className="note">Le prix garanti est payé sur les tonnes acceptées au tri pour l’alimentation humaine, comme dans les contrats de collecte. Agreste mesure le rendement à l’arrivée à la ferme, avant ce tri : on retire donc une part refusée de {Math.round(((HYPOTHESES as any).part_non_valorisee.valeur) * 100)} %. Avec les hypothèses du 30/10, le prix plancher de la Seine-et-Marne serait de {(thresholds as any).sensibilite.scenario_historique.toLocaleString('fr-FR')} €/t.</p>
        </section>

        <section>
          <h3>La météo</h3>
          <p>La météo journalière NASA POWER de 2010 à 2025 est lue pour 43 départements, au centroïde de chacun. Elle est résumée en six variables agronomiques, exprimées en écart à la climatologie 2010–2018 : pluie de mars à juillet, pluie d’avril à juin, jours au-dessus de 30 °C en juin et juillet (stress à la floraison), gelées tardives d’avril à mi-mai, pluie à la récolte de mi-juillet à mi-août, et température maximale de mai à juillet. Ces variables sont les entrées des deux modèles d’apprentissage ; dans la simulation, chaque année tirée rejoue la météo d’une année réelle.</p>
        </section>

        <section>
          <h3>Effets estimés sur le rendement de la lentille</h3>
          <table className="tbl">
            <thead><tr><th>Variable</th><th className="num">Effet médian</th></tr></thead>
            <tbody>
              {Object.entries(coefs.q50).filter(([k]) => k !== 'constante').map(([k, v]) => (
                <tr key={k}><td>{FEATURES[k] ?? k}</td><td className="num">{v > 0 ? '+' : v < 0 ? '−' : ''}{Math.abs(v * 100).toLocaleString('fr-FR', { maximumFractionDigits: 1 })} %</td></tr>
              ))}
            </tbody>
          </table>
          <p className="note">Effet d’un écart-type de plus sur le rendement relatif, au quantile 50 %. Écarts mesurés par rapport à la climatologie 2010–2018.</p>
        </section>

        <section>
          <h3>Comparaison des modèles sur le backtest</h3>
          <table className="tbl">
            <thead><tr><th>Modèle</th><th className="num">Perte pinball</th><th className="num">Couverture à 80 %</th><th className="num">P* 2026, 77</th></tr></thead>
            <tbody>
              <tr><td>Moyennes des années passées (sans modèle)</td><td className="num">—</td><td className="num">—</td><td className="num">{STRAT.moyenne.toLocaleString('fr-FR')} €/t</td></tr>
              <tr><td>Tendance seule (référence)</td><td className="num">{G.pinball_M0.toLocaleString('fr-FR')}</td><td className="num">{pct(G.couverture_M0)}</td><td className="num">{STRAT.M0.toLocaleString('fr-FR')} €/t</td></tr>
              <tr className="hl"><td>Régression quantile météo, retenue</td><td className="num">{G.pinball_M1.toLocaleString('fr-FR')}</td><td className="num">{pct(G.couverture_M1)}</td><td className="num">{STRAT.M1.toLocaleString('fr-FR')} €/t</td></tr>
              <tr><td>LightGBM quantile (gradient boosting)</td><td className="num">{G.pinball_M2.toLocaleString('fr-FR')}</td><td className="num">{pct(G.couverture_M2)}</td><td className="num">{STRAT.M2.toLocaleString('fr-FR')} €/t</td></tr>
              <tr><td>Choix automatique sur validation interne</td><td className="num">{G.pinball_auto.toLocaleString('fr-FR')}</td><td className="num">{pct(G.couverture_auto)}</td><td className="num">—</td></tr>
            </tbody>
          </table>
          <p className="note">{backtest.protocole} Le modèle retenu a été choisi avant tout résultat. Contrats tenus : {pct(G.taux_tenus_moyenne)} avec un prix fixé sur les moyennes, {pct(G.taux_tenus_M0)} avec la tendance seule, {pct(G.taux_tenus)} avec la régression quantile météo, {pct(G.taux_tenus_M2)} avec LightGBM, {pct(G.taux_tenus_auto)} avec le choix automatique. Les modèles les plus précis sous-estiment les mauvaises années. Le prix 2026 varie fortement d’un modèle à l’autre (de {STRAT.M2.toLocaleString('fr-FR')} à {STRAT.M0.toLocaleString('fr-FR')} €/t) : c’est une incertitude de modèle, qui s’ajoute à l’incertitude statistique. Nous avons aussi testé une régularisation choisie en validation interne : plus précise, mais moins bien calibrée ; elle n’est pas retenue.</p>
        </section>

        <section>
          <h3>Hypothèses</h3>
          <table className="tbl hyp">
            <tbody>
              {Object.entries(HYPOTHESES).filter(([k]) => !HIDDEN.has(k)).map(([k, v]) => (
                <tr key={k}>
                  <td><b>{NAMES[k] ?? k}</b><span>{v.url ? <a href={v.url} target="_blank" rel="noreferrer">{v.source}</a> : v.source}</span></td>
                  <td className="num">{value(k, v.valeur)}<span>{statusText(v.etiquette)}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section>
          <h3>Données</h3>
          <ul>
            <li><b>Agreste, Statistique agricole annuelle 2010–2025.</b> Surfaces et rendements par département. Mesuré.</li>
            <li><b>IGN, Registre parcellaire graphique 2025.</b> {meta.n_parcelles.toLocaleString('fr-FR')} parcelles de blé tendre d’hiver et de lentille en Île-de-France. Mesuré.</li>
            <li><b>NASA POWER.</b> Météo journalière 2010–2025 pour 43 départements. Mesuré.</li>
            <li><b>Eurostat.</b> Indice des prix du blé tendre, calé sur le prix rendu Rouen d’Agreste en 2019-2020 ; prix observés de la lentille 2012–2016 ; commerce extérieur Comext. Mesuré.</li>
          </ul>
        </section>

        <section>
          <h3>Limites</h3>
          <ul>
            <li>Rendements départementaux : à la parcelle, le risque réel est plus fort.</li>
            <li>Niveau de rendement de la lentille en Île-de-France emprunté aux départements producteurs voisins ({meta.voisins_lentille.map((d: string) => VOISINS[d] ?? d).join(', ')}), soit {meta.niveau_lentille_idf_qha.toLocaleString('fr-FR')} q/ha.</li>
            <li>Le prix plancher lui-même est incertain : en rééchantillonnant les années, celui de la Seine-et-Marne varie de {((thresholds as any).par_departement.find((d: any) => d.dep === '77').p_star_ic80 ?? []).map((v: number) => v.toLocaleString('fr-FR')).join(' à ')} €/t (intervalle à 80 %). Seize années ne suffisent pas à cerner les mauvaises années ; des données de coopérative le resserreraient.</li>
            <li>Agreste estime souvent le rendement de la lentille au niveau régional : {(meta as any).panel_lentille.departements_mesures} départements mesurés, mais {(meta as any).panel_lentille.series_independantes} séries indépendantes seulement.</li>
            <li>Sept années test seulement ; 2020 et 2021, absentes de l’entraînement, font céder les contrats.</li>
            <li>La météo n’améliore pas la précision face à la tendance seule ; elle améliore la calibration.</li>
            <li>Charges constantes dans le temps ; aide couplée de 2026 encore indicative, ajustée en fin de campagne selon les surfaces.</li>
            <li>Part refusée au tri et bénéfice de rotation : hypothèses de l’équipe, testées en sensibilité.</li>
            <li>Un prix plancher n’est pas une assurance : une récolte effondrée réduit la marge.</li>
          </ul>
        </section>
      </div>
    </div>
  );
}
