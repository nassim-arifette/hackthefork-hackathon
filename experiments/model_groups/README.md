# Comparaison par groupes : QRF dense et M0

M0 désigne ici la famille `trend`, réévaluée dans le même protocole de recherche que QRF, avec le même modèle blé et les mêmes scénarios. Les taux de l'ancien système calibré à 82 % ne sont pas les taux de cette référence à quantiles bruts.

Chaque ligne compare exactement les mêmes départements et années. La perte, les taux tenus, les prix moyens et les manques moyens donnent le même poids à chaque année. Les prix médians sont calculés sur les cas. Les intervalles rééchantillonnent les années entières, avec les écarts appariés au même M0.

L'objectif de 80 % est affiché séparément de la perte économique. Un modèle peut réduire la perte tout en protégeant moins de contrats. Les groupes sont fixés par le script avant inspection des scores ; tous sont publiés, y compris ceux qui régressent. Les résultats par groupes sont exploratoires, pas une règle de sélection validée pour une future campagne.

## Groupes connus avant campagne

| Groupe | Cas / années | Perte M0 → QRF dense | Gain perte | Tenus M0 → QRF dense | Δ perte, IC95 % |
|---|---:|---:|---:|---:|---:|
| all: all cases | 192 / 7 | 243.8 → 208.5 | 14.5% | 68.2% → 65.6% | [-64.0 ; -8.3] |
| region: 24 - Centre-Val de Loire | 42 / 7 | 165.5 → 169.2 | -2.2% | 76.2% → 69.0% | [-23.4 ; 29.6] |
| region: 27 - Bourgogne-Franche-Comté | 8 / 7 | 659.5 → 573.8 | 13.0% | 42.9% → 42.9% | [-197.9 ; 12.5] |
| region: 44 - Grand Est | 18 / 7 | 224.2 → 171.4 | 23.5% | 57.1% → 57.1% | [-116.0 ; -2.4] |
| region: 52 - Pays de la Loire | 24 / 7 | 230.2 → 206.2 | 10.4% | 82.1% → 85.7% | [-55.5 ; 3.2] |
| region: 75 - Nouvelle Aquitaine | 26 / 7 | 241.4 → 177.7 | 26.4% | 60.7% → 67.9% | [-106.8 ; -24.4] |
| region: 76 - Occitanie | 50 / 7 | 227.3 → 204.8 | 9.9% | 70.8% → 62.6% | [-63.4 ; 5.8] |
| region: 84 - Auvergne-Rhône-Alpes | 24 / 7 | 338.0 → 262.1 | 22.5% | 67.9% → 66.7% | [-130.5 ; -22.9] |
| history: <8 years | 36 / 7 | 221.7 → 190.6 | 14.0% | 69.1% → 74.8% | [-65.6 ; -2.5] |
| history: >=8 years | 156 / 7 | 250.5 → 214.2 | 14.5% | 67.8% → 63.6% | [-68.9 ; -7.0] |
| volatility: high | 60 / 7 | 284.0 → 240.9 | 15.2% | 70.7% → 69.3% | [-81.8 ; -7.2] |
| volatility: low | 68 / 7 | 261.2 → 224.8 | 13.9% | 62.9% → 56.5% | [-82.5 ; -4.5] |
| volatility: medium | 64 / 7 | 194.3 → 164.8 | 15.2% | 69.8% → 70.7% | [-57.7 ; -3.6] |
| yield_level: high | 97 / 7 | 213.1 → 189.2 | 11.2% | 69.0% → 66.4% | [-41.8 ; -4.2] |
| yield_level: low | 95 / 7 | 276.9 → 229.7 | 17.0% | 67.0% → 64.4% | [-94.8 ; -6.3] |
| idf_donor: IDF donor departments | 28 / 7 | 328.6 → 293.1 | 10.8% | 60.7% → 60.7% | [-77.1 ; 9.4] |
| idf_donor: other departments | 164 / 7 | 230.9 → 195.7 | 15.2% | 69.4% → 66.3% | [-62.1 ; -10.4] |

## Diagnostics rétrospectifs

Les étiquettes suivantes utilisent la récolte ou la météo réalisée, le prix réalisé, ou l'ancienne sélection globale des départements. Elles expliquent les échecs ; elles ne sont pas disponibles pour choisir un modèle au moment de signer le contrat.

| Groupe | Cas / années | Perte M0 → QRF dense | Tenus M0 → QRF dense | Manque €/ha M0 → QRF dense |
|---|---:|---:|---:|---:|
| original_cohort: added 59 | 59 / 7 | 249.9 → 195.8 | 66.9% → 65.7% | 125.2 → 103.2 |
| original_cohort: original 133 | 133 / 7 | 248.3 → 220.6 | 68.2% → 65.6% | 113.5 → 107.4 |
| harvest_collapse: yield <60% of past mean | 52 / 5 | 458.9 → 431.2 | 19.0% → 4.3% | 309.3 → 296.1 |
| harvest_collapse: yield >=60% of past mean | 140 / 7 | 112.2 → 90.7 | 84.4% → 85.7% | 32.3 → 23.9 |
| extreme_weather: extreme | 104 / 7 | 256.2 → 225.3 | 67.0% → 65.7% | 140.1 → 130.8 |
| extreme_weather: within historical thresholds | 88 / 5 | 278.4 → 213.9 | 55.9% → 60.4% | 159.2 → 107.7 |
| wheat_price_shock: price <=1.2x last known | 133 / 5 | 145.5 → 124.8 | 80.6% → 73.6% | 34.8 → 49.5 |
| wheat_price_shock: price >1.2x last known | 59 / 2 | 489.6 → 417.8 | 37.2% → 45.7% | 321.9 → 247.1 |

## Lecture et fichiers

- Un groupe avec moins de trois années ou quinze cas porte `support=limited` dans le CSV. Les départements partagent des chocs annuels ; le nombre de cas n'est pas un nombre d'années indépendantes.
- `group_comparisons.csv` publie tous les candidats demandés, toutes les régions et quatre pondérations : années égales, années et groupes Agreste connus égaux, années et régions égales, puis groupes Agreste identifiés sur toute la période. Cette dernière est une sensibilité rétrospective de l'évaluation, jamais une donnée d'entraînement.
- `annual_comparisons.csv` conserve chaque écart annuel. `case_groups.csv` contient les caractéristiques passées et les diagnostics. `group_thresholds.json` documente les seuils estimés avec le passé uniquement.
- `department_comparisons.csv` donne chaque département, ses années testées, les fractions de contrats tenus et le nombre de succès requis pour 80 % (6/7 sur sept ans). `department_summary.json` publie les moyennes à poids égal par département et le nombre de départements atteignant 80 %, séparément pour tous, au moins cinq ans et sept ans complets.
- Les intervalles bootstrap sont descriptifs et non corrigés pour la multiplicité des groupes. Ils servent à distinguer les écarts stables des signaux isolés, pas à annoncer un groupe gagnant garanti.
- Les quatre départements donneurs du projet francilien sont 10, 28, 45 et 89. Leur évaluation ne constitue pas une validation sur des récoltes lentille observées en Île-de-France.

La commande exacte figure dans `manifest.json`, champ `command_line`. Le lancement par défaut reproduit l'analyse brute : `python pipeline/analyze_model_groups.py`. Pour ajouter une expérience, renseigner `--prediction-file`, `--baseline`, `--candidates` et `--report-candidate` ; toute cohorte différente est refusée explicitement.
