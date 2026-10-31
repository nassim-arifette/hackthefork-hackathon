# Vérification indépendante des résultats canoniques

Les contrôles passent pour les **36 modèles**, soit **212 112 lignes contractuelles** sur **1 964 cas culture–département–année** de 2016 à 2025. La période d’évaluation 2019–2025 contient **1 384 cas** ; 2016–2018 sert au démarrage temporel.

La tolérance numérique est **absolue : 10⁻⁹**, sans tolérance relative. Ce rapport ne revendique pas une identité des octets : l’ordre des lignes et les colonnes supplémentaires diffèrent. Les clés, catégories et verdicts sont comparés exactement.

| Référence actuelle du dépôt | Lignes comparées | Verdicts modifiés | Écart maximal du coefficient | Écart maximal toutes colonnes numériques |
| --- | ---: | ---: | ---: | ---: |
| M0 / trend | 5 892 | 0 | 5.12e-13 | 1.36e-12 |
| QRF saisonnier | 5 892 | 0 | 6.82e-13 | 1.36e-12 |

Les deux références retrouvent leurs 50 unités culture–année d’entraînement, leurs données économiques, leurs cohortes et leurs coûts agrégés à cette tolérance. La référence est `experiments/multilegumes_benchmark/predictions.csv.gz`, qui intègre la mise à jour économique PR3. Le coefficient indexé est sans unité ; les coefficients fixe et par tranches sont en €/t.

| Culture | Cas 2016–2025 | Cas évalués 2019–2025 | Départements distincts |
| --- | ---: | ---: | ---: |
| feverole | 699 | 491 | 76 |
| haricot | 108 | 78 | 14 |
| lentille | 274 | 192 | 35 |
| pois | 718 | 494 | 77 |
| pois_chiche | 165 | 129 | 23 |

Le recalcul indépendant utilise uniquement les CSV et les YAML archivés, sans appeler les fonctions économiques du benchmark : tonnes acceptées après tri, besoin de paiement face au blé, trois bases contractuelles, paiement, verdict incluant l’égalité, déficit, prix effectif, coût attendu par tonne et perte économique. Les moyennes et dispersions historiques sont reconstruites à partir des seuls rendements antérieurs. Aucun désaccord au-delà de la tolérance n’est trouvé. Les 540 agrégations culture–modèle–contrat (couverture, coûts pondérés par tonnes, moyennes annuelles et déficits) sont également recalculées indépendamment et concordent.

Le besoin de paiement du scénario central est : prix du blé × rendement du blé − charges du blé + charges de la légumineuse − aide − bénéfice de rotation. Les contrats rémunèrent les tonnes acceptées. Les coûts sont des ratios de sommes de paiements et de tonnes ; la rotation reste une hypothèse économique explicite.

Les 1 800 audits culture–année–modèle respectent strictement les coupures temporelles : entraînement, météo simulée et estimation de dépendance utilisent des années antérieures à l’année évaluée. Tous les bras et les trois contrats utilisent exactement les mêmes cas observés. Les taux de protection simulée enregistrés valent tous 80 %, soit 16 000 succès sur 20 000 scénarios. Ce contrôle porte sur les taux sauvegardés : les tableaux des 20 000 scénarios ne sont pas régénérés ici.

Les deux calculs canoniques sont repartis de zéro et ont le même profil NumPy effectif, y compris la désactivation SIMD prescrite. Les empreintes des trois parties ZIP, des fichiers de résultat et des entrées archivées sont vérifiées. Les anciens résultats issus d’un mélange de profils matériels ne sont pas utilisés.

Le JSON joint contient les empreintes, les écarts maximaux par variable, les comptages par culture et les métriques comparées par contrat. L’audit des politiques et de la sélection temporelle est présenté ci-dessous.

## Vérification des politiques finales

Les **614 496 décisions** passent le recalcul indépendant du paiement, du verdict, du déficit, du coût attendu et de la perte économique. Les corrections des quatre calibrages sont reconstruites à partir des trois années antérieures, puis les **420 choix de sélecteur** et leurs **17 640 scores candidats** sont vérifiés. Aucun résultat de l’année choisie n’entre dans la décision.

Les **4 440 lignes de métriques globales**, les **9 000 comparaisons appariées ponctuelles**, **20 comparaisons principales avec intervalles par années** et **16 sous-groupes utiles** sont recalculés et concordent à la tolérance absolue de 10⁻⁹. Les empreintes des sorties de l’analyse et de son entrée combinée concordent.

| Comparaison, 2019–2025 | Cas | Protection candidat / M0 | Coût candidat / M0 (€/t acceptée) | Écart de coût [IC95 % par années] |
| --- | ---: | ---: | ---: | ---: |
| Lentille fixe, sélecteur QRF | 192 | 80.21 % / 79.17 % | 1761.57 / 1890.82 | -129.25 [-254.77 ; 6.54] |
| Haricot fixe, CatBoost dense/cal95 | 78 | 80.77 % / 82.05 % | 1823.16 / 1851.90 | -28.74 [-61.94 ; -1.43] |
| Pois indexé, sélecteur complet | 494 | 83.81 % / 83.81 % | 457.69 / 468.85 | -11.16 [-28.88 ; 13.41] |
| Pois chiche indexé, sélecteur complet | 129 | 84.50 % / 84.50 % | 797.03 / 820.14 | -23.10 [-55.54 ; 20.83] |

Pour la lentille à prix fixe, le sélecteur QRF protège deux cas supplémentaires et coûte 6,84 % de moins que le sélecteur M0. Le sélecteur sur toute la grille atteint seulement 77,60 % et coûte 1 792,70 €/t : il ne fait pas mieux que le sélecteur QRF, à 80,21 % et 1 761,57 €/t.

Le haricot CatBoost dense/cal95 est un candidat choisi rétrospectivement dans la grille : son économie de 28,74 €/t accompagne un cas protégé de moins que M0/cal95 (63 contre 64 sur 78), et un déficit moyen plus élevé. Son score ne doit pas être attribué au sélecteur automatique.

Pour pois et pois chiche, les sélecteurs complets indexés atteignent respectivement 83,81 % et 84,50 %, identiques aux sélecteurs M0. Les économies observées de 2,38 % et 2,82 % ont des intervalles de coût traversant zéro. Le contrat indexé fixe un multiplicateur du prix du blé, pas un prix ferme en €/t.

Exemples descriptifs vérifiés : lentille, Centre-Val de Loire (42 cas, 80,95 % dans les deux stratégies, −95,31 €/t pour le sélecteur QRF) et Pays de la Loire (24 cas, 87,50 % dans les deux, −225,02 €/t) ; haricot, Centre-Val de Loire (30 cas, 90 % dans les deux, −50,80 €/t pour CatBoost dense/cal95). Les autres groupes, y compris les résultats défavorables, sont conservés dans le JSON. Ces sous-groupes ne constituent pas une validation indépendante de leur choix.
