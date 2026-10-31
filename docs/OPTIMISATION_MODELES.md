# Optimisations testées directement dans Colab

**QRF Monte-Carlo reste la meilleure base.** Le 31 octobre 2026, deux expériences supplémentaires ont été exécutées sur le runtime Colab existant : six variantes QRF et quatre configurations CatBoost direct, chacune avec une sélection fondée uniquement sur le passé. Les données et hypothèses économiques restent celles du benchmark terminé.

## Résultats comparables

Les modèles sont évalués sur les mêmes **192 cas département × année, de 2019 à 2025**. La perte contrat est la pinball à 0,8 du prix d'équilibre réalisé, moyennée à poids égal par année ; plus bas est meilleur. Le taux tenu compte les cas où le prix proposé permet à la marge lentille d'égaler ou dépasser celle du blé. Les prix sont départ ferme.

| Modèle | Perte contrat €/t ↓ | Contrats tenus | Prix médian €/t |
|---|---:|---:|---:|
| QRF Monte-Carlo initial | 209,49 | 63,0 % | 1 159 |
| QRF, 101 quantiles fixes | 208,48 | 64,1 % | 1 170 |
| QRF, paramètres sélectionnés sur le passé | 212,01 | 63,0 % | 1 170 |
| CatBoost direct, sélection passée | 247,44 | 66,7 % | 1 364 |
| QRF direct initial | 280,91 | 78,1 % | 1 511 |
| QRF direct calibré initial | 316,49 | 82,3 % | 1 744 |

**101 quantiles apportent un petit gain de 0,5 %**, avec un manque moyen ramené de 108,54 à 105,95 €/ha. La sélection automatique des variantes QRF dégrade le score de 1,2 %. Les variantes conservant tous les exemples dans les feuilles ou modifiant la profondeur ne dépassent pas la référence. Le résultat du candidat fixe est descriptif ; la politique sélectionnée sur le passé mesure ce qu'aurait donné le réglage automatique.

**CatBoost direct améliore QRF direct de 11,9 % en perte**, mais tient moins de contrats. Il reste derrière QRF Monte-Carlo. Son meilleur candidat fixe rétrospectif atteint 230,75 €/t et 67,7 % de contrats tenus ; le résultat de la sélection passée demeure 247,44 €/t. Une baisse de perte ne signifie pas automatiquement que l'objectif de protection de 80 % est atteint.

## Ce qui a été testé

**QRF.** Passage de Q10/Q50/Q90 avec extrapolation des queues à une interpolation de 101 quantiles entre 0 et 1. Comparaison séparée de `max_samples_leaf=1` et `None`, puis de deux couples profondeur/taille minimale des feuilles. La [documentation officielle quantile-forest](https://zillow.github.io/quantile-forest/user_guide/fit_predict.html) précise que le réglage par défaut conserve un exemple aléatoire par feuille ; `None` les conserve tous. Tous les candidats utilisent le même modèle linéaire blé, les mêmes années météo/prix historiques et les mêmes 20 000 tirages. Le témoin reproduit les prix du premier run à moins de 10⁻⁷ €/t près.

**CatBoost direct.** Quatre candidats combinent profondeur 2 ou 3 et cible prix brut ou écart au prix de référence calculable avant campagne. L'objectif est directement `Quantile:alpha=0.8` en €/t, avec le même poids total pour chaque année d'entraînement. Les variables explicatives excluent météo et prix réalisés de l'année cible. Voir les [objectifs officiels CatBoost](https://catboost.ai/docs/en/concepts/loss-functions-regression).

Les deux sélecteurs utilisent les trois années précédentes, à partir des prédictions 2016–2018 pour la décision 2019. Chaque entraînement est limité aux années antérieures. Les 2019–2025 ont déjà servi à explorer les modèles : ces nouveaux essais poursuivent cette comparaison temporelle de recherche.

## Fichiers et vérification

- [QRF : rapport, paramètres, prédictions, archive complète](../experiments/qrf_optimization/README.md) ; [script](../pipeline/benchmark_qrf_optimization.py).
- [CatBoost : rapport, paramètres, prédictions et audits](../experiments/direct_catboost_optimization/README.md) ; [script](../pipeline/benchmark_direct_catboost.py).
- Sauvegardes Drive : `HackTheFork/optimizations/2026-10-31/qrf` et `HackTheFork/optimizations/2026-10-31/direct_catboost`.

Les résultats ont été téléchargés depuis Colab, les empreintes des scripts vérifiées, les scores recalculés et toutes les décisions des sélecteurs reproduites depuis les prédictions passées. **41 tests passent**, dont les six nouveaux contrôles de quantiles, sélection temporelle, poids annuels et cohorte. Aucun export de production n'est remplacé par ces expériences.

## Prochain essai prioritaire

Mon choix est de conserver QRF et de tester la **dépendance des erreurs de rendement blé/lentille**, à distributions marginales inchangées. Le code partage déjà l'année météo, mais tire encore les rangs résiduels des deux cultures indépendamment. Estimer leurs rangs conjoints sur des prévisions strictement passées permettrait de tester cette hypothèse sans changer simultanément le modèle et les scénarios.

Ensuite : comparer une calibration du prix plus stable que la fenêtre actuelle de trois ans, avec poids des années et intensité de correction choisis sur le passé. Le critère de décision doit montrer ensemble perte contrat, taux tenu annuel et manque à l'hectare. Ces pistes restent à mesurer ; les essais achevés ici établissent seulement que densifier QRF apporte peu et que CatBoost direct ne détrône pas QRF Monte-Carlo.
