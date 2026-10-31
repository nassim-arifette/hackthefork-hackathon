# Comparaison par groupes : QRF calibré et M0 calibré

M0 et QRF utilisent ici chacun une correction du prix choisie uniquement sur les années antérieures. La comparaison porte sur les politiques trend__past_selected et qrf__past_selected du run contract_policies_sensitivity. Les groupes reprennent exactement les définitions de l’analyse brute ; aucun groupe n’a été choisi sur son résultat calibré.

Chaque ligne compare exactement les mêmes départements et années. La perte, les taux tenus, les prix moyens et les manques moyens donnent le même poids à chaque année. Les prix médians sont calculés sur les cas. Les intervalles rééchantillonnent les années entières, avec les écarts appariés au même M0.

L'objectif de 80 % est affiché séparément de la perte économique. Un modèle peut réduire la perte tout en protégeant moins de contrats. Les groupes sont fixés par le script avant inspection des scores ; tous sont publiés, y compris ceux qui régressent. Les résultats par groupes sont exploratoires, pas une règle de sélection validée pour une future campagne.

## Groupes connus avant campagne

| Groupe | Cas / années | Perte M0 calibré → QRF calibré | Gain perte | Tenus M0 calibré → QRF calibré | Δ perte, IC95 % |
|---|---:|---:|---:|---:|---:|
| all: all cases | 192 / 7 | 288.0 → 233.0 | 19.1% | 82.5% → 83.5% | [-108.7 ; -5.1] |
| region: 24 - Centre-Val de Loire | 42 / 7 | 273.6 → 251.1 | 8.2% | 76.2% → 76.2% | [-91.0 ; 44.5] |
| region: 27 - Bourgogne-Franche-Comté | 8 / 7 | 607.2 → 509.3 | 16.1% | 57.1% → 64.3% | [-241.5 ; 42.8] |
| region: 44 - Grand Est | 18 / 7 | 237.5 → 181.5 | 23.6% | 85.7% → 71.4% | [-119.1 ; 3.4] |
| region: 52 - Pays de la Loire | 24 / 7 | 334.3 → 265.8 | 20.5% | 85.7% → 85.7% | [-122.4 ; -18.8] |
| region: 75 - Nouvelle Aquitaine | 26 / 7 | 242.7 → 188.5 | 22.3% | 89.3% → 92.9% | [-103.0 ; -11.8] |
| region: 76 - Occitanie | 50 / 7 | 234.3 → 189.2 | 19.3% | 88.5% → 89.5% | [-90.7 ; -8.5] |
| region: 84 - Auvergne-Rhône-Alpes | 24 / 7 | 381.6 → 292.2 | 23.4% | 78.6% → 89.3% | [-177.7 ; 0.8] |
| history: <8 years | 36 / 7 | 337.8 → 264.5 | 21.7% | 88.6% → 87.3% | [-139.9 ; -11.9] |
| history: >=8 years | 156 / 7 | 277.4 → 227.3 | 18.1% | 80.5% → 82.2% | [-101.3 ; -1.1] |
| volatility: high | 60 / 7 | 320.2 → 261.5 | 18.3% | 79.6% → 81.4% | [-122.9 ; 5.0] |
| volatility: low | 68 / 7 | 259.4 → 200.5 | 22.7% | 84.3% → 81.3% | [-101.7 ; -24.4] |
| volatility: medium | 64 / 7 | 286.3 → 237.5 | 17.1% | 83.2% → 87.9% | [-109.3 ; 6.4] |
| yield_level: high | 97 / 7 | 278.5 → 229.0 | 17.8% | 79.6% → 77.8% | [-102.2 ; -1.3] |
| yield_level: low | 95 / 7 | 297.7 → 237.2 | 20.3% | 85.4% → 89.1% | [-116.8 ; -9.2] |
| idf_donor: IDF donor departments | 28 / 7 | 376.0 → 327.2 | 13.0% | 71.4% → 67.9% | [-123.6 ; 32.7] |
| idf_donor: other departments | 164 / 7 | 274.4 → 218.7 | 20.3% | 84.3% → 85.9% | [-107.4 ; -9.2] |

## Diagnostics rétrospectifs

Les étiquettes suivantes utilisent la récolte ou la météo réalisée, le prix réalisé, ou l'ancienne sélection globale des départements. Elles expliquent les échecs ; elles ne sont pas disponibles pour choisir un modèle au moment de signer le contrat.

| Groupe | Cas / années | Perte M0 calibré → QRF calibré | Tenus M0 calibré → QRF calibré | Manque €/ha M0 calibré → QRF calibré |
|---|---:|---:|---:|---:|
| original_cohort: added 59 | 59 / 7 | 293.0 → 218.9 | 88.9% → 89.0% | 30.3 → 21.6 |
| original_cohort: original 133 | 133 / 7 | 297.0 → 248.8 | 78.4% → 80.0% | 46.3 → 43.5 |
| harvest_collapse: yield <60% of past mean | 52 / 5 | 271.8 → 236.5 | 42.5% → 53.1% | 129.0 → 106.1 |
| harvest_collapse: yield >=60% of past mean | 140 / 7 | 260.5 → 218.6 | 98.1% → 94.6% | 1.0 → 4.4 |
| extreme_weather: extreme | 104 / 7 | 280.4 → 231.3 | 78.0% → 76.7% | 59.4 → 53.3 |
| extreme_weather: within historical thresholds | 88 / 5 | 342.8 → 302.2 | 85.2% → 85.3% | 38.0 → 34.1 |
| wheat_price_shock: price <=1.2x last known | 133 / 5 | 288.0 → 216.0 | 87.6% → 85.5% | 17.1 → 23.5 |
| wheat_price_shock: price >1.2x last known | 59 / 2 | 288.2 → 275.7 | 69.8% → 78.2% | 97.9 → 64.8 |

## Lecture et fichiers

- Un groupe avec moins de trois années ou quinze cas porte `support=limited` dans le CSV. Les départements partagent des chocs annuels ; le nombre de cas n'est pas un nombre d'années indépendantes.
- `group_comparisons.csv` publie tous les candidats demandés, toutes les régions et quatre pondérations : années égales, années et groupes Agreste connus égaux, années et régions égales, puis groupes Agreste identifiés sur toute la période. Cette dernière est une sensibilité rétrospective de l'évaluation, jamais une donnée d'entraînement.
- `annual_comparisons.csv` conserve chaque écart annuel. `case_groups.csv` contient les caractéristiques passées et les diagnostics. `group_thresholds.json` documente les seuils estimés avec le passé uniquement.
- `department_comparisons.csv` donne chaque département, ses années testées, les fractions de contrats tenus et le nombre de succès requis pour 80 % (6/7 sur sept ans). `department_summary.json` publie les moyennes à poids égal par département et le nombre de départements atteignant 80 %, séparément pour tous, au moins cinq ans et sept ans complets.
- Les intervalles bootstrap sont descriptifs et non corrigés pour la multiplicité des groupes. Ils servent à distinguer les écarts stables des signaux isolés, pas à annoncer un groupe gagnant garanti.
- Les quatre départements donneurs du projet francilien sont 10, 28, 45 et 89. Leur évaluation ne constitue pas une validation sur des récoltes lentille observées en Île-de-France.

La commande exacte figure dans `manifest.json`, champ `command_line`. Le lancement par défaut reproduit l'analyse brute : `python pipeline/analyze_model_groups.py`. Pour ajouter une expérience, renseigner `--prediction-file`, `--baseline`, `--candidates` et `--report-candidate` ; toute cohorte différente est refusée explicitement.
