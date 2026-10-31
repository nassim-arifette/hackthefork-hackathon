# Comparaison par groupes : QRF transféré et M0 transféré

Transfert spatial : la région cible est exclue de tout apprentissage lentille. Les niveaux lentille sont transférés depuis quatre analogues climatiques extérieurs à la région. Les historiques de rendement des départements cibles servent uniquement à des diagnostics rétrospectifs, jamais à choisir les prévisions.

Chaque ligne compare exactement les mêmes départements et années. La perte, les taux tenus, les prix moyens et les manques moyens donnent le même poids à chaque année. Les prix médians sont calculés sur les cas. Les intervalles rééchantillonnent les années entières, avec les écarts appariés au même M0.

L'objectif de 80 % est affiché séparément de la perte économique. Un modèle peut réduire la perte tout en protégeant moins de contrats. Les groupes sont fixés par le script avant inspection des scores ; tous sont publiés, y compris ceux qui régressent. Les résultats par groupes sont exploratoires, pas une règle de sélection validée pour une future campagne.

## Groupes connus avant campagne

| Groupe | Cas / années | Perte M0 transféré → QRF transféré | Gain perte | Tenus M0 transféré → QRF transféré | Δ perte, IC95 % |
|---|---:|---:|---:|---:|---:|
| all: all cases | 192 / 7 | 291.8 → 285.3 | 2.2% | 60.2% → 50.7% | [-26.9 ; 16.5] |
| region: 24 - Centre-Val de Loire | 42 / 7 | 206.4 → 186.9 | 9.4% | 76.2% → 76.2% | [-56.4 ; 13.7] |
| region: 27 - Bourgogne-Franche-Comté | 8 / 7 | 858.3 → 890.9 | -3.8% | 28.6% → 14.3% | [-39.3 ; 111.8] |
| region: 44 - Grand Est | 18 / 7 | 182.7 → 143.2 | 21.6% | 89.3% → 89.3% | [-70.8 ; -7.8] |
| region: 52 - Pays de la Loire | 24 / 7 | 208.9 → 185.8 | 11.0% | 75.0% → 60.7% | [-53.7 ; 13.1] |
| region: 75 - Nouvelle Aquitaine | 26 / 7 | 274.1 → 222.0 | 19.0% | 50.0% → 50.0% | [-95.2 ; -12.1] |
| region: 76 - Occitanie | 50 / 7 | 238.2 → 276.2 | -16.0% | 51.3% → 28.9% | [9.6 ; 65.1] |
| region: 84 - Auvergne-Rhône-Alpes | 24 / 7 | 592.9 → 602.4 | -1.6% | 38.1% → 28.6% | [-45.6 ; 75.3] |
| idf_donor: IDF donor departments | 28 / 7 | 392.9 → 379.1 | 3.5% | 64.3% → 60.7% | [-35.3 ; 5.8] |
| idf_donor: other departments | 164 / 7 | 275.6 → 270.5 | 1.9% | 59.5% → 49.0% | [-25.8 ; 19.3] |

## Diagnostics rétrospectifs

Les étiquettes suivantes utilisent la récolte ou la météo réalisée, le prix réalisé, ou l'ancienne sélection globale des départements. Elles expliquent les échecs ; elles ne sont pas disponibles pour choisir un modèle au moment de signer le contrat.

| Groupe | Cas / années | Perte M0 transféré → QRF transféré | Tenus M0 transféré → QRF transféré | Manque €/ha M0 transféré → QRF transféré |
|---|---:|---:|---:|---:|
| history: <8 years | 36 / 7 | 239.2 → 225.8 | 67.5% → 54.0% | 115.6 → 133.3 |
| history: >=8 years | 156 / 7 | 305.5 → 300.4 | 57.9% → 49.5% | 152.8 → 165.5 |
| volatility: high | 60 / 7 | 310.7 → 313.8 | 64.3% → 51.7% | 149.3 → 172.4 |
| volatility: low | 68 / 7 | 277.2 → 253.9 | 64.0% → 61.1% | 129.9 → 129.6 |
| volatility: medium | 64 / 7 | 291.1 → 293.6 | 51.4% → 37.5% | 159.4 → 179.4 |
| yield_level: high | 97 / 7 | 210.7 → 182.4 | 73.8% → 69.8% | 92.1 → 90.0 |
| yield_level: low | 95 / 7 | 377.1 → 392.7 | 46.0% → 31.0% | 199.8 → 229.4 |
| original_cohort: added 59 | 59 / 7 | 276.8 → 269.4 | 58.1% → 50.4% | 137.5 → 154.4 |
| original_cohort: original 133 | 133 / 7 | 302.8 → 295.4 | 60.0% → 50.5% | 151.8 → 162.7 |
| harvest_collapse: yield <60% of past mean | 52 / 5 | 584.6 → 583.7 | 13.6% → 2.7% | 370.7 → 370.3 |
| harvest_collapse: yield >=60% of past mean | 140 / 7 | 134.6 → 137.9 | 75.0% → 65.5% | 47.4 → 69.2 |
| extreme_weather: extreme | 104 / 7 | 244.9 → 234.8 | 65.7% → 45.6% | 130.6 → 141.5 |
| extreme_weather: within historical thresholds | 88 / 5 | 427.0 → 417.1 | 54.4% → 45.4% | 206.0 → 211.6 |
| wheat_price_shock: price <=1.2x last known | 133 / 5 | 177.2 → 179.9 | 68.8% → 57.4% | 68.9 → 98.0 |
| wheat_price_shock: price >1.2x last known | 59 / 2 | 578.2 → 548.8 | 38.9% → 33.9% | 333.4 → 308.4 |

## Lecture et fichiers

- Un groupe avec moins de trois années ou quinze cas porte `support=limited` dans le CSV. Les départements partagent des chocs annuels ; le nombre de cas n'est pas un nombre d'années indépendantes.
- `group_comparisons.csv` publie tous les candidats demandés, toutes les régions et quatre pondérations : années égales, années et groupes Agreste connus égaux, années et régions égales, puis groupes Agreste identifiés sur toute la période. Cette dernière est une sensibilité rétrospective de l'évaluation, jamais une donnée d'entraînement.
- `annual_comparisons.csv` conserve chaque écart annuel. `case_groups.csv` contient les caractéristiques passées et les diagnostics. `group_thresholds.json` documente les seuils estimés avec le passé uniquement.
- `department_comparisons.csv` donne chaque département, ses années testées, les fractions de contrats tenus et le nombre de succès requis pour 80 % (6/7 sur sept ans). `department_summary.json` publie les moyennes à poids égal par département et le nombre de départements atteignant 80 %, séparément pour tous, au moins cinq ans et sept ans complets.
- Les intervalles bootstrap sont descriptifs et non corrigés pour la multiplicité des groupes. Ils servent à distinguer les écarts stables des signaux isolés, pas à annoncer un groupe gagnant garanti.
- Les quatre départements donneurs du projet francilien sont 10, 28, 45 et 89. Leur évaluation ne constitue pas une validation sur des récoltes lentille observées en Île-de-France.

La commande exacte figure dans `manifest.json`, champ `command_line`. Le lancement par défaut reproduit l'analyse brute : `python pipeline/analyze_model_groups.py`. Pour ajouter une expérience, renseigner `--prediction-file`, `--baseline`, `--candidates` et `--report-candidate` ; toute cohorte différente est refusée explicitement.
