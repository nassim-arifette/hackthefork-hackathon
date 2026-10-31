# Benchmark commun des cinq légumineuses

Les résultats de ce dossier incorporent les budgets de la **PR #3** : haricot 1 000 €/ha et pois 450 €/ha. Les 300 configurations finales proviennent de 180 configurations réutilisées après contrôle strict des entrées et de 120 configurations recalculées dans Colab pour les deux cultures modifiées. `manifest.json` conserve cette provenance par culture. Les conclusions sont dans [AUDIT_MULTILEGUMES.md](../../docs/AUDIT_MULTILEGUMES.md).

Les CSV détaillés sont versionnés en `.csv.gz` ; pandas les lit directement. Les commandes de reproduction doivent écrire dans un nouveau dossier, afin de conserver les résultats de référence. Le [notebook Colab](../../notebooks/multilegumes_colab.ipynb) réexécute les 300 configurations avec les hypothèses actuelles et sauvegarde les checkpoints sur Drive.

Le script [`benchmark_multilegumes.py`](../../pipeline/benchmark_multilegumes.py)
produit les prévisions brutes nécessaires à la calibration économique séparée.
Il compare M0 (tendance), M1 (quantiles linéaires), QRF avec les six variables
météo historiques, puis QRF, LightGBM et CatBoost avec les cinq variables
saisonnières propres à chaque culture.

```bash
python pipeline/benchmark_multilegumes.py \
  --seasonal-file data/meteo_saisonnier_cultures.csv \
  --output experiments/multilegumes_reproduced \
  --samples 20000 --threads 1
```

## Découpage et comparaison

- Prédictions glissantes 2016–2025 ; 2016–2018 servent à initialiser les
  corrections de prix, 2019–2025 constituent la période rapportée.
- Pour chaque année, groupes Agreste, représentants, niveaux moyens,
  normalisation météo et modèles sont reconstruits avec les seules années
  antérieures. Une série doit disposer de trois mesures passées.
- Le blé est le même modèle linéaire à six variables pour tous les candidats,
  appris sur les observations utilisables des 87 départements météo disponibles.
- Les six modèles et les trois contrats partagent exactement les mêmes cas à
  l'intérieur d'une culture. Les cohortes des différentes cultures restent
  distinctes ; on ne les réduit pas à leur intersection géographique.
- Les mêmes tirages aléatoires sont utilisés pour tous les modèles, cultures et
  formes contractuelles d'un département et d'une année. Météo et prix du blé
  proviennent de la même année passée. Les rangs résiduels culture/blé sont
  indépendants dans ce contrôle.

| Culture | Ancienne cohorte | Nouvelle cohorte | Cas communs |
|---|---:|---:|---:|
| Lentille | 133 | 192 | 133 |
| Pois chiche | 100 | 129 | 100 |
| Haricot sec | 71 | 78 | 71 |
| Pois protéagineux | 493 | 494 | 493 |
| Féverole | 446 | 491 | 444 |

Pour la féverole, les anciens cas Gironde 33 de 2024 et 2025 ne sont pas dans
la nouvelle cohorte : les groupes reconstruits sur leur passé retiennent Landes
40 comme représentant. `cohorts.json` conserve les listes exactes des entrées et
sorties. Les drapeaux de doublon calculés sur toute la période ne servent qu'à
ce diagnostic historique, jamais à l'apprentissage moderne.

## Décision économique

Les charges, aides, rotation et refus au tri viennent du scénario v4 dans les
deux fichiers YAML. Les rendements et prix historiques sont rejoués sous ces
hypothèses économiques fixes. Le rendement payé est le rendement brut multiplié
une seule fois par la fraction acceptée.

Pour chaque scénario, le besoin de règlement est :

`besoin = prix_blé × rendement_blé − charges_blé + charges_culture − aide − rotation`.

Ce besoin reste signé. Le coefficient du contrat est le quantile empirique 80 %
de `besoin / base`, borné commercialement à zéro. Les égalités comptent comme des
contrats tenus. La base vaut :

- prix fixe : tonnes acceptées ;
- indexé : tonnes acceptées × prix du blé à la récolte ; le multiplicateur est
  fixé avant campagne, son prix en euros ne l'est pas ;
- tranches : tonnes acceptées pondérées par des prix marginaux proportionnels
  à `1 / 0,7 / 0,4`, avec bornes à `0,7 / 1,4` fois le rendement accepté moyen
  local passé. Ces ratios sont des paramètres de benchmark préspecifiés,
  différents du barème de démonstration lentille.

Les distributions simulées utilisent uniquement Q10/Q50/Q90 bruts avec la même
interpolation et les mêmes queues pour tous les candidats. Aucun intervalle CQR
élargi n'est réutilisé comme distribution. La calibration économique ultérieure
travaille sur les coefficients hors échantillon et leurs seuils signés.

## Coûts et fichiers

Le coût attendu par tonne est le rapport `E[paiement] / E[tonnes acceptées]`.
Pour les tableaux annuels, on additionne d'abord les règlements et les tonnes des
départements, puis on calcule ce rapport. Les années ont ensuite le même poids.
Les colonnes `*_pooled` conservent séparément le rapport sur toute la période.
Chaque observation représente ici un hectare type ; aucune surface effectivement
engagée n'est inventée.

- `predictions.csv` : coefficients, seuils signés, bases de paiement, rendements
  acceptés, coûts prévisionnels et réalisés, déficits et verdicts par cas.
- `summary.json` / `summary.csv` : résultats bruts par culture, modèle et contrat.
- `audit.json` : années, représentants, effectifs, variables et hypothèses de
  chaque entraînement.
- `manifest.json` : empreintes des sources, données, versions et paramètres.
- `checkpoints/` : une sauvegarde par culture–année–modèle, soit 300 unités ;
  la reprise refuse des sources, données ou options incompatibles.
- `progress.json` : progression lisible par le lanceur Colab.

La couverture brute des rendements utilise la météo réalisée de l'année test :
c'est un diagnostic distinct de la protection du contrat avant campagne. Les
scores portent sur les départements disposant d'un historique de la culture ;
ils ne constituent pas un test de transfert vers les départements sans historique.
