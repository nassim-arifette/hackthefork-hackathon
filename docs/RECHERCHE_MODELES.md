# Modèle de contrat : recherche et expériences du 31 octobre 2026

## Décision

**Le benchmark Colab terminé confirme la forêt quantile comme référence Monte-Carlo à quantiles bruts : perte contrat de 209,5 €/t, contre 285,3 €/t pour TabPFN 3.5.** Elle tient toutefois seulement 63,0 % des contrats historiques : gagner le classement ne valide pas encore la protection recherchée à 80 %. CatBoost et TabPFN ont désormais été évalués ; aucun ne justifie un remplacement. Le modèle direct QRF calibré atteint 82,3 % au total mais tombe à 54,2 % en 2025 : il reste un concurrent de recherche.

Les [résultats Colab complets](RESULTATS_COLAB.md) présentent les 19 configurations, les métriques recalculées par année et les fichiers originaux. Les contrôles CPU antérieurs restent ci-dessous, en distinguant les quantiles bruts des quantiles élargis. L'objectif suivant est d'améliorer la distribution simulée et sa dépendance entre cultures, puis de comparer le contrat au même protocole.

Le classement porte sur le contrat, pas seulement sur la précision du rendement. La version actuelle de l'application conserve ses résultats ; cette branche fournit les modèles, comparaisons, tests et commandes nécessaires pour choisir son successeur.

## La bonne cible

Pour chaque département et scénario, en t/ha :

```
marge_L = P × Y_L − C_L + aide + bonus_rotation
marge_B = prix_ble × Y_B − C_B
R = (prix_ble × Y_B − C_B + C_L − aide − bonus_rotation) / Y_L
P* = Q80(R)
```

Une égalité de marge est gagnante. P* est départ ferme ; le transport appartient au calcul du prix rendu au site. Le bonus de rotation reste à zéro dans les hypothèses actuelles.

Le chemin Monte-Carlo conserve **20 000 scénarios**, une même année historique pour la météo des deux cultures et le prix du blé, et la tendance projetée à l'année de décision. Les scénarios 2026 utilisent exclusivement 2010–2025. Le quantile empirique utilise `inverted_cdf` : c'est le plus petit seuil qui couvre au moins 80 % des scénarios, égalités comprises.

Pour départager les modèles, on mesure la pinball loss du **prix d'équilibre réalisé**, au quantile 0,8 : sous-estimer R de 100 €/t coûte 80 points ; le surestimer de 100 €/t coûte 20 points. On affiche également les contrats tenus et le manque à gagner à l'hectare. Un prix très élevé ne suffit donc pas à gagner le benchmark.

## Ce qui change dans le benchmark

- Les regroupements de séries Agreste identiques sont réestimés sur le passé disponible. Les indicateurs `doublon` calculés sur 2010–2025 ne pilotent plus l'entraînement des anciens millésimes.
- Les niveaux de rendement et la normalisation météo sont ajustés sur les données d'entraînement de chaque modèle.
- Un premier protocole `split` fige réellement le modèle avant les trois années de calibration. Il mesure notamment le coût d'un modèle entraîné trois ans en arrière.
- Le protocole `rolling` produit des prévisions hors échantillon pour chacune des trois dernières années, puis ajuste le modèle final sur tout le passé. C'est une calibration temporelle empirique, pas la garantie mathématique de split CQR.
- Les résultats sont détaillés par année. Les scores globaux donnent le même poids à chaque année ; le pourcentage « contrats tenus » compte aussi les cas département × année. Les intervalles de rééchantillonnage portent sur les années.
- Le concurrent `direct_*` apprend Q80(R) à partir de variables connues avant la campagne : niveaux historiques, variabilité, derniers rendements et dernier prix du blé. Il ne reçoit aucune météo réalisée de l'année à prédire.

Les nouveaux modèles sont comparés sur **192 cas communs de 2019 à 2025**. Ce n'est pas la population des **133 cas** publiée dans le README ; les pourcentages ne constituent donc pas une comparaison directe avec les anciens 86 %. Les années ayant déjà servi à explorer le projet, ce benchmark est une comparaison de recherche reproductible.

## Pourquoi ces modèles : articles et documentation

1. **Forêts quantiles** — [Meinshausen, JMLR 2006](https://jmlr.org/papers/v7/meinshausen06a.html) estime une distribution conditionnelle à partir des observations des feuilles. Candidat adapté au petit panel et aux relations météo non linéaires. Implémentation : [quantile-forest](https://zillow.github.io/quantile-forest/).
2. **Calibration des quantiles** — [Romano, Patterson et Candès, NeurIPS 2019](https://papers.neurips.cc/paper_files/paper/2019/hash/5103c3584b063c431bd1268e9b5e76fb-Abstract.html) fonde CQR. Dans le code actuel, la normalisation inclut les années de calibration et le modèle est réajusté après leur utilisation : ce n'est pas ce protocole standard.
3. **Dépendance et dérive temporelle** — [Barber et al., 2023](https://arxiv.org/abs/2202.13415) explique pourquoi la couverture conformal standard ne se transpose pas automatiquement à des données dépendantes ou dont la distribution change. Le choix ici est une calibration glissante évaluée sur la décision économique ; ce n'est pas une implémentation du théorème de cet article.
4. **TabPFN** — [Hollmann et al., Nature 2025](https://www.nature.com/articles/s41586-024-08328-6) montre l'intérêt d'un modèle préentraîné pour les petits jeux tabulaires. [TabPFN 3.5, rapport du 15 septembre 2026](https://priorlabs.ai/technical-reports/tabpfn-3-5) et sa [documentation de régression](https://docs.priorlabs.ai/capabilities/regression) motivent le challenger actuel : quantiles issus d'une distribution prédictive, sans entraîner un grand réseau de zéro. Ses résultats publiés sont une raison de le tester, pas un score acquis sur la lentille.
5. **CatBoost MultiQuantile** — [documentation officielle](https://catboost.ai/docs/en/concepts/loss-functions-regression). L'exécution locale était bloquée par l'absence d'accès à `/proc/self/statm` ; le run Colab est terminé. CatBoost obtient la plus faible valeur de la colonne `pinball` (calculée sur les bornes élargies de rendement), mais une perte contrat de 256,3 €/t, supérieure à celle du QRF.
6. **Agronomie** — [bilan lentille 2025, Terres Inovia](https://www.terresinovia.fr/fr/actualites/lentille-bilan-de-campagne-national-2025) : différences régionales et effet des chaleurs sur les semis tardifs. Prochaine amélioration des entrées : fenêtres phénologiques, séquences sèches et excès d'eau, plutôt qu'un seul cumul mars–juillet. Le code actuel utilise de la pluie avril–juin, pas un vrai bilan pluie–évapotranspiration malgré la description de `MODELE.md`.

## Résultats et choix pratique

Les tableaux ci-dessous proviennent des fichiers de résultats. Les prix médians sont ceux des contrats historiques, sauf dans la section explicitement consacrée aux prévisions 2026.

### Run Colab terminé : quantiles bruts, mêmes 192 cas

Le run `experiments/colab_2026_10_31` comprend les deux benchmarks terminés, leurs prédictions et les archives d'entrée et de sortie. La comparaison complète et les définitions des métriques figurent dans [RESULTATS_COLAB.md](RESULTATS_COLAB.md).

| Configuration | Score contrat ↓ €/t | Contrats tenus | Prix médian €/t | Manque moyen €/ha |
|---|---:|---:|---:|---:|
| QRF Monte-Carlo | 209,5 | 63,0 % | 1 159 | 108,5 |
| CatBoost Monte-Carlo | 256,3 | 55,7 % | 1 020 | 160,3 |
| TabPFN Monte-Carlo | 285,3 | 49,5 % | 975 | 189,6 |
| QRF direct | 280,9 | 78,1 % | 1 511 | 58,7 |
| TabPFN direct | 281,0 | 71,4 % | 1 477 | 75,0 |
| QRF direct calibré | 316,5 | 82,3 % | 1 744 | 39,1 |
| TabPFN direct calibré | 335,0 | 79,7 % | 1 719 | 45,5 |

Les 80 % des scénarios sont atteints par construction dans le Monte-Carlo. Le taux historique est une vérification distincte. La colonne `coverage` des JSON mesure l'intervalle de rendement : ses 80,1 % pour QRF ne sont pas les 63,0 % de contrats tenus. QRF reste la référence de recherche, sans promotion automatique vers l'application.

### Contrôle CPU antérieur après séparation distribution / intervalle

Run `experiments/model_benchmark_raw`, calibration glissante, apprentissage final sur tout le passé, 20 000 scénarios, mêmes 192 cas et mêmes hypothèses économiques que le contrôle historique :

| Modèle | Score contrat ↓ | Contrats tenus | Prix médian €/t | Manque moyen €/ha |
|---|---:|---:|---:|---:|
| Forêt quantile | 209,5 | 63,0 % | 1 159 | 108,5 |
| LightGBM | 235,4 | 58,3 % | 1 048 | 142,6 |
| Linéaire | 264,8 | 67,7 % | 1 370 | 113,2 |

La forêt quantile gagne sur la perte du prix d'équilibre ; la régression linéaire protège davantage en proposant un prix plus élevé. Cette expérience confirme que corriger un intervalle de rendement ne suffit pas à calibrer la distribution du prix. Le run Colab a repris cette formulation pour tous les candidats. Ce tableau conserve les chiffres du contrôle CPU ; le tableau Colab utilise ses propres sorties. Les colonnes `pinball`, `coverage` et `width` des JSON de recherche conservent leur définition historique sur les bornes élargies ; le classement ci-dessus utilise uniquement les métriques économiques.

### Contrôle historique : rendements avec quantiles élargis

| Modèle | Score contrat ↓ (€/t) | Contrats tenus | Prix médian proposé (€/t) | Manque à gagner moyen (€/ha) |
|---|---:|---:|---:|---:|
| Régression linéaire | 279.4 | 75.0% | 1807 | 63.7 |
| LightGBM | 194.6 | 72.9% | 1354 | 69.1 |
| Forêt quantile | 198.6 | 75.5% | 1483 | 54.7 |
| Ensemble | 218.7 | 74.5% | 1474 | 67.4 |

LightGBM réduit le score contrat de **30.3%** face à la régression linéaire de ce même protocole. La forêt quantile est proche en score, tient davantage de contrats et réduit davantage le manque à gagner moyen. Les trois modèles atteignent 80 % dans leurs simulations par construction ; le taux historique réalisé est un contrôle distinct.

### Contrôle CPU antérieur : modèle direct du prix d’équilibre

| Modèle | Score contrat ↓ (€/t) | Contrats tenus | Prix médian (€/t) |
|---|---:|---:|---:|
| direct_lightgbm | 261.0 | 65.6% | 1158 |
| direct_qrf | 280.9 | 78.1% | 1511 |
| direct_qrf_cal | 316.5 | 82.3% | 1744 |

**Résultat de sélection : ne pas promouvoir la calibration directe sur le seul 82,3 %.** Le CSV Colab confirme qu'elle ne tient plus que 54,2 % des contrats en 2025, contre 100 % pour le QRF direct brut, tout en réduisant la perte de cette année : le score et la contrainte de protection doivent être examinés ensemble. Dans le contrôle de projection 2026 déjà effectué, elle multiplie le prix brut par environ 0,54 après les dernières bonnes années. Ce mécanisme fait tomber le prix Seine-et-Marne à environ 608 €/t. Le modèle direct reste un concurrent, pas le remplacement retenu. La calibration supplémentaire du prix Monte-Carlo détériore également le score dans l'expérience CPU ; elle est écartée.

### Prévisions 2026, départ ferme, 20 000 scénarios

| Modèle Monte-Carlo | Seine-et-Marne | Yvelines | Essonne | Val-d’Oise |
|---|---:|---:|---:|---:|
| linear | 1426 €/t | 1368 €/t | 1343 €/t | 1431 €/t |
| lightgbm | 1295 €/t | 1266 €/t | 1225 €/t | 1332 €/t |
| qrf | 1097 €/t | 1109 €/t | 1063 €/t | 1142 €/t |

Ces prix ne sont pas les prix médians historiques du tableau précédent. Ils sont calculés pour la campagne 2026 avec les données 2010–2025. Les rendements lentille franciliens sont transférés depuis les départements 10, 89, 28 et 45 ; le département 51, doublon de série, n’est plus compté une seconde fois. Le changement par rapport aux 1 622 €/t combine le modèle, sa calibration, le centrage météo local et cette correction du transfert.

**Vérification actuelle :** 35 tests passent, dont perturbation des données futures, séparation calibration/ajustement, normalisation sans fuite, quantile empirique minimal, égalité de marge et reprise des benchmarks. L'exécution Colab de CatBoost et TabPFN est désormais terminée ; ses résultats sont archivés séparément et n'ont pas modifié ces prévisions 2026.

## Exécution CPU

```bash
python -m venv .venv-research
source .venv-research/bin/activate
pip install -r requirements-research.txt
python -m pytest -q
OMP_NUM_THREADS=1 python pipeline/benchmark_models.py --calibration rolling --output experiments/model_benchmark_rolling
OMP_NUM_THREADS=1 python pipeline/benchmark_contract.py
OMP_NUM_THREADS=1 python pipeline/forecast_research.py
```

`experiments/model_benchmark` conserve aussi le protocole split. `price_calibration_warmup` contient les décisions 2016–2018 pour initialiser une calibration du prix ; `price_calibration` contient cette expérience supplémentaire. Les CSV contiennent toutes les décisions, les JSON les agrégats, versions, paramètres et traces des découpages pour les benchmarks principaux.

## Colab : expériences terminées et procédure de reprise

[Google Colab CLI officiel](https://github.com/googlecolab/google-colab-cli), annoncé par [Google en juin 2026](https://developers.googleblog.com/introducing-the-google-colab-cli/).

Ouvrir [le notebook Colab](https://colab.research.google.com/github/nassim-arifette/hackthefork-hackathon/blob/research/probabilistic-benchmark/notebooks/benchmark_colab.ipynb), sélectionner un GPU T4 et exécuter les cellules. La première demande l'autorisation Drive et la clé dans un champ masqué, sauf si le secret Colab `TABPFN_TOKEN` existe déjà.

Deux barres affichent l'avancement par modèle et année (56 étapes rendement/baseline, puis 50 étapes de contrat direct). La sauvegarde s'effectue directement dans `Mon Drive/HackTheFork/benchmarks/<empreinte des sources>/`, après chaque étape. Elle comprend prédictions, erreurs de calibration nécessaires à la reprise, paramètres, journaux et résultats finaux. Une interruption pendant un entraînement ne perd que cette étape. Relancer le notebook reprend les étapes terminées sans réentraînement. Les tests simulent une coupure et vérifient l'identité des prédictions et de la calibration avec une exécution complète.

Les sources sont conservées dans Drive ; les récupérer à nouveau demande `NOUVELLE_VERSION = True`. Une modification de code, données, options ou versions de bibliothèques ne réutilise pas silencieusement des checkpoints incompatibles. Les archives d'entrée sont déterministes pour retrouver le même dossier après un redémarrage. Les clés ne figurent ni dans les archives ni dans les checkpoints.

Depuis une machine avec le CLI et une session Google connectée, **après avoir connecté Drive depuis le notebook sur le même runtime** :

```bash
pip install google-colab-cli
python scripts/package_benchmark.py
colab new -s hackthefork --gpu T4
colab upload -s hackthefork benchmark-input.zip /content/benchmark-input.zip
# Configurer TABPFN_TOKEN dans les secrets du notebook/runtime.
colab exec -s hackthefork -f scripts/colab_benchmark.py
colab download -s hackthefork /content/benchmark-results.zip ./benchmark-results.zip
colab stop -s hackthefork
```

Le script lance les mêmes modèles CPU, CatBoost sur les rendements lentille, puis TabPFN 3.5 sur les rendements lentille et le prix direct, avec les mêmes années et métriques. Après revue de la branche Youssef, le run Colab a utilisé `--simulation-quantiles raw` : les scénarios utilisent les quantiles de distribution, séparés des bornes conformelles. Les contrôles CPU `raw` et `expanded` restent identifiés séparément ci-dessus ; les nouveaux scores Colab utilisent tous `raw`, sans mélanger les classements. Le paquet `tabpfn==9.0.0` et la famille `ModelVersion.V3_5` sont explicitement sélectionnés. La [configuration officielle des poids](https://docs.priorlabs.ai/models/accessing-model-weights) demande l'acceptation de la licence et un secret `TABPFN_TOKEN`. L'authentification Google s'effectue dans le flux du CLI ; aucun mot de passe n'est nécessaire dans le code. Les poids et données restent sur le runtime ; l'API de prédiction hébergée n'est pas utilisée.

Le run est terminé : **56/56 étapes rendement/témoin et 50/50 étapes directes**, avec sauvegarde après chaque modèle–année. Les résultats originaux, les sources exécutées et les contrôles annuels sont disponibles dans [le rapport Colab](RESULTATS_COLAB.md). TabPFN ne remporte ni le classement Monte-Carlo ni celui du contrat direct.

## Suite ciblée

1. Comparer une grille de quantiles QRF plus dense à la reconstruction actuelle Q10/Q50/Q90 et queues linéaires, avec les mêmes 20 000 scénarios et cas de validation.
2. À distributions marginales inchangées, comparer les résidus indépendants à des rangs de résidus blé/lentille appariés, estimés hors échantillon. Partager l'année météo ne conserve pas toute la dépendance entre cultures. Évaluer ces deux changements séparément sur le contrat et les taux annuels.

La prévision 2026 est calculée avec les données arrêtées à 2025 pour reproduire une décision avant campagne. Elle ne présente pas la récolte 2026 comme un futur inconnu à la date d'exécution du 31 octobre 2026.


## Revue de la branche Youssef : validation et scénario économique

Branche examinée : [fix/validation-scenario-economique](https://github.com/youssefmir/hackthefork-hackathon/tree/fix/validation-scenario-economique), commit `c61ff3f4641af8b3bf72a272551da4d87d9f3f6c`. Les 31 tests passent dans l'environnement de recherche disponible ; le protocole, le backtest, les exports et la logique acheteur ont été lus. Ce contrôle n'est pas un build de l'interface.

**Décision : reprendre les améliorations de calcul et d'interface, puis remplacer le choix du modèle final par une sélection sur le contrat et un apprentissage temporel glissant.** La branche répond mieux à la négociation producteur–acheteur, mais son modèle automatique actuel n'est pas le candidat à promouvoir.

À reprendre : frontières temporelles des transformations et du regroupement ; tests qui perturbent réellement les données futures ; séparation entre quantiles de distribution et bornes conformelles ; comparaison des pertes de marge et du coût d'achat ; scénarios de dépendance entre cultures ; prix rendu partagé entre carte, parcelles sélectionnées et contrat ; plafond acheteur après tri et transformation. La séparation quantiles/intervalles est intégrée au run Colab via `--simulation-quantiles raw`. Les anciens résultats de cette branche recherche utilisent explicitement les quantiles élargis dans le Monte-Carlo et restent un contrôle historique ; la calibration de la distribution elle-même reste une expérience à comparer.

### Le résultat de 3 024 €/t vient largement du calendrier d'apprentissage

Dans le code examiné, pour prédire 2026, les coefficients et niveaux sont appris sur **2010–2020** ; 2021–2022 sélectionnent le modèle et 2023–2025 calibrent uniquement les intervalles. Or ces intervalles ne servent pas au prix. Les cinq années les plus récentes n'actualisent donc pas la tendance utilisée dans la simulation.

Un recalcul de contrôle, sans modification de la branche de Youssef, reproduit :

| Expérience en Seine-et-Marne | Prix Q80 départ ferme | Rendement lentille moyen simulé |
|---|---:|---:|
| Auto de la branche : M0 lentille / M0 blé, apprentissage 2010–2020 | 3 023,91 €/t | 0,829 t/ha |
| Même famille M0, tendance, niveaux et regroupement réajustés jusqu'en 2025 | 1 483,74 €/t | 1,443 t/ha |

Les deux expériences gardent les coûts de la branche (440/280 €/ha, aide et rotation nulles), le pool 2010–2025, 20 000 scénarios et la graine 77. La seconde est une ablation du calendrier, pas un modèle déjà sélectionné par backtest. Elle montre pourquoi le prix élevé ne suffit pas à conclure à l'impasse économique de la filière.

Le protocole figé de 2019 n'utilise que quatre années pour apprendre. Je propose d'estimer les erreurs par prévisions glissantes hors échantillon, puis d'ajuster le prédicteur final avec tout le passé disponible, en conservant une calibration distincte de la distribution/du prix.

### Sélectionner le contrat qui répond à l'objectif

`auto` minimise la pinball des rendements avec météo réalisée. Notre décision porte sur le **quantile 80 % du prix d'équilibre avant campagne**. Il faut sélectionner sur cette perte économique, puis départager avec le taux de marge gagnante et le manque €/ha. Le backtest livré affiche 60,1 % de marges gagnantes pour auto ; ces 173 cas ne sont pas les 192 de notre benchmark et les hypothèses diffèrent.

La calibration des intervalles est bien corrigée dans cette branche. Mais elle n'améliore pas la distribution simulée : le code teste explicitement que changer `qhat` ne change aucun prix. La suite utile est donc une calibration temporelle des quantiles ou de la décision économique, testée sur le contrat, plutôt qu'un élargissement d'intervalle pris pour une distribution.

### Hypothèses économiques à retenir pour le hackathon

L'aide n'a pas à être nulle au motif que la lentille serait d'éligibilité inconnue : la [notice Telepac 2026, p. 4](https://www.telepac.agriculture.gouv.fr/telepac/pdf/tas/2026/Dossier-PAC-2026_notice_aides-couplees.pdf) inclut explicitement les lentilles récoltées en graines, y compris pour l'alimentation humaine. Les [122 €/ha de l'arrêté](https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000053594055) concernent la campagne 2025. Utiliser l'aide de la campagne comme hypothèse centrale pour les surfaces éligibles, avec zéro en variante.

Le plafond acheteur est une bonne addition : `revente × (1 − pertes) − tri − transformation − autres coûts − marge`. Pour agir sur un éventuel écart de prix, comparer un prix uniforme, un contrat à paliers et un prix de base plus une prime par hectare. À prix de base p, la prime minimale est `max(0, Q80(PW*YW-CW+CL-aide-p*YL))`. Elle soutient les très faibles récoltes. La rotation peut être un scénario commercial assumé, affiché séparément de la marge de campagne.

Enfin, `p_star()` utilise encore le quantile interpolé par défaut. Pour correspondre exactement au plus petit prix couvrant au moins 80 % des scénarios, employer `method="inverted_cdf"` et arrondir au-dessus à la précision du contrat. C'est une correction simple, distincte des choix de modèle.
