# Données, preprocessing et optimisation économique : audit avancé

Le prix fixe minimal assurant une marge au moins égale au blé dans 80 % des scénarios reste l'objectif initial. L'évaluation porte sur les mêmes cas observés pour chaque candidat. Les comparaisons de contrats indexés ou par tranches restent séparées.

## Ce qui est évalué

- 36 configurations de modèles/variables/distributions, quatre calibrages admissibles, cible économique toujours **80 %**.
- M0 `trend` et le QRF saisonnier antérieur sont conservés comme références. Chaque concurrent est apparié à chacune de ces références sous le même calibrage ; les sélecteurs sont comparés à des sélecteurs restreints à M0 ou à l'ancien QRF. Le sélecteur supplémentaire `m0_extended` autorise aussi les variantes M0 de distribution/dépendance, pour vérifier si les améliorations du simulateur profitent également à la baseline.
- `raw/cal80/cal90/cal95` : coefficient brut ou correction additive positive estimée sur les trois années hors temps précédentes. Les nombres 90 et 95 désignent des quantiles de correction, pas une promesse de protection à 90 % ou 95 %.
- Sélection automatique des variables, réglages, familles et calibrages : parmi les configurations disponibles, choisir sur les trois années antérieures le coût le plus bas atteignant 80 % ; à défaut retenir la meilleure protection passée. Une configuration commune est choisie pour une culture et une forme de contrat, sans utiliser les résultats de l'année à prédire.
- Paiement €/t acceptée = somme des paiements / somme des rendements acceptés. Il exclut transport et tri ; chaque département–année représente ici un hectare, sans pondération par les surfaces nationales.
- La distribution simulée, les données statiques, les interactions et les réglages de chaque configuration sont détaillés dans `candidate_catalog.json` et le manifeste du benchmark. Les gains d'une configuration modifiant plusieurs éléments ne sont pas attribués à un seul élément.
- La météo de l'année test ne sert qu'au diagnostic de rendement après récolte. Le prix avant campagne rejoue les historiques antérieurs. Une carte de sol récente apporte une information structurelle rétrospective ; elle ne doit pas être présentée comme disponible à toutes les anciennes dates de décision.
- La fenêtre `since_2023` fournit une sensibilité à la date des cartes ; la source INRAE BDGSF/CLC2012 utilisée pour les sols a été publiée en 2022. Elle réutilise les décisions temporelles déjà produites et ne constitue pas une nouvelle période de sélection ni une preuve que toutes les versions des données étaient disponibles à leur date historique.
- Les intervalles rééchantillonnent des années entières avec les mêmes tirages pour chaque candidat. Ils décrivent la sensibilité aux années observées, pas la probabilité de réussite future.

## Algorithmes évalués et références

### fixed

| Culture | Politique | Cas | Marge ≥ blé | Paiement €/t acceptée | Déficit €/ha |
| --- | --- | --- | --- | --- | --- |
| feverole | qrf_seasonal/cal95 | 491 | 76.58% | 698.2 | 74.3 |
| feverole | selector/all_models | 491 | 69.04% | 683.2 | 84.7 |
| feverole | selector/m0_extended | 491 | 72.10% | 706.8 | 72.1 |
| feverole | selector/m0_only | 491 | 73.12% | 711.7 | 67.9 |
| feverole | selector/qrf_reference | 491 | 71.69% | 653.4 | 82.4 |
| feverole | trend/cal95 | 491 | 75.97% | 717.4 | 62.1 |
| haricot | qrf_seasonal/cal95 | 78 | 82.05% | 1 873.3 | 72.8 |
| haricot | selector/all_models | 78 | 70.51% | 1 730.2 | 97.8 |
| haricot | selector/m0_extended | 78 | 71.79% | 1 755.1 | 87.4 |
| haricot | selector/m0_only | 78 | 71.79% | 1 753.6 | 86.8 |
| haricot | selector/qrf_reference | 78 | 71.79% | 1 758.0 | 93.4 |
| haricot | trend/cal95 | 78 | 82.05% | 1 851.9 | 64.5 |
| lentille | qrf_seasonal/cal95 | 192 | 81.77% | 1 906.8 | 34.8 |
| lentille | selector/all_models | 192 | 77.60% | 1 792.7 | 44.6 |
| lentille | selector/m0_extended | 192 | 76.04% | 1 874.9 | 49.6 |
| lentille | selector/m0_only | 192 | 79.17% | 1 890.8 | 42.4 |
| lentille | selector/qrf_reference | 192 | 80.21% | 1 761.6 | 38.9 |
| lentille | trend/cal95 | 192 | 80.21% | 2 031.1 | 41.2 |
| pois | qrf_seasonal/cal95 | 494 | 72.47% | 532.3 | 71.1 |
| pois | selector/all_models | 494 | 69.23% | 515.6 | 115.0 |
| pois | selector/m0_extended | 494 | 71.26% | 533.3 | 102.8 |
| pois | selector/m0_only | 494 | 72.67% | 537.5 | 99.1 |
| pois | selector/qrf_reference | 494 | 71.26% | 526.6 | 84.4 |
| pois | trend/cal95 | 494 | 73.68% | 549.2 | 70.9 |
| pois_chiche | qrf_seasonal/cal95 | 129 | 71.32% | 967.0 | 72.4 |
| pois_chiche | selector/all_models | 129 | 68.99% | 921.8 | 88.0 |
| pois_chiche | selector/m0_extended | 129 | 68.99% | 947.5 | 78.3 |
| pois_chiche | selector/m0_only | 129 | 69.77% | 963.3 | 76.9 |
| pois_chiche | selector/qrf_reference | 129 | 68.99% | 920.1 | 83.8 |
| pois_chiche | trend/cal95 | 129 | 72.09% | 978.7 | 64.8 |

### indexed

| Culture | Politique | Cas | Marge ≥ blé | Paiement €/t acceptée | Déficit €/ha |
| --- | --- | --- | --- | --- | --- |
| feverole | qrf_seasonal/cal95 | 491 | 90.22% | 594.6 | 11.5 |
| feverole | selector/all_models | 491 | 79.02% | 536.4 | 33.7 |
| feverole | selector/m0_extended | 491 | 79.23% | 540.0 | 33.0 |
| feverole | selector/m0_only | 491 | 86.15% | 562.0 | 19.9 |
| feverole | selector/qrf_reference | 491 | 86.76% | 566.0 | 17.0 |
| feverole | trend/cal95 | 491 | 89.61% | 609.7 | 10.8 |
| haricot | qrf_seasonal/cal95 | 78 | 93.59% | 1 906.7 | 23.1 |
| haricot | selector/all_models | 78 | 79.49% | 1 506.1 | 60.2 |
| haricot | selector/m0_extended | 78 | 79.49% | 1 566.6 | 52.9 |
| haricot | selector/m0_only | 78 | 79.49% | 1 568.7 | 50.0 |
| haricot | selector/qrf_reference | 78 | 80.77% | 1 585.7 | 53.2 |
| haricot | trend/cal95 | 78 | 92.31% | 1 859.3 | 22.9 |
| lentille | qrf_seasonal/cal95 | 192 | 88.02% | 1 906.6 | 13.6 |
| lentille | selector/all_models | 192 | 78.12% | 1 798.1 | 35.7 |
| lentille | selector/m0_extended | 192 | 82.29% | 1 828.5 | 27.5 |
| lentille | selector/m0_only | 192 | 83.33% | 1 846.0 | 26.0 |
| lentille | selector/qrf_reference | 192 | 79.17% | 1 733.5 | 28.4 |
| lentille | trend/cal95 | 192 | 86.98% | 1 995.9 | 18.6 |
| pois | qrf_seasonal/cal95 | 494 | 88.87% | 471.1 | 11.6 |
| pois | selector/all_models | 494 | 83.81% | 457.7 | 18.4 |
| pois | selector/m0_extended | 494 | 79.55% | 457.7 | 31.4 |
| pois | selector/m0_only | 494 | 83.81% | 468.9 | 20.9 |
| pois | selector/qrf_reference | 494 | 80.57% | 451.8 | 27.1 |
| pois | trend/cal95 | 494 | 88.66% | 482.0 | 13.4 |
| pois_chiche | qrf_seasonal/cal95 | 129 | 93.02% | 888.9 | 8.2 |
| pois_chiche | selector/all_models | 129 | 84.50% | 797.0 | 25.0 |
| pois_chiche | selector/m0_extended | 129 | 85.27% | 821.3 | 22.1 |
| pois_chiche | selector/m0_only | 129 | 84.50% | 820.1 | 22.8 |
| pois_chiche | selector/qrf_reference | 129 | 84.50% | 824.4 | 25.9 |
| pois_chiche | trend/cal95 | 129 | 94.57% | 908.9 | 7.9 |

### tiers

| Culture | Politique | Cas | Marge ≥ blé | Paiement €/t acceptée | Déficit €/ha |
| --- | --- | --- | --- | --- | --- |
| feverole | qrf_seasonal/cal95 | 491 | 73.93% | 647.6 | 79.3 |
| feverole | selector/all_models | 491 | 67.01% | 635.4 | 97.8 |
| feverole | selector/m0_extended | 491 | 71.28% | 657.3 | 80.5 |
| feverole | selector/m0_only | 491 | 72.71% | 660.6 | 76.2 |
| feverole | selector/qrf_reference | 491 | 70.88% | 616.5 | 86.2 |
| feverole | trend/cal95 | 491 | 74.13% | 665.0 | 70.8 |
| haricot | qrf_seasonal/cal95 | 78 | 80.77% | 1 633.2 | 76.2 |
| haricot | selector/all_models | 78 | 67.95% | 1 422.8 | 97.3 |
| haricot | selector/m0_extended | 78 | 69.23% | 1 542.3 | 98.5 |
| haricot | selector/m0_only | 78 | 69.23% | 1 541.7 | 98.5 |
| haricot | selector/qrf_reference | 78 | 69.23% | 1 554.0 | 95.4 |
| haricot | trend/cal95 | 78 | 79.49% | 1 611.1 | 75.2 |
| lentille | qrf_seasonal/cal95 | 192 | 79.69% | 1 716.1 | 36.7 |
| lentille | selector/all_models | 192 | 75.00% | 1 595.4 | 49.3 |
| lentille | selector/m0_extended | 192 | 74.48% | 1 680.0 | 49.7 |
| lentille | selector/m0_only | 192 | 75.52% | 1 683.5 | 48.6 |
| lentille | selector/qrf_reference | 192 | 79.17% | 1 596.8 | 38.7 |
| lentille | trend/cal95 | 192 | 78.65% | 1 821.0 | 42.2 |
| pois | qrf_seasonal/cal95 | 494 | 71.66% | 508.3 | 81.0 |
| pois | selector/all_models | 494 | 69.43% | 494.0 | 114.2 |
| pois | selector/m0_extended | 494 | 71.05% | 506.8 | 102.7 |
| pois | selector/m0_only | 494 | 72.67% | 515.2 | 84.9 |
| pois | selector/qrf_reference | 494 | 71.26% | 505.1 | 88.8 |
| pois | trend/cal95 | 494 | 72.87% | 515.8 | 83.2 |
| pois_chiche | qrf_seasonal/cal95 | 129 | 68.99% | 901.5 | 83.5 |
| pois_chiche | selector/all_models | 129 | 67.44% | 851.9 | 92.4 |
| pois_chiche | selector/m0_extended | 129 | 67.44% | 866.5 | 85.9 |
| pois_chiche | selector/m0_only | 129 | 67.44% | 868.5 | 84.6 |
| pois_chiche | selector/qrf_reference | 129 | 68.22% | 860.8 | 90.1 |
| pois_chiche | trend/cal95 | 129 | 68.99% | 914.0 | 75.0 |

## Candidats retenus après comparaison : diagnostic rétrospectif

Ce tableau choisit après lecture des résultats. Ses scores ne sont pas ceux du sélecteur automatique et ne constituent pas un test indépendant de ce choix.

| Culture | Contrat | Candidat rétrospectif | Cas | Marge ≥ blé | Paiement €/t | Statut |
| --- | --- | --- | --- | --- | --- | --- |
| feverole | fixed | qrf_rpg_weather_dense/cal95 | 491 | 76.99% | 701.0 | aucun candidat à 80 % ; meilleure protection observée |
| feverole | indexed | trend_dense/raw | 491 | 80.45% | 501.7 | moins cher parmi candidats testés ≥80 % |
| feverole | tiers | qrf_leaf5_depth8/cal95 | 491 | 74.75% | 649.5 | aucun candidat à 80 % ; meilleure protection observée |
| haricot | fixed | cat_dense/cal95 | 78 | 80.77% | 1 823.2 | moins cher parmi candidats testés ≥80 % |
| haricot | indexed | cat_sparse/cal90 | 78 | 84.62% | 1 491.3 | moins cher parmi candidats testés ≥80 % |
| haricot | tiers | qrf_features05/cal95 | 78 | 80.77% | 1 613.4 | moins cher parmi candidats testés ≥80 % |
| lentille | fixed | qrf_seasonal/cal95 | 192 | 81.77% | 1 906.8 | moins cher parmi candidats testés ≥80 % |
| lentille | indexed | qrf_seasonal/cal90 | 192 | 84.90% | 1 754.5 | moins cher parmi candidats testés ≥80 % |
| lentille | tiers | qrf_combined_dense/cal95 | 192 | 80.73% | 1 735.5 | moins cher parmi candidats testés ≥80 % |
| pois | fixed | trend_dense/cal95 | 494 | 74.09% | 550.5 | aucun candidat à 80 % ; meilleure protection observée |
| pois | indexed | qrf_seasonal/cal90 | 494 | 80.16% | 439.5 | moins cher parmi candidats testés ≥80 % |
| pois | tiers | trend_dense/cal95 | 494 | 73.48% | 518.9 | aucun candidat à 80 % ; meilleure protection observée |
| pois_chiche | fixed | qrf_combined_dense/cal95 | 129 | 72.87% | 960.6 | aucun candidat à 80 % ; meilleure protection observée |
| pois_chiche | indexed | trend_joint_empirical/cal80 | 129 | 82.95% | 741.3 | moins cher parmi candidats testés ≥80 % |
| pois_chiche | tiers | cat_depth6/cal95 | 129 | 69.77% | 898.4 | aucun candidat à 80 % ; meilleure protection observée |

## Décomposition et sous-groupes

`ablation.csv` publie les transitions de variables, distributions et paramètres en brut et avec cal95, avec les cas sauvés et perdus. Les colonnes `parent` et `candidate` identifient exactement les deux configurations ; le catalogue précise toute autre différence.
`summary.csv.gz` et `subgroup_comparisons.csv.gz` incluent tous les groupes, favorables et défavorables : année, région, département, Île-de-France, historique, volatilité passée, ancienne/nouvelle cohorte. Les effectifs sont conservés. Aucun sous-groupe n'est créé après sélection d'un résultat favorable.

## Reproduction et traçabilité

- `global_summary.csv` : tous les candidats et sélecteurs, périodes complète et depuis 2023.
- `paired_baselines.csv` : écarts appariés contre M0 et ancien QRF, calibrages identiques, intervalles par années.
- `selection_decisions.csv` : décision retenue et dernières années utilisées ; `selection_candidates.csv.gz` : tous les candidats et leurs scores passés avant chaque choix.
- `policy_decisions.csv.gz` : décisions compactes, à joindre aux prédictions brutes par culture/contrat/année/département/modèle pour retrouver les données économiques complètes.
- `yield_diagnostics.csv` : diagnostic avec météo réalisée, séparé de l'objectif contractuel et non utilisé pour choisir les politiques. La perte quantile en t/ha, lorsqu'elle est fournie, sert à comparer les normalisations ; les pertes relatives ne sont pas directement comparables entre cibles normalisées différemment.
- `candidate_catalog.json` : configurations exécutées ; `manifest.json` : entrées, empreintes et paramètres d'analyse.
