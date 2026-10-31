# Politiques de prix centrées sur la protection à 80 %

Les mêmes corrections sont appliquées à M0 et QRF. Chaque correction utilise uniquement les erreurs de prix issues des prévisions temporelles des années antérieures. Les sélecteurs recherchent le prix moyen le plus bas parmi les politiques ayant tenu au moins 80 % des contrats, en moyenne annuelle, pendant les trois années précédentes. À défaut, ils retiennent la meilleure protection passée, puis le prix le plus bas.

Les 46 politiques fixes et quatre sélecteurs sont tous rapportés. Les trois premières années servent à initialiser les corrections et sélecteurs ; les 192 cas 2019–2025 constituent la comparaison. Une hausse de prix peut augmenter la protection sans améliorer la qualité du modèle. La cible du produit reste 80 %. Les quantiles internes de correction testés ici sont [0.8, 0.9, 0.95] ; les niveaux 90 % et 95 %, s'ils sont présents, constituent des marges contre la dérive à tester, pas un changement de l'objectif produit.

| Politique | Perte contrat €/t ↓ | Tenus, cas | Tenus, années | Prix moyen €/t | Manque moyen €/ha |
|---|---:|---:|---:|---:|---:|
| hybrid__global_selected | 240.72 | 80.7% | 82.0% | 1939 | 43.93 |
| hybrid__regional_selected | 245.66 | 72.9% | 74.3% | 1812 | 62.71 |
| qrf__add_expanding_signed | 212.55 | 67.2% | 69.2% | 1363 | 96.54 |
| qrf__add_expanding_uplift | 207.86 | 69.8% | 71.7% | 1379 | 88.56 |
| qrf__log_3y_signed | 215.29 | 71.4% | 72.7% | 1688 | 62.93 |
| qrf__log_3y_uplift | 211.87 | 73.4% | 74.7% | 1702 | 56.40 |
| qrf__log_5y_q90_signed | 232.96 | 80.2% | 81.6% | 1899 | 43.74 |
| qrf__log_5y_q90_uplift | 232.96 | 80.2% | 81.6% | 1899 | 43.74 |
| qrf__log_5y_q95_signed | 256.08 | 84.9% | 86.0% | 2146 | 29.07 |
| qrf__log_5y_q95_uplift | 256.08 | 84.9% | 86.0% | 2146 | 29.07 |
| qrf__log_5y_signed | 221.50 | 68.8% | 70.7% | 1550 | 81.83 |
| qrf__log_5y_uplift | 216.50 | 71.9% | 73.7% | 1569 | 73.50 |
| qrf__log_expanding_q90_signed | 205.49 | 79.2% | 80.6% | 1754 | 44.43 |
| qrf__log_expanding_q90_uplift | 205.49 | 79.2% | 80.6% | 1754 | 44.43 |
| qrf__log_expanding_q95_signed | 238.15 | 84.4% | 85.5% | 2054 | 29.26 |
| qrf__log_expanding_q95_uplift | 238.15 | 84.4% | 85.5% | 2054 | 29.26 |
| qrf__log_expanding_signed | 209.33 | 67.7% | 69.6% | 1439 | 87.01 |
| qrf__log_expanding_uplift | 204.33 | 70.8% | 72.6% | 1458 | 78.68 |
| qrf__past_selected | 233.04 | 82.3% | 83.5% | 1984 | 35.27 |
| qrf__raw | 209.49 | 63.0% | 64.6% | 1241 | 108.54 |
| qrf__regional_expanding_q90_signed | 227.74 | 74.0% | 75.7% | 1759 | 55.97 |
| qrf__regional_expanding_q90_uplift | 227.73 | 75.0% | 76.7% | 1760 | 55.85 |
| qrf__regional_expanding_q95_signed | 244.75 | 79.7% | 81.1% | 2011 | 38.79 |
| qrf__regional_expanding_q95_uplift | 244.77 | 79.7% | 81.1% | 2011 | 38.79 |
| qrf__regional_expanding_signed | 228.08 | 68.2% | 70.0% | 1443 | 97.71 |
| qrf__regional_expanding_uplift | 220.19 | 70.8% | 72.5% | 1467 | 85.76 |
| trend__add_expanding_signed | 257.44 | 65.6% | 67.7% | 1443 | 116.11 |
| trend__add_expanding_uplift | 249.90 | 68.2% | 70.3% | 1470 | 103.50 |
| trend__log_3y_signed | 273.20 | 69.8% | 71.6% | 1812 | 80.40 |
| trend__log_3y_uplift | 267.32 | 72.4% | 74.2% | 1836 | 69.43 |
| trend__log_5y_q90_signed | 307.95 | 78.1% | 79.6% | 2176 | 53.43 |
| trend__log_5y_q90_uplift | 307.95 | 78.1% | 79.6% | 2176 | 53.43 |
| trend__log_5y_q95_signed | 322.54 | 82.3% | 83.5% | 2390 | 38.41 |
| trend__log_5y_q95_uplift | 322.54 | 82.3% | 83.5% | 2390 | 38.41 |
| trend__log_5y_signed | 286.16 | 67.2% | 69.2% | 1707 | 101.07 |
| trend__log_5y_uplift | 278.44 | 69.8% | 71.7% | 1739 | 87.67 |
| trend__log_expanding_q90_signed | 270.18 | 75.5% | 77.1% | 1929 | 59.42 |
| trend__log_expanding_q90_uplift | 270.18 | 75.5% | 77.1% | 1929 | 59.42 |
| trend__log_expanding_q95_signed | 305.99 | 81.8% | 83.0% | 2306 | 38.54 |
| trend__log_expanding_q95_uplift | 305.99 | 81.8% | 83.0% | 2306 | 38.54 |
| trend__log_expanding_signed | 263.19 | 67.2% | 69.2% | 1538 | 108.37 |
| trend__log_expanding_uplift | 255.47 | 69.8% | 71.7% | 1569 | 94.97 |
| trend__past_selected | 288.03 | 81.2% | 82.5% | 2208 | 40.15 |
| trend__raw | 243.79 | 66.1% | 68.2% | 1341 | 116.84 |
| trend__regional_expanding_q90_signed | 293.38 | 74.0% | 75.7% | 1939 | 71.12 |
| trend__regional_expanding_q90_uplift | 292.83 | 74.0% | 75.7% | 1944 | 70.05 |
| trend__regional_expanding_q95_signed | 316.02 | 75.0% | 76.7% | 2244 | 50.75 |
| trend__regional_expanding_q95_uplift | 315.84 | 75.0% | 76.7% | 2246 | 50.38 |
| trend__regional_expanding_signed | 274.07 | 63.5% | 65.8% | 1529 | 116.75 |
| trend__regional_expanding_uplift | 262.35 | 68.8% | 70.8% | 1570 | 98.07 |

Les tableaux complets, scores annuels, régionaux et départementaux, prix par cas et décisions de sélection sont dans les CSV et `results.json`. `paired_m0_qrf.csv` compare les deux familles sous la même recette de correction et rééchantillonne les années pour les intervalles descriptifs des écarts ; les petits groupes sont signalés. Une protection groupée de 80 % ne signifie pas 80 % dans chaque département. Les groupes régionaux sont administratifs et connus à la signature. Le sélecteur régional exige trois années et douze cas antérieurs ; sinon il utilise le choix global. La correction régionale est ramenée vers la correction globale avec un poids de `n_annees / (n_annees + 5)`.

Les corrections globales signées utilisent le plus petit quantile empirique couvrant le niveau interne choisi du poids des observations passées. Chaque année reçoit un poids total identique. La correction régionale mélange deux quantiles : ce retrait vers le global est une heuristique, pas le quantile exact d'un groupe. Les politiques `uplift` empêchent une baisse sous le prix brut et ne sont donc pas minimales quand la correction signée serait négative. La frontière économique de prix nul est appliquée à la correction additive. `margin_surplus_eur_ha` désigne l'excédent de marge de la lentille sur le blé dans les cas gagnants ; ce n'est pas un montant économiquement trop payé.

Reproduire depuis la racine :

```bash
python pipeline/benchmark_contract_policies.py --calibration-quantiles 0.8 0.9 0.95 --base-protocol modern_raw_raw --output experiments/policies_sensitivity_rerun
```

Aucune donnée de l'année à prédire n'entre dans la correction ni dans le choix de politique. Les résultats décrivent le backtest ; atteindre la contrainte sur le passé ne force pas son respect sur l'année suivante.

Exécution Colab téléchargée et vérifiée. `__raw` signifie ici « sans correction supplémentaire du prix » ; le protocole de simulation de base est `modern_raw_raw`. Le choix minimise le prix passé parmi les candidats admissibles de cette grille, sans prétendre être le minimum parmi tous les modèles possibles.


## Tables détaillées archivées

Les prédictions par cas et les audits complets (`predictions.csv`, `predictions_with_warmup.csv`, `results.json`) sont conservés à l’identique dans `results-colab.zip`. `summary.json` et les CSV agrégés restent directement lisibles dans GitHub. Avant de lancer une analyse qui lit les détails :

```bash
python scripts/restore_audit_artifacts.py
```

La restauration vérifie l’empreinte de l’archive et refuse d’écraser une version locale différente.
