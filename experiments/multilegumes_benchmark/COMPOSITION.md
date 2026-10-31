# Composition exacte après mise à jour économique

Ce dossier rassemble 300 ajustements culture–année–modèle : 180 résultats réutilisés à hypothèses strictement identiques et 120 recalculs complets après modification des charges. Aucun prix n'a été corrigé par une approximation sur l'ancien résultat.

| Culture | Charges €/ha | Origine |
| --- | ---: | --- |
| lentille | 500 | résultats identiques réutilisés |
| pois_chiche | 500 | résultats identiques réutilisés |
| haricot | 1000 | recalcul complet |
| pois | 450 | recalcul complet |
| feverole | 400 | résultats identiques réutilisés |

Le script vérifie l'identité des versions de dépendances, modèles, données météo, rendements, prix du blé, options de simulation et variables saisonnières. Seul `data/cultures.yaml` peut différer entre les deux exécutions. Pour les cultures réutilisées, les hypothèses numériques de chaque entraînement doivent être exactement celles de la configuration courante. Il vérifie aussi les cohortes, années d'apprentissage, besoins économiques et tonnes acceptées.

La version de production ajoute ensuite la fonction `series_passees` à `pipeline/model.py`. Une vérification AST contre les sources réellement exécutées prouve que tous les anciens nœuds sont identiques et que le benchmark ne référence pas ce helper. L'archive est vérifiée membre par membre contre le manifeste. Les empreintes exécutées restent intactes ; les empreintes courantes et la justification figurent dans `composition.checkout_compatibility`. Aucun résultat n'est recalculé pour cette addition.

- Source initiale : `experiments/multilegumes_pre_pr3`, signature `b9460e8a28b4043f1580f52a78954ed9b5ee36c27c1044697d5f48f10f0bff1e`.
- Recalcul : `experiments/multilegumes_pr3_recalculation`, signature `6e006243cc0b83cf9647ded3753d3bd30374886ff265d76a22735cc5f49d197e`.
- Source effective par culture et empreintes des fichiers : `manifest.json`.

Les fichiers `predictions.csv.gz` sont lus automatiquement si le CSV non compressé n'est pas présent. Les empreintes de provenance portent sur les octets CSV décompressés : compresser pour publication ne change pas l'identité du résultat.

Reproduire directement le résultat avec la configuration courante est possible en relançant les cinq cultures, sans assemblage :

```bash
python pipeline/benchmark_multilegumes.py \
  --seasonal-file data/meteo_saisonnier_cultures.csv \
  --samples 20000 --seed 42 --threads 1 \
  --output experiments/multilegumes_full_current
```
