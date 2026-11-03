# Attribution de l'écart entre ancien et nouveau protocole

Exécuté dans Google Colab le 31 octobre 2026, CPU un thread, 165 secondes. Les simulations comparatives utilisent 20 000 tirages communs ; la reproduction historique conserve ses 6 000 tirages et ses graines d'origine. Les trois modèles sont `trend` (famille M0), `linear` (famille M1) et `qrf`. Le modèle blé reste M1/linéaire dans toutes les comparaisons.

## Contrôles de reproduction

- **Les 266 prix historiques M0/M1 arrondis sont identiques aux exports d'origine**, et tous les verdicts de marge concordent : 133 observations par modèle.
- Les **576 prix modernes bruts** M0/M1/QRF reproduisent les résultats Colab précédents à moins de **4,55 × 10⁻¹³ €/t** : 192 observations par modèle.
- 3 tests unitaires passent ; revue indépendante du script réalisée. Après téléchargement, tous les agrégats, 30 coupures d'entraînement et 90 coupures de calibration ont été vérifiés.
- Les 133 cas historiques sont inclus dans les 192 modernes. L'évaluation porte sur 2019–2025 ; les prévisions modernes 2016–2018 servent uniquement à amorcer des politiques décidées sur le passé.

## Pourquoi l'ancien M1 tenait davantage de contrats

Ces étapes sont comparées sur les **mêmes 133 cas**. Chaque ligne modifie seulement le bloc indiqué par rapport à la précédente ; cette décomposition suit un chemin explicite et n'est pas une attribution unique indépendante de l'ordre.

| Étape M1 | Contrats tenus | Prix médian €/t | Perte contrat €/t | Manque moyen €/ha |
|---|---:|---:|---:|---:|
| Pipeline historique exact | 85,7 % | 2 658 | 357,04 | 31,11 |
| Tirages/quantile alignés sur le benchmark récent | 85,7 % | 2 603 | 352,00 | 30,70 |
| Regroupements estimés sur les seules observations utilisables passées | 79,7 % | 2 005 | 309,16 | 57,33 |
| Préparation météo moderne, calibration historique conservée | 78,9 % | 1 923 | 283,67 | 58,98 |
| Calibration glissante moderne, quantiles élargis simulés | 75,9 % | 1 889 | 293,69 | 69,19 |
| Quantiles bruts simulés | 70,7 % | 1 412 | 271,70 | 111,71 |

Les 59 observations supplémentaires ne sont donc pas la cause principale de la chute de protection. L'ancien M1 combine regroupement global, préparation et calibration différentes, puis simulation à partir des bornes élargies. Il propose des prix plus élevés. La version récente a changé plusieurs blocs simultanément, pas uniquement le modèle de rendement.

Le pont `past_groups_legacy_weather_cal` change le regroupement global en regroupement sur les données utilisables strictement passées. Il impose aussi trois observations historiques au blé, comme le protocole moderne. Il conserve la climatologie fixe et la calibration/refit historiques. `modern_prep_legacy_cal` conserve les modèles finaux et la préparation moderne, mais remplace la calibration glissante par l'ancienne règle signée. Ces ponts sont des diagnostics du changement de protocole, pas des candidats proposés pour déploiement.

## Comparer QRF à M0 au même protocole

Sur les mêmes **192 cas**, avec calibration glissante, mêmes tirages et mêmes choix de simulation pour les deux modèles :

| Simulation | Modèle | Perte contrat €/t ↓ | Contrats tenus ↑ | Prix médian €/t | Manque moyen €/ha ↓ |
|---|---|---:|---:|---:|---:|
| Quantiles bruts | M0 | 243,79 | 66,1 % | 1 254 | 116,84 |
| Quantiles bruts | QRF | 209,49 | 63,0 % | 1 159 | 108,54 |
| Quantiles élargis | M0 | 294,63 | 74,0 % | 1 831 | 67,92 |
| Quantiles élargis | QRF | **198,62** | **75,5 %** | **1 483** | **54,69** |

QRF avec quantiles élargis améliore les quatre indicateurs face à M0 utilisant le même protocole. Cela ne s'applique pas à chaque année :

- **2020** : QRF tient 50 % contre 60 % pour M0 ; perte 173,5 contre 162,2 €/t.
- **2022** : QRF tient 62,1 % contre 44,8 % ; perte 245,5 contre 314,8 €/t.
- **2024** : les deux tiennent 100 % ; QRF réduit le prix médian de 2 771 à 1 614 €/t.
- **2025** : QRF tient 95,8 % contre 100 %, avec un prix médian de 1 045 contre 2 526 €/t et une perte de 91,5 contre 398,5 €/t.

Globalement QRF propose un prix inférieur dans 119 cas sur 192 ; il gagne huit contrats que M0 perd et en perd cinq que M0 tient. Les années restent l'unité des chocs, les départements d'une même année étant corrélés. Le taux global de 75,5 % reste inférieur à la cible de 80 %.

## Factoriel lentille/blé

Les quatre variantes `modern_raw_raw`, `modern_expanded_raw`, `modern_raw_expanded`, `modern_expanded_expanded` conservent exactement les mêmes modèles et tirages. Elles permettent de séparer l'élargissement côté lentille de celui côté blé.

Pour M1 sur les 133 cas, l'élargissement augmente le prix moyen d'environ **467 €/t** : attribution symétrique **462 €/t côté lentille** et **6 €/t côté blé** (poids égaux des cas). La même allocation du gain de contrats tenus est de **3,76 points côté lentille** et **1,50 point côté blé**. La contribution au prix est donc dominée par la lentille, qui intervient au dénominateur du prix d'équilibre. Ce calcul décrit les effets de construction des scénarios ; il ne transforme pas les bornes d'un intervalle calibré en quantiles de distribution garantis.

## Fichiers et reproduction

- `predictions.csv` : 3 796 prédictions d'évaluation, avec protocole, modèle, prix, seuil réalisé, marge manquante, rendements réalisés, ajustements et appartenance aux 133 anciens cas.
- `predictions_with_warmup.csv` : 4 780 lignes, incluant les années 2016–2018 pour les quatre variantes modernes.
- `results.json`, `summary.csv`, `annual_metrics.csv` : agrégats et audits.
- `legacy_reproduction.csv` : contrôle des 266 décisions historiques.
- `attribution_steps.csv` : différences successives sur les 133 cas ; `factorial_attribution.csv` : contributions symétriques des élargissements.
- `manifest.json`, `execution.json` : versions, paramètres, empreintes et vérifications.
- `results-full.zip` : résultats originaux complets, copie du script exécuté, journal et sauvegardes de chaque année.

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python pipeline/benchmark_protocol_attribution.py \
  --output experiments/protocol_attribution_rerun
```

Les dépendances figurent dans `requirements-research.txt`. Sauvegarde Drive : `HackTheFork/deep_audit/2026-10-31/protocol`. Les exports de production ne sont pas modifiés.
