# Résultats Colab du 31 octobre 2026

**QRF est la meilleure base Monte-Carlo du benchmark : perte contrat de 209,5 €/t, contre 285,3 €/t pour TabPFN.** Son taux historique de 63,0 % indique le travail restant pour retrouver les 80 % visés hors échantillon : améliorer la distribution des rendements et leur dépendance. Le modèle direct QRF calibré atteint 82,3 % au total ; son résultat 2025 explique pourquoi il reste un concurrent à améliorer plutôt que le choix retenu.

## Expérience et fichiers

Les deux expériences sont terminées : **56/56 étapes rendement/témoin et 50/50 étapes de contrat direct**. Les tableaux reprennent les résultats originaux ; aucun nouvel entraînement n'a été effectué pour ce rapport.

- [Rendements : résultats JSON](../experiments/colab_2026_10_31/colab_benchmark/results.json) et [prédictions CSV](../experiments/colab_2026_10_31/colab_benchmark/predictions.csv).
- [Contrat direct : résultats JSON](../experiments/colab_2026_10_31/colab_contract/results.json) et [prédictions CSV](../experiments/colab_2026_10_31/colab_contract/predictions.csv).
- [Archive complète des résultats](../experiments/colab_2026_10_31/results-full.zip) et [archive des sources exécutées](../experiments/colab_2026_10_31/input-snapshot.zip).

L'archive d'entrée a pour SHA-256 `60304f3585c0c8850dfeef82f81dd4edff23f988f9a3d47f63a21a8dcef999c6` ; le checkout source est `54d9f666ebc9c64a8ac45944225337ca2401e0e6`. Le JSON brut conserve `source_commit: unknown` : Colab exécutait les sources extraites sans répertoire `.git`. Le message Git du journal concerne cette métadonnée, pas l'entraînement. Les empreintes des scripts et données ainsi que les versions sont conservées dans les JSON, notamment Python 3.13.16, TabPFN 9.0.0 et CatBoost 1.2.10 ; l'adaptateur TabPFN sélectionne la famille 3.5.

Les **19 configurations** couvrent les mêmes **192 cas département × année de 2019 à 2025**. Le premier benchmark compare sept modèles de rendement lentille et un témoin historique ; le modèle blé reste linéaire pour tous les Monte-Carlo. Il utilise 20 000 scénarios, la graine 42, la calibration glissante et les quantiles de distribution bruts (`raw`). Le second compare cinq modèles directs, leurs versions calibrées et la sélection `direct_auto`. Ses années 2016–2018 servent à initialiser la calibration et ne sont pas comptées dans les scores.

## Lire les métriques

La décision est le plus petit prix départ ferme tel que la marge lentille soit au moins celle du blé dans 80 % des scénarios : `P* = Q80((prix_ble × Y_ble − C_ble + C_lentille − aide − rotation) / Y_lentille)`. Le Monte-Carlo utilise le quantile empirique `inverted_cdf`, égalités comprises. Les modèles directs prédisent ce quantile sans passer par les 20 000 simulations.

La **perte contrat** est la pinball à 0,8 du prix d'équilibre réalisé : elle pénalise une sous-estimation de 100 €/t de 80 points et une surestimation de 100 €/t de 20 points. La perte et le manque moyen donnent le même poids à chaque année. « Tenus, cas » compte les 192 observations ; « Tenus, années » moyenne les sept taux annuels. Le manque moyen en €/ha inclut les cas sans déficit, à zéro.

**Les prix ci-dessous sont des médianes de contrats historiques, pas des prévisions 2026.** La colonne `coverage` des JSON porte sur les intervalles élargis de rendement, avec météo réalisée. Ainsi, les 80,1 % de couverture du QRF ne sont pas les 63,0 % de contrats tenus. Atteindre 80 % dans la distribution simulée ne prouve pas une réussite historique de 80 %.

## Rendements puis Monte-Carlo

Classement par perte contrat croissante ; `paired_history` est le témoin fondé sur les rendements et prix historiques appariés.

| Configuration | Perte contrat €/t ↓ | Tenus, cas | Tenus, années | Prix médian €/t | Manque moyen €/ha |
|---|---:|---:|---:|---:|---:|
| qrf | 209,5 | 63,0 % | 64,6 % | 1 159 | 108,5 |
| ensemble | 226,4 | 63,0 % | 65,0 % | 1 154 | 120,0 |
| lightgbm | 236,3 | 57,8 % | 59,7 % | 1 048 | 143,2 |
| trend | 243,8 | 66,1 % | 68,2 % | 1 254 | 116,8 |
| catboost | 256,3 | 55,7 % | 57,7 % | 1 020 | 160,3 |
| linear | 264,8 | 67,7 % | 69,8 % | 1 370 | 113,2 |
| tabpfn | 285,3 | 49,5 % | 51,7 % | 975 | 189,6 |
| paired_history | 323,3 | 47,9 % | 50,3 % | 929 | 216,9 |

QRF obtient la meilleure perte et le plus faible manque moyen de cette famille. TabPFN tient 95 contrats sur 192, contre 121 pour QRF. CatBoost obtient la plus faible valeur de la colonne `pinball` du run (0,0954, calculée sur les bornes élargies de rendement), mais sa perte contrat est de 256,3 €/t : le classement sur le rendement ne sélectionne pas le meilleur contrat. Aucun Monte-Carlo testé n'atteint 80 % de contrats historiques tenus.

## Prévision directe du prix d'équilibre

Les versions `_cal` appliquent une correction signée des erreurs logarithmiques des trois années précédentes, avec un poids total identique par année. `direct_auto` choisit sur la perte des années antérieures parmi les candidats disponibles ; il inclut ici TabPFN.

| Configuration | Perte contrat €/t ↓ | Tenus, cas | Tenus, années | Prix médian €/t | Manque moyen €/ha |
|---|---:|---:|---:|---:|---:|
| direct_lightgbm | 261,0 | 65,6 % | 66,3 % | 1 158 | 92,2 |
| direct_qrf | 280,9 | 78,1 % | 79,6 % | 1 511 | 58,7 |
| direct_tabpfn | 281,0 | 71,4 % | 73,1 % | 1 477 | 75,0 |
| direct_linear | 283,3 | 77,1 % | 78,4 % | 1 524 | 64,3 |
| direct_pooled | 290,2 | 63,5 % | 65,8 % | 1 314 | 116,1 |
| direct_qrf_cal | 316,5 | 82,3 % | 82,3 % | 1 744 | 39,1 |
| direct_lightgbm_cal | 331,6 | 76,0 % | 75,3 % | 1 544 | 73,9 |
| direct_auto | 331,6 | 71,9 % | 72,0 % | 1 590 | 62,6 |
| direct_linear_cal | 331,8 | 79,2 % | 78,9 % | 1 761 | 48,1 |
| direct_tabpfn_cal | 335,0 | 79,7 % | 80,4 % | 1 719 | 45,5 |
| direct_pooled_cal | 339,7 | 79,7 % | 81,1 % | 1 681 | 51,8 |

`direct_qrf_cal` est la seule configuration qui dépasse 80 % sur les cas regroupés : **158/192**. `direct_tabpfn_cal` et `direct_pooled_cal` restent à **153/192 = 79,69 %**, même si leur moyenne annuelle dépasse 80 %. Le meilleur score direct appartient à LightGBM ; il reste supérieur à la perte du QRF Monte-Carlo. TabPFN direct est presque à égalité avec QRF direct en perte (281,0 contre 280,9), avec moins de contrats tenus et davantage de manque moyen.

## Contrôle année par année

Les taux annuels suivants sont recalculés à partir des CSV. Les observations d'une même année partagent des chocs ; les 192 cas ne représentent donc pas 192 années indépendantes.

| Année | Cas | QRF Monte-Carlo | TabPFN Monte-Carlo | QRF direct | QRF direct calibré | TabPFN direct calibré |
|---|---:|---:|---:|---:|---:|---:|
| 2019 | 28 | 60,7 % | 46,4 % | 60,7 % | 82,1 % | 67,9 % |
| 2020 | 30 | 46,7 % | 33,3 % | 50,0 % | 83,3 % | 73,3 % |
| 2021 | 30 | 46,7 % | 33,3 % | 53,3 % | 63,3 % | 53,3 % |
| 2022 | 29 | 41,4 % | 13,8 % | 93,1 % | 93,1 % | 93,1 % |
| 2023 | 27 | 77,8 % | 51,9 % | 100,0 % | 100,0 % | 100,0 % |
| 2024 | 24 | 95,8 % | 95,8 % | 100,0 % | 100,0 % | 100,0 % |
| 2025 | 24 | 83,3 % | 87,5 % | 100,0 % | 54,2 % | 75,0 % |

Les bonnes années récentes ne résument pas la performance du QRF Monte-Carlo : ses pertes annuelles culminent à **453,1 €/t en 2021** et **401,9 €/t en 2022**, contre **66,0 €/t en 2025**.

La calibration directe ne constitue pas un choix par défaut sur le seul 82,3 %. En 2025, elle multiplie les prix QRF directs par **0,560** : le prix médian passe de **1 117 à 625 €/t**, et les contrats tenus de **24/24 à 13/24**. La perte de cette année diminue pourtant de **136,0 à 79,2 €/t**. Ce cas illustre précisément pourquoi gagner en perte et tenir au moins 80 % des contrats ne sont pas des critères interchangeables. Le contrôle 2026 déjà publié dans [RECHERCHE_MODELES.md](RECHERCHE_MODELES.md) relève aussi une forte réduction du prix par cette correction ; ce n'est pas une nouvelle prévision issue du run Colab.

L'intervalle bootstrap à 80 %, obtenu en rééchantillonnant les années, est de **55,1–74,3 %** pour le taux annuel moyen du QRF Monte-Carlo, et **74,2–90,2 %** pour le QRF direct calibré. Ce dernier résultat ne démontre donc pas un taux futur d'au moins 80 %. Les années 2019–2025 ayant déjà servi à explorer les modèles, il s'agit d'une comparaison temporelle de recherche, pas d'une nouvelle validation indépendante.

## Décision et deux expériences suivantes

**Conserver QRF comme référence Monte-Carlo à améliorer.** Ne promouvoir ni TabPFN ni la calibration directe sur ce run. L'objectif reste le prix minimal satisfaisant les 80 % simulés, avec une distribution suffisamment calibrée pour retrouver cette protection hors échantillon.

1. Comparer QRF avec une grille de quantiles plus dense à la reconstruction actuelle Q10/Q50/Q90 et queues linéaires, en gardant les mêmes années, hypothèses et 20 000 scénarios.
2. À distributions marginales inchangées, comparer les tirages résiduels indépendants à des rangs de résidus blé/lentille appariés, estimés sur des prévisions temporelles hors échantillon. Partager l'année météo ne conserve pas toute cette dépendance.

Ces deux changements doivent être évalués séparément contre le QRF actuel, avec perte contrat, taux tenu annuel et manque à l'hectare.
