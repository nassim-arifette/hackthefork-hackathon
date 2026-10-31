# Politiques de prix centrées sur la protection à 80 %

Les mêmes corrections sont appliquées à M0 et QRF. Chaque correction utilise uniquement les erreurs de prix issues des prévisions temporelles des années antérieures. Les sélecteurs recherchent le prix moyen le plus bas parmi les politiques ayant tenu au moins 80 % des contrats, en moyenne annuelle, pendant les trois années précédentes. À défaut, ils retiennent la meilleure protection passée, puis le prix le plus bas.

Les 22 politiques fixes et quatre sélecteurs sont tous rapportés. Les trois premières années servent à initialiser les corrections et sélecteurs ; les 192 cas 2019–2025 constituent la comparaison. Une hausse de prix peut augmenter la protection sans améliorer la qualité du modèle.

| Politique | Perte contrat €/t ↓ | Tenus, cas | Tenus, années | Prix moyen €/t | Manque moyen €/ha |
|---|---:|---:|---:|---:|---:|
| trend__raw | 243.79 | 66.1% | 68.2% | 1341 | 116.84 |
| qrf__raw | 209.49 | 63.0% | 64.6% | 1241 | 108.54 |
| trend__log_expanding_signed | 263.19 | 67.2% | 69.2% | 1538 | 108.37 |
| qrf__log_expanding_signed | 209.33 | 67.7% | 69.6% | 1439 | 87.01 |
| trend__regional_expanding_signed | 274.07 | 63.5% | 65.8% | 1529 | 116.75 |
| qrf__regional_expanding_signed | 228.08 | 68.2% | 70.0% | 1443 | 97.71 |
| trend__past_selected | 275.17 | 71.9% | 73.7% | 1850 | 73.24 |
| qrf__past_selected | 217.52 | 74.5% | 76.1% | 1695 | 61.40 |
| hybrid__global_selected | 229.91 | 73.4% | 75.1% | 1650 | 72.26 |
| hybrid__regional_selected | 224.78 | 68.2% | 69.9% | 1536 | 89.85 |

Les tableaux complets, scores annuels, régionaux et départementaux, prix par cas et décisions de sélection sont dans les CSV et `results.json`. `paired_m0_qrf.csv` compare les deux familles sous la même recette de correction et rééchantillonne les années pour les intervalles descriptifs des écarts ; les petits groupes sont signalés. Une protection groupée de 80 % ne signifie pas 80 % dans chaque département. Les groupes régionaux sont administratifs et connus à la signature. Le sélecteur régional exige trois années et douze cas antérieurs ; sinon il utilise le choix global. La correction régionale est ramenée vers la correction globale avec un poids de `n_annees / (n_annees + 5)`.

Les corrections globales signées utilisent le plus petit quantile empirique couvrant 80 % du poids des observations passées. Chaque année reçoit un poids total identique. La correction régionale mélange deux quantiles : ce retrait vers le global est une heuristique, pas le quantile exact d'un groupe. Les politiques `uplift` empêchent une baisse sous le prix brut et ne sont donc pas minimales quand la correction signée serait négative. La frontière économique de prix nul est appliquée à la correction additive. `margin_surplus_eur_ha` désigne l'excédent de marge de la lentille sur le blé dans les cas gagnants ; ce n'est pas un montant économiquement trop payé.

Reproduire depuis la racine :

```bash
python pipeline/benchmark_contract_policies.py
```

Aucune donnée de l'année à prédire n'entre dans la correction ni dans le choix de politique. Les résultats décrivent le backtest ; atteindre la contrainte sur le passé ne force pas son respect sur l'année suivante.


## Tables détaillées archivées

Les prédictions par cas et les audits complets (`predictions.csv`, `predictions_with_warmup.csv`, `results.json`) sont conservés à l’identique dans `results-colab.zip`. `summary.json` et les CSV agrégés restent directement lisibles dans GitHub. Avant de lancer une analyse qui lit les détails :

```bash
python scripts/restore_audit_artifacts.py
```

La restauration vérifie l’empreinte de l’archive et refuse d’écraser une version locale différente.
