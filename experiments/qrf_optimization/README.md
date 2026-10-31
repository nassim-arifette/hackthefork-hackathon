# QRF : quantiles et paramètres, expérience Colab

Exécution du 31 octobre 2026. Six variantes fixées avant le calcul, plus une politique choisissant sur les trois années précédentes. Échauffement 2016–2018 ; évaluation sur les mêmes 192 cas département–année de 2019 à 2025. 20 000 scénarios, mêmes tirages et même modèle blé que le benchmark original.

| Modèle | Perte contrat €/t ↓ | Contrats tenus | Prix médian €/t | Manque moyen €/ha |
|---|---:|---:|---:|---:|
| qrf_dense | 208.48 | 64.1% | 1170.22 | 105.95 |
| qrf_sparse | 209.49 | 63.0% | 1158.57 | 108.54 |
| qrf_past_selected | 212.01 | 63.0% | 1170.22 | 110.07 |
| qrf_dense_flexible | 217.36 | 60.9% | 1120.65 | 114.89 |
| qrf_dense_all_leaf | 219.70 | 59.9% | 1106.88 | 118.13 |
| qrf_sparse_all_leaf | 222.02 | 58.9% | 1109.49 | 120.66 |
| qrf_dense_smooth | 227.73 | 58.9% | 1110.78 | 127.29 |

`qrf_sparse` reproduit la référence à 4,55 × 10⁻¹³ €/t près. `qrf_dense` interpole 101 quantiles de 0 à 1, contre trois quantiles et une extrapolation linéaire des queues pour la référence. Les variantes `all_leaf` conservent tous les exemples par feuille ; `smooth` et `flexible` changent aussi profondeur et taille minimale des feuilles.

Le gain de 0,5 % du candidat dense est descriptif. La politique sélectionnée uniquement sur le passé perd 1,2 % face à la référence. Le réglage automatique ne donne donc pas de progrès sur ce run.

Reproduction depuis la racine du repo, avec requirements-research.txt :

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python pipeline/benchmark_qrf_optimization.py \
  --reference experiments/colab_2026_10_31/colab_benchmark/predictions.csv \
  --output experiments/qrf_optimization_rerun
```

`results.json` contient paramètres, versions, empreintes des entrées et sources, audits et sélections. `manifest.json` lie les checkpoints à la configuration. `execution.json` ajoute l’empreinte du CSV de référence et les vérifications après téléchargement. `results-full.zip` contient toutes les sauvegardes par année, le journal et la copie du script exécuté. `predictions_with_warmup.csv` permet de recalculer la sélection passée.

Sauvegardes Drive : `HackTheFork/optimizations/2026-10-31/qrf`. Les fichiers de production restent inchangés.
