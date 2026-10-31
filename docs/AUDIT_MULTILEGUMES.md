# Quels modèles et contrats retenir pour les cinq légumineuses ?

**Pour l'objectif initial, prix fixé avant campagne sur la lentille, le meilleur candidat testé est QRF avec des fenêtres météo propres à la culture et une calibration économique `cal95`.** Sur les mêmes 192 cas que M0, il atteint **81,77 %** de marges au moins égales au blé, contre **80,21 %** pour M0 soumis au même calibrage, avec un paiement moyen de **1 907 contre 2 031 €/t acceptée : −6,12 %**. Le déficit moyen passe de **41,18 à 34,80 €/ha**.

Les autres cultures ne justifient pas le même choix. M0 reste compétitif sur haricot et féverole ; l'indexation sur le prix du blé est le changement le plus utile pour pois et pois chiche. **Changer de modèle et changer de contrat sont deux décisions séparées.**

## Ce qui a effectivement été comparé

Le benchmark utilise les hypothèses de la PR #3 : charges haricot **1 000 €/ha**, pois **450 €/ha**, lentille et pois chiche **500 €/ha**, féverole **400 €/ha**, blé **700 €/ha**. Aide et effet de rotation restent respectivement **105 et 150 €/ha**. Les paiements portent sur les tonnes acceptées après le refus de 10 % ou 5 % fixé par culture.

- Six modèles : **M0 tendance**, M1 quantiles linéaires, QRF historique, QRF avec fenêtres propres à la culture, LightGBM et CatBoost avec ces mêmes fenêtres.
- Trois formes : prix fixe, multiplicateur du prix du blé fixé avant campagne, barème marginal par tranches. Les tranches de recherche ont des ratios `1 / 0,7 / 0,4` et des bornes fixées d'après le rendement net moyen passé ; elles diffèrent du barème de démonstration.
- Années test **2019–2025**, avec prédictions hors temps **2016–2018** pour amorcer les corrections et la sélection. Chaque entraînement, regroupement de séries, normalisation et calibration n'utilise que le passé.
- **20 000 scénarios par département–année–modèle**, mêmes tirages entre candidats, même année historique pour météo et prix du blé, même modèle blé et même cohorte par culture.
- **1 384 cas département–année** au total, sans mélanger les cinq cultures dans un unique score. Les tests portent sur des rendements historiques sous hypothèses économiques fixes.

La **vraie baseline M0** est la tendance des rendements relatifs avec quantiles de résidus, évaluée dans le même moteur économique. Les tableaux comparent également chaque candidat à **M0 avec la même calibration**, et le sélecteur complet à un sélecteur limité à M0. Une ancienne version de QRF ne sert jamais de baseline principale.

`cal80`, `cal90` et `cal95` désignent le quantile des erreurs de coefficient observées pendant les trois années précédentes. Le correctif est positif ou nul et s'ajoute au coefficient brut. **La cible du produit reste 80 %, même pour `cal95`.** Le coefficient brut est le minimum exact couvrant 80 % des scénarios ; le coefficient corrigé est un prix calibré visant la protection hors échantillon, avec ce minimum brut comme plancher. Les variantes qui peuvent baisser ce plancher sont conservées uniquement comme ablations `signed`, exclues de la sélection produit.

Les €/t ci-dessous sont **somme des règlements / somme des tonnes acceptées**, sur des hectares types de poids égal. Ils excluent collecte et tri. Ce sont des moyennes de benchmark, **pas un nouveau tarif départemental pour 2026**. La démonstration conserve son moteur M1 et son P* brut de **1 568 €/t acceptée départ ferme en Seine-et-Marne**.

## Prix fixe : répondre d'abord à la promesse initiale

Les candidats de cette section sont retenus **après comparaison du benchmark**, pour orienter le prototype. Leurs coefficients annuels ont tous été calculés avant l'année évaluée ; le choix final du candidat reste exploratoire.

| Culture | Candidat fixe à retenir parmi les essais | Cas tenus | Paiement €/t nette | M0 au même calibrage | Conclusion |
| --- | --- | ---: | ---: | --- | --- |
| Lentille | QRF fenêtres culture, `cal95` | **157/192 · 81,77 %** | **1 907** | 154/192 · 80,21 %, 2 031 €/t | Plus de cas tenus et −6,12 % de coût |
| Haricot sec | **M0, `cal95`** | **64/78 · 82,05 %** | **1 852** | Même politique | Le modèle simple reste le moins cher parmi ceux atteignant 80 % |
| Pois chiche | Aucun candidat n'atteint 80 % | Meilleur taux : 95/129 · 73,64 % | 979 pour M1 `cal95` | — | Étudier le contrat indexé |
| Pois protéagineux | Aucun candidat n'atteint 80 % | Meilleur taux : 364/494 · 73,68 % | 549 pour M0 `cal95` | — | Étudier le contrat indexé |
| Féverole | Aucun candidat n'atteint 80 % | Meilleur taux : 381/491 · 77,60 % | 699 pour QRF `cal95` | — | Étudier le contrat indexé |

Pour la lentille, QRF historique `cal95` tient également **157/192 cas**, à **1 915 €/t**. Les fenêtres propres à la culture réduisent encore le coût d'environ **9 €/t** ; l'essentiel du gain vient du couple distribution QRF et calibration de la décision économique. CatBoost a bien été testé dans les 300 unités : il ne remplace pas automatiquement ces candidats.

![Prix fixe : coût et protection](../experiments/multilegumes_policies/coverage_cost_fixed.svg)

## Indexation et tranches : des offres supplémentaires

Un contrat indexé fixe son **multiplicateur** avant campagne et utilise le prix du blé à la récolte pour le règlement. Il ne fixe donc pas un prix final en euros à la signature. Ces résultats ne sont pas présentés comme ceux du seul modèle de rendement.

| Culture | Candidat indexé | Cas tenus | Paiement €/t nette | Lecture face à M0 |
| --- | --- | ---: | ---: | --- |
| Lentille | QRF fenêtres culture, `cal90` | **163/192 · 84,90 %** | **1 755** | M0 `cal90` : 82,81 %, 1 858 €/t ; gain de protection et −5,55 % |
| Haricot sec | M1 linéaire, `cal80` | **63/78 · 80,77 %** | **1 404** | M0 `cal80` coûte moins, 1 287 €/t, mais ne tient que 73,08 % ; M0 `cal90` atteint 84,62 % à 1 497 €/t |
| Pois protéagineux | LightGBM fenêtres culture, `cal90` | **400/494 · 80,97 %** | **439** | M0 `cal90` : 83,20 %, 454 €/t ; −3,40 % avec une protection moins élevée, toujours ≥80 % |
| Pois chiche | **M0, `cal80`** | **106/129 · 82,17 %** | **753** | Candidat le moins cher parmi ceux atteignant 80 % |
| Féverole | **M0 brut** | **397/491 · 80,86 %** | **506** | Candidat le moins cher parmi ceux atteignant 80 % |

Sur lentille indexée, LightGBM `cal90` est encore un peu moins cher : **1 742 €/t, 157/192 cas (81,77 %)**. QRF avec fenêtres culture coûte **13 €/t** de plus et tient **six cas supplémentaires**. Ce choix explicite permet de discuter le compromis coût/protection avec l'acheteur.

Les tranches donnent aussi un candidat utile en lentille : **QRF historique `cal95`, 156/192 cas (81,25 %), 1 727 €/t**, contre M0 au même calibrage **78,65 %, 1 821 €/t**. En haricot, QRF fenêtres culture `cal95` atteint **63/78 cas (80,77 %), 1 633 €/t**. Aucun candidat à tranches testé ne franchit 80 % pour les trois autres cultures. Le choix entre fixe, indexé et tranches est fait après cette comparaison ; aucun sélecteur prospectif entre formes de contrat n'a été validé ici.

![Contrats indexés : coût et protection](../experiments/multilegumes_policies/coverage_cost_indexed.svg)

## Les gains ne viennent pas seulement des cas ajoutés

Le regroupement Agreste est recalculé sur le passé de chaque pli. La nouvelle cohorte lentille compte 192 cas, dont les **133 anciens cas** et 59 entrants. Pour la féverole, l'intersection est **444**, avec **47 entrants et 2 sortants** : les cas Gironde 2024 et 2025 changent de représentant. Les listes exactes figurent dans [le rapprochement des cohortes](../experiments/multilegumes_policies/cohort_reconciliation.csv).

Comparaison **lentille fixe, QRF fenêtres culture `cal95` contre M0 `cal95`**, sans réentraîner ni choisir les modèles selon ces groupes :

| Groupe | Cas | Protection QRF / M0 | Paiement QRF / M0, €/t nette |
| --- | ---: | --- | ---: |
| Ancienne cohorte | **133** | **81,20 % / 79,70 %** | **1 987 / 2 131** |
| Nouveaux cas | **59** | **83,05 % / 81,36 %** | **1 674 / 1 741** |
| Centre-Val de Loire | 42 | 80,95 % / 80,95 % | 1 954 / 2 047 |
| Pays de la Loire | 24 | 87,50 % / 87,50 % | 2 111 / 2 343 |
| Nouvelle-Aquitaine | 26 | 88,46 % / 88,46 % | 2 022 / 2 189 |
| Occitanie | 50 | 88,00 % / 86,00 % | 1 623 / 1 711 |
| Auvergne-Rhône-Alpes | 24 | 70,83 % / 66,67 % | 2 512 / 2 709 |
| Grand Est | 18 | 77,78 % / 77,78 % | 1 424 / 1 437 |
| Bourgogne-Franche-Comté | 8 | 50,00 % / 37,50 % | 2 170 / 2 341 |

Les économies sont visibles dans plusieurs bassins, mais la cible n'est pas atteinte partout. Les huit cas de Bourgogne-Franche-Comté restent affichés pour ne pas masquer ce point ; ils ne suffisent pas à établir une règle commerciale régionale.

Les groupes définis d'après le passé apportent une autre lecture : pour les **129 cas avec un coefficient de variation historique entre 20 et 40 %**, QRF tient **86,82 % contre 85,27 %**, à **2 107 contre 2 272 €/t**. Pour les **51 cas avec CV ≤20 %**, les deux modèles restent sous 80 % et QRF coûte **21 €/t de plus**. L'analyse complète conserve aussi les classes de 3–5, 6–9 et 10+ observations passées ; aucune classe perdante n'a été retirée.

## Île-de-France : deux cultures réellement testables

Pour les départements 77, 78, 91 et 95, les données fournissent **28 cas test pour le pois et 28 pour la féverole**, sur sept ans. Les politiques ci-dessous ont été entraînées et calibrées dans le benchmark national ; le tableau en extrait les cas franciliens.

| Culture et contrat | Candidat | Cas tenus | Paiement €/t nette | Comparateur |
| --- | --- | ---: | ---: | --- |
| Pois indexé | **QRF historique `cal90`** | **25/28 · 89,29 %** | **456** | M0 `cal90` : 23/28 · 82,14 %, 463 €/t |
| Pois indexé | LightGBM culture `cal90` | 23/28 · 82,14 % | 448 | M0 `cal90` : même protection, 463 €/t |
| Féverole indexée | **M0 brut** | **23/28 · 82,14 %** | **550** | Solution simple à faible coût |
| Féverole indexée | QRF historique `cal90` | 24/28 · 85,71 % | 599 | M0 `cal90` : 25/28 · 89,29 %, 615 €/t |

Le résultat pois est un exemple concret où QRF fait mieux que M0 dans le groupe correspondant au projet. Pour lentille, pois chiche et haricot, il n'existe pas de cohorte francilienne observée dans ce benchmark : les performances nationales **ne valident pas automatiquement le transfert** de rendement vers le site acheteur. Il faut conserver le statut d'hypothèse des rendements transférés et utiliser le pilote pour les mesurer.

## Sélection automatique : évaluée séparément

Le sélecteur choisit avant chaque année, par culture et forme de contrat, le moins cher des **24 candidats** satisfaisant 80 % sur les trois années passées. Si aucun n'y parvient, il prend la meilleure protection passée. C'est une sélection dans cet ensemble fini, pas un optimum global.

Il tient **397/494 cas de pois indexé (80,36 %)** à **449 €/t**, contre **83,81 % et 469 €/t** pour le sélecteur limité à M0. En pois chiche indexé, il tient **107/129 cas (82,95 %)** à **767 €/t**, contre **84,50 % et 820 €/t** pour le sélecteur M0.

En revanche, **aucun sélecteur automatique à prix fixe n'atteint 80 %** sur la période ; en lentille fixe il tient **77,08 %**. Cela motive le choix d'un candidat stable comme QRF culture `cal95` pour le prototype, plutôt que l'activation du changement automatique annuel de modèle. Les [décisions annuelles](../experiments/multilegumes_policies/selection_decisions.csv) permettent de voir chaque choix et les résultats passés qui l'ont déclenché.

Une seconde analyse donne la même masse à chaque année dans la calibration, au lieu de pondérer chaque département–année de la même façon. **Le résultat lentille fixe QRF culture `cal95` est inchangé** ; le candidat M0 pois chiche indexé `cal80` passe de **82,17 à 84,50 %**, pour un coût de **753 à 755 €/t**. Ce contrôle ne transforme pas les sélecteurs à prix fixe en politiques atteignant 80 %.

## Les années difficiles restent visibles

Le résultat global lentille fixe ne signifie pas que chacune des sept années a obtenu 80 %. Voici les résultats QRF culture `cal95` et M0 `cal95` sur les mêmes cas :

| Année | Cas | Protection QRF / M0 | Écart de paiement QRF − M0, €/t |
| --- | ---: | --- | ---: |
| 2019 | 28 | 75,00 % / 71,43 % | +25 |
| 2020 | 30 | 73,33 % / 73,33 % | −30 |
| 2021 | 30 | 53,33 % / 53,33 % | +156 |
| 2022 | 29 | 79,31 % / 72,41 % | +56 |
| 2023 | 27 | 100 % / 100 % | −247 |
| 2024 | 24 | 100 % / 100 % | −320 |
| 2025 | 24 | 100 % / 100 % | −398 |

Le gain global de coût de 124 €/t varie donc selon les années. Le rééchantillonnage des **années entières**, qui préserve la dépendance entre départements, donne un intervalle descriptif à 95 % de **−262 à +28 €/t** pour cet écart. L'intérêt constaté du candidat est réel dans ce benchmark ; cet intervalle ne constitue pas une probabilité de gain futur. Les 20 000 simulations restent des scénarios rejoués, pas 20 000 années d'information nouvelles.

## Reproduction et lien avec la démonstration

Le premier calcul Colab comporte 300 unités culture–année–modèle. Après la PR #3, **120 unités haricot/pois ont été entièrement recalculées**, avec les nouvelles charges. Les 180 autres ont été réutilisées après vérification des hypothèses, de toutes les empreintes communes et des versions. Aucun ancien prix n'a été ajusté par une règle approximative. Le [manifeste composite](../experiments/multilegumes_benchmark/manifest.json) et la [description de l'assemblage](../experiments/multilegumes_benchmark/COMPOSITION.md) conservent la provenance par culture.

```bash
python pipeline/merge_multilegumes_runs.py \
  --previous experiments/multilegumes_pre_pr3 \
  --replacement experiments/multilegumes_pr3_recalculation \
  --output experiments/multilegumes_benchmark

python pipeline/analyze_multilegumes.py \
  --input experiments/multilegumes_benchmark/predictions.csv.gz \
  --output experiments/multilegumes_policies

python pipeline/analyze_multilegumes.py \
  --input experiments/multilegumes_benchmark/predictions.csv.gz \
  --output experiments/multilegumes_policies_year_weighted \
  --calibration-weighting year --summary-only
```

- [Tableau global, toutes les politiques](../experiments/multilegumes_policies/global_summary.csv).
- [Comparaisons appariées à M0](../experiments/multilegumes_policies/paired_baselines.csv), incluant cas gagnés/perdus et intervalles par années.
- [Rapport détaillé et graphiques](../experiments/multilegumes_policies/REPORT.md).
- [Sensibilité à la pondération annuelle](../experiments/multilegumes_policies_year_weighted/summary.csv).
- [Tous les résumés de groupes](../experiments/multilegumes_policies/summary.csv.gz) et [toutes les comparaisons de sous-groupes](../experiments/multilegumes_policies/subgroup_comparisons.csv.gz) conservent les groupes gagnants et perdants.
- [Décisions ligne par ligne](../experiments/multilegumes_policies/policy_decisions.csv.gz) : les 182 688 décisions peuvent être jointes aux prédictions brutes pour reconstruire paiements et marges. La version complète redondante reste dans la sauvegarde Drive.
- [Optimisation des sites](../experiments/sites/README.md) : les coûts de collecte et de tri sont ajoutés au règlement producteur sur la bonne assiette brute/nette. La sélection spatiale d'un scénario à prix fixe ne devient pas automatiquement la sélection d'un contrat indexé ou à tranches.

La validation automatique comprend **97 tests passés**, dont les contrôles de cohorte identique, de calibration strictement passée, d'égalité des marges, de besoins signés, de coût pondéré par les tonnes et de provenance de l'assemblage après la PR #3. Une relecture indépendante a également recalculé les paiements, déficits et verdicts des **182 688 décisions**, sans différence.

## Sources agronomiques mobilisées

Les fenêtres de [crop_weather.py](../pipeline/crop_weather.py) sont fixées avant l'évaluation des scores. Elles traduisent les phases et sensibilités décrites dans les références suivantes ; elles restent des approximations calendaires, car les dates de semis et le type hiver/printemps ne sont pas observés pour chaque ligne départementale.

- [Terres Inovia — cycle de la lentille](https://www.terresinovia.fr/fr/informations-techniques/lentille/le-cycle-de-la-culture-de-la-lentille).
- [Terres Inovia — guide pois chiche 2026](https://www.terresinovia.fr/sites/default/files/2026-04/guide_culture_pois-chiche_2026_terresinovia.pdf).
- [Terres Inovia — sécheresse et températures élevées en féverole](https://www.terresinovia.fr/fr/informations-techniques/feverole-de-printemps/accidents-climatiques-de-la-feverole-secheresse-et).
- [Terres Inovia — implantation des pois et féveroles de printemps](https://www.terresinovia.fr/fr/actualites/reussir-limplantation-des-pois-et-feveroles-de-printemps).
- [Bio Bourgogne et chambres d'agriculture — itinéraire du haricot sec](https://www.produire-bio.fr/articles-pratiques/a-la-decouverte-du-phasealus-vulgaris/).

Les modèles de recherche restent des candidats à intégrer explicitement. Les corrections de calcul et d'interface peuvent être utilisées dans la démonstration immédiatement ; remplacer le moteur M1 par une politique de recherche nécessite de recalculer ses exports et d'indiquer le contrat retenu.
