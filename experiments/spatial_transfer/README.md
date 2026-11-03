# Transfert vers une région sans rendements lentille connus

Exécuté directement dans Colab le 31 octobre 2026. Les 7 régions productrices sont exclues tour à tour, pour chacune des 7 années 2019–2025. Les 2 modèles ont été évalués sur les mêmes 192 cas : 98 ajustements lentille et 7 ajustements blé.

Le niveau de rendement de la cible vient de la moyenne des 4 départements d’entraînement les plus proches en climat historique standardisé. Ni les rendements lentille de la cible ni ceux de sa région ne servent à l’apprentissage ou au choix des donneurs. Seul le filtre anti-doublon consulte les séries passées masquées pour écarter des mesures partagées de l’autre côté de la séparation. Le blé et la météo passés de la cible restent disponibles, comme pour le problème francilien.

Les deux modèles partagent donneurs, niveau transféré, modèle blé linéaire, quantiles bruts et 20 000 tirages. Ce test évalue une stratégie de transfert par analogues climatiques ; il ne reproduit pas exactement le proxy actuel à voisins fixes de l’application. Il ne constitue pas une validation directe en Île-de-France.

| Modèle | Perte contrat €/t ↓ | Contrats tenus | Prix médian €/t | Manque €/ha |
|---|---:|---:|---:|---:|
| local_history_qrf | 209.49 | 63.0% | 1158.57 | 108.54 |
| local_history_trend | 243.79 | 66.1% | 1253.95 | 116.84 |
| transfer_qrf | 285.28 | 49.0% | 1053.78 | 158.16 |
| transfer_trend | 291.77 | 58.3% | 1192.91 | 144.45 |

`local_history_*` utilise les rendements passés de la cible et reprend le benchmark initial ; `transfer_*` exclut toute sa région. Les prix sont départ ferme. La perte et le manque à l’hectare donnent un poids égal aux années.

| Région exclue | Cas | Perte M0 | Perte QRF | Tenus M0 | Tenus QRF |
|---|---:|---:|---:|---:|---:|
| 24 - Centre-Val de Loire | 42 | 206.39 | 186.95 | 76.2% | 76.2% |
| 27 - Bourgogne-Franche-Comté | 8 | 858.30 | 890.95 | 25.0% | 12.5% |
| 44 - Grand Est | 18 | 182.71 | 143.23 | 83.3% | 83.3% |
| 52 - Pays de la Loire | 24 | 208.86 | 185.79 | 75.0% | 58.3% |
| 75 - Nouvelle Aquitaine | 26 | 274.14 | 221.96 | 46.2% | 46.2% |
| 76 - Occitanie | 50 | 238.17 | 276.25 | 50.0% | 28.0% |
| 84 - Auvergne-Rhône-Alpes | 24 | 592.88 | 602.40 | 33.3% | 25.0% |

Les groupes définis par la volatilité ou le niveau du rendement lentille cible ne seraient pas disponibles dans ce scénario de transfert : ils ne pourraient servir qu’à un diagnostic rétrospectif. La région et son climat historique restent connus avant la campagne.

## Pourquoi le transfert échoue dans certains groupes

Le diagnostic après calcul compare le niveau transféré aux rendements que le test avait masqués. En médiane, le proxy vaut **1,63 fois** le niveau historique local en Bourgogne-Franche-Comté et **1,76 fois** en Auvergne-Rhône-Alpes. Les récoltes des années test représentent respectivement **45 % et 43 %** de ce niveau transféré : les donneurs climatiques conduisent à une hypothèse de productivité trop élevée. En Occitanie, le proxy vaut **1,24 fois** le niveau local et les récoltes test représentent **62 %** du proxy. Cela contribue à des prix insuffisants.

À l’inverse, le proxy Grand Est ne représente que **64 %** du niveau historique local. Les prix y sont élevés et les deux modèles tiennent 83,3 % des contrats. Le gain de perte QRF dans cette région ne signifie pas un prix médian plus bas : il est de 1 584 €/t contre 1 541 €/t pour M0. Dans le Centre, QRF réduit le prix médian de 1 348 à 1 141 €/t avec le même taux tenu, mais ce taux reste à 76,2 %.

Ces ratios sont des médianes par cas, calculées après téléchargement avec [`derive_level_diagnostics.py`](derive_level_diagnostics.py). Ils décrivent les erreurs de transfert ; ils n’ont servi ni à choisir les donneurs ni à entraîner le modèle. Les fichiers `level_diagnostics.csv` et `regional_level_diagnostics.csv` permettent de reproduire ce constat. Les résultats suggèrent de mieux estimer le niveau absolu de la lentille avant de chercher seulement un meilleur modèle de ses fluctuations.

Reproduction depuis la racine du repo, avec requirements-research.txt :

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python pipeline/benchmark_spatial_transfer.py \
  --output experiments/spatial_transfer_rerun
```

`results.json` contient les paramètres, versions, empreintes et 49 audits détaillés (régions/départements d’apprentissage, donneurs, distance climatique, niveau transféré). `results-full.zip` conserve tous les points de reprise et le script exécuté. Trois tests couvrent l’exclusion des années futures, l’absence de niveau lentille cible et l’exclusion des séries dupliquées.
