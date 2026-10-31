# Benchmark Colab terminé — 31 octobre 2026

Exécution `60304f3585c0c885`, code source vérifié au commit `54d9f666ebc9c64a8ac45944225337ca2401e0e6`. Les archives originales ont été récupérées depuis le dossier Drive de cette exécution. Les **56 étapes rendement et 50 étapes contrat direct** sont terminées.

Lire l'analyse et les tableaux dans [RESULTATS_COLAB.md](../../docs/RESULTATS_COLAB.md).

## Fichiers

| Fichier | Contenu |
|---|---|
| `input-snapshot.zip` | Archive exacte des sources, données et dépendances utilisées |
| `results-full.zip` | Archive originale complète : résultats, prédictions, journaux, progression et 106 points de reprise |
| `colab_benchmark/results.json` | Scores des sept modèles lentille et de la référence historique, versions et audit temporel |
| `colab_benchmark/predictions.csv` | 1 536 décisions : huit méthodes × 192 cas département–année |
| `colab_contract/results.json` | Scores des modèles directs, calibration et choix automatique |
| `colab_contract/predictions.csv` | 2 112 décisions : onze méthodes × les mêmes 192 cas |
| `*/annual_metrics.csv` | Synthèses annuelles recalculées depuis les prédictions complètes |
| `provenance.json` | Empreintes SHA-256, commit des entrées et contrôles de cohérence |

Les `results.json` et `predictions.csv` sont conservés à l'identique. Les CSV annuels et le manifeste de provenance sont des ajouts lors de l'import. Les points de reprise sont des résultats et erreurs de calibration ; ce ne sont pas les poids entraînés des modèles.

## Contrôles à l'import

- Correspondance de chaque fichier d'entrée avec le commit source.
- Correspondance des empreintes des données et scripts avec les rapports.
- Recalcul des scores économiques depuis les CSV ; absence de doublons méthode–année–département.
- Même cohorte de 192 cas 2019–2025 pour les 19 configurations.
- Signature des 106 points de reprise conforme aux deux manifestes.

Le champ original `source_commit: unknown` du rapport rendement vient de l'absence de `.git` dans Colab. Le commit a été retrouvé et vérifié séparément, sans modifier ce rapport. Le message de journal `fatal: not a git repository` était intercepté et n'a pas interrompu le benchmark ; l'affichage est corrigé dans les versions suivantes du notebook.

## Rejouer le calcul

Extraire `input-snapshot.zip` dans un nouveau dossier, installer `requirements-research.txt`, `tabpfn==9.0.0` et disposer d'un GPU CUDA avec accès aux poids TabPFN 3.5. Puis, depuis ce dossier :

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python pipeline/benchmark_models.py \
  --models trend linear lightgbm qrf catboost ensemble tabpfn \
  --device cuda --calibration rolling --simulation-quantiles raw \
  --output experiments/colab_benchmark

OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python pipeline/benchmark_contract.py \
  --models pooled linear lightgbm qrf tabpfn --device cuda \
  --reference experiments/colab_benchmark/predictions.csv \
  --output experiments/colab_contract
```

Les archives permettent de relire les résultats sans compte Prior Labs, sans GPU et sans relancer l'expérience. Pour une nouvelle exécution interactive avec sauvegarde Drive, utiliser le [notebook du dépôt](../../notebooks/benchmark_colab.ipynb).
