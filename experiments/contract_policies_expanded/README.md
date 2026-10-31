# Politiques de prix centrées sur la protection à 80 %

Les mêmes corrections sont appliquées à M0 et QRF. Chaque correction utilise uniquement les erreurs de prix issues des prévisions temporelles des années antérieures. Les sélecteurs recherchent le prix moyen le plus bas parmi les politiques ayant tenu au moins 80 % des contrats, en moyenne annuelle, pendant les trois années précédentes. À défaut, ils retiennent la meilleure protection passée, puis le prix le plus bas.

Les 46 politiques fixes et quatre sélecteurs sont tous rapportés. Les trois premières années servent à initialiser les corrections et sélecteurs ; les 192 cas 2019–2025 constituent la comparaison. Une hausse de prix peut augmenter la protection sans améliorer la qualité du modèle. La cible du produit reste 80 %. Les quantiles internes de correction testés ici sont [0.8, 0.9, 0.95] ; les niveaux 90 % et 95 %, s'ils sont présents, constituent des marges contre la dérive à tester, pas un changement de l'objectif produit.

| Politique | Perte contrat €/t ↓ | Tenus, cas | Tenus, années | Prix moyen €/t | Manque moyen €/ha |
|---|---:|---:|---:|---:|---:|
| hybrid__global_selected | 247.01 | 81.2% | 82.5% | 2033 | 38.08 |
| hybrid__regional_selected | 246.69 | 77.1% | 78.5% | 1994 | 39.31 |
| qrf__add_expanding_signed | 211.04 | 72.4% | 74.0% | 1605 | 70.25 |
| qrf__add_expanding_uplift | 201.34 | 76.6% | 78.1% | 1651 | 53.19 |
| qrf__log_3y_signed | 224.23 | 74.0% | 75.2% | 1796 | 56.95 |
| qrf__log_3y_uplift | 222.80 | 79.7% | 81.0% | 1871 | 41.78 |
| qrf__log_5y_q90_signed | 254.95 | 81.2% | 82.6% | 2074 | 37.83 |
| qrf__log_5y_q90_uplift | 254.91 | 81.8% | 83.1% | 2076 | 37.30 |
| qrf__log_5y_q95_signed | 290.34 | 85.9% | 87.0% | 2368 | 23.29 |
| qrf__log_5y_q95_uplift | 290.34 | 85.9% | 87.0% | 2368 | 23.29 |
| qrf__log_5y_signed | 230.85 | 74.0% | 75.6% | 1731 | 67.08 |
| qrf__log_5y_uplift | 219.63 | 79.7% | 81.2% | 1788 | 48.56 |
| qrf__log_expanding_q90_signed | 230.70 | 80.2% | 81.6% | 1947 | 38.31 |
| qrf__log_expanding_q90_uplift | 230.65 | 80.7% | 82.1% | 1949 | 37.78 |
| qrf__log_expanding_q95_signed | 268.84 | 85.9% | 87.0% | 2258 | 23.46 |
| qrf__log_expanding_q95_uplift | 268.84 | 85.9% | 87.0% | 2258 | 23.46 |
| qrf__log_expanding_signed | 215.30 | 71.9% | 73.6% | 1622 | 70.27 |
| qrf__log_expanding_uplift | 204.13 | 77.6% | 79.1% | 1679 | 51.75 |
| qrf__past_selected | 243.44 | 82.3% | 83.4% | 2072 | 31.85 |
| qrf__raw | 198.62 | 75.5% | 77.1% | 1622 | 54.69 |
| qrf__regional_expanding_q90_signed | 241.65 | 76.6% | 78.1% | 1937 | 45.40 |
| qrf__regional_expanding_q90_uplift | 239.98 | 79.2% | 80.7% | 1954 | 41.34 |
| qrf__regional_expanding_q95_signed | 266.05 | 82.8% | 84.1% | 2203 | 29.64 |
| qrf__regional_expanding_q95_uplift | 265.78 | 83.3% | 84.6% | 2207 | 28.84 |
| qrf__regional_expanding_signed | 236.62 | 70.3% | 72.1% | 1625 | 82.33 |
| qrf__regional_expanding_uplift | 214.02 | 76.0% | 77.6% | 1710 | 53.75 |
| trend__add_expanding_signed | 313.32 | 66.7% | 68.7% | 1936 | 90.72 |
| trend__add_expanding_uplift | 298.80 | 74.0% | 75.7% | 1998 | 66.63 |
| trend__log_3y_signed | 332.84 | 72.9% | 74.6% | 2226 | 68.00 |
| trend__log_3y_uplift | 338.40 | 79.2% | 80.6% | 2344 | 51.14 |
| trend__log_5y_q90_signed | 399.77 | 79.7% | 81.1% | 2718 | 45.31 |
| trend__log_5y_q90_uplift | 399.24 | 81.2% | 82.6% | 2727 | 43.29 |
| trend__log_5y_q95_signed | 445.20 | 84.9% | 86.0% | 3066 | 31.88 |
| trend__log_5y_q95_uplift | 445.20 | 84.9% | 86.0% | 3067 | 31.69 |
| trend__log_5y_signed | 354.64 | 67.7% | 69.7% | 2167 | 87.47 |
| trend__log_5y_uplift | 337.67 | 76.0% | 77.7% | 2246 | 60.84 |
| trend__log_expanding_q90_signed | 342.61 | 78.6% | 80.1% | 2415 | 46.94 |
| trend__log_expanding_q90_uplift | 342.08 | 80.2% | 81.6% | 2424 | 44.92 |
| trend__log_expanding_q95_signed | 408.32 | 84.9% | 86.0% | 2881 | 31.97 |
| trend__log_expanding_q95_uplift | 408.33 | 84.9% | 86.0% | 2882 | 31.77 |
| trend__log_expanding_signed | 321.18 | 65.6% | 67.8% | 1956 | 92.06 |
| trend__log_expanding_uplift | 304.21 | 74.0% | 75.7% | 2034 | 65.43 |
| trend__past_selected | 366.39 | 82.8% | 84.0% | 2636 | 36.73 |
| trend__raw | 294.63 | 74.0% | 75.7% | 1968 | 67.92 |
| trend__regional_expanding_q90_signed | 370.45 | 74.5% | 76.2% | 2441 | 59.53 |
| trend__regional_expanding_q90_uplift | 367.38 | 77.1% | 78.7% | 2468 | 53.11 |
| trend__regional_expanding_q95_signed | 410.03 | 79.7% | 81.1% | 2803 | 42.11 |
| trend__regional_expanding_q95_uplift | 408.93 | 81.8% | 83.0% | 2812 | 39.34 |
| trend__regional_expanding_signed | 339.37 | 66.1% | 68.2% | 1960 | 102.92 |
| trend__regional_expanding_uplift | 310.05 | 76.6% | 78.2% | 2074 | 64.20 |

Les tableaux complets, scores annuels, régionaux et départementaux, prix par cas et décisions de sélection sont dans les CSV et `results.json`. `paired_m0_qrf.csv` compare les deux familles sous la même recette de correction et rééchantillonne les années pour les intervalles descriptifs des écarts ; les petits groupes sont signalés. Une protection groupée de 80 % ne signifie pas 80 % dans chaque département. Les groupes régionaux sont administratifs et connus à la signature. Le sélecteur régional exige trois années et douze cas antérieurs ; sinon il utilise le choix global. La correction régionale est ramenée vers la correction globale avec un poids de `n_annees / (n_annees + 5)`.

Les corrections globales signées utilisent le plus petit quantile empirique couvrant le niveau interne choisi du poids des observations passées. Chaque année reçoit un poids total identique. La correction régionale mélange deux quantiles : ce retrait vers le global est une heuristique, pas le quantile exact d'un groupe. Les politiques `uplift` empêchent une baisse sous le prix brut et ne sont donc pas minimales quand la correction signée serait négative. La frontière économique de prix nul est appliquée à la correction additive. `margin_surplus_eur_ha` désigne l'excédent de marge de la lentille sur le blé dans les cas gagnants ; ce n'est pas un montant économiquement trop payé.

Reproduire depuis la racine :

```bash
python pipeline/benchmark_contract_policies.py --calibration-quantiles 0.8 0.9 0.95 --base-protocol modern_expanded_expanded --output experiments/policies_expanded_rerun
```

Aucune donnée de l'année à prédire n'entre dans la correction ni dans le choix de politique. Les résultats décrivent le backtest ; atteindre la contrainte sur le passé ne force pas son respect sur l'année suivante.

Exécution Colab téléchargée et vérifiée. `__raw` signifie ici « sans correction supplémentaire du prix » ; le protocole de simulation de base est `modern_expanded_expanded`. Le choix minimise le prix passé parmi les candidats admissibles de cette grille, sans prétendre être le minimum parmi tous les modèles possibles.


## Tables détaillées archivées

Les prédictions par cas et les audits complets (`predictions.csv`, `predictions_with_warmup.csv`, `results.json`) sont conservés à l’identique dans `results-colab.zip`. `summary.json` et les CSV agrégés restent directement lisibles dans GitHub. Avant de lancer une analyse qui lit les détails :

```bash
python scripts/restore_audit_artifacts.py
```

La restauration vérifie l’empreinte de l’archive et refuse d’écraser une version locale différente.
