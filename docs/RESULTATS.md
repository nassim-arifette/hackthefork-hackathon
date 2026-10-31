# Résultats recalculés — 30 octobre 2026

Ces chiffres remplacent ceux des versions précédentes. Les changements de cohorte, normalisation, calibration, simulation et aide empêchent une comparaison directe avec les anciens taux. Protocole : [MODELE](MODELE.md). Articles : [RECHERCHE](RECHERCHE.md).

**L’objectif de 80 % n’est pas atteint dans l’évaluation : la procédure automatique atteint la marge du blé dans 60,1 % des 173 cas, sur 7 années.** Elle ne démontre pas une garantie de marge ni la supériorité économique de la météo.

## Diagnostic des rendements

Quantiles bruts pour la perte pinball ; bornes corrigées pour la couverture. La météo de l’année test est observée rétrospectivement : ces métriques conditionnelles ne sont pas des prévisions avant semis.

| Modèle lentille | Perte pinball ↓ | Couverture, objectif 80 % | Erreur absolue médiane normalisée | Erreur absolue médiane q/ha |
|---|---:|---:|---:|---:|
| M0 | 0,1330 | 63,0 % | 0,302 | 4,80 |
| M1 | 0,1478 | 65,3 % | 0,337 | 5,01 |
| M2 | 0,1307 | 74,6 % | 0,328 | 4,68 |
| M3 | 0,1332 | 67,6 % | 0,309 | 4,46 |
| auto | 0,1320 | 63,6 % | 0,302 | 4,62 |

M2 obtient ici la perte quantile la plus basse, mais cela ne prouve pas qu’il produit le contrat économiquement le plus utile. La médiane des erreurs en q/ha est calculée par observation après conversion avec son propre niveau départemental ; ce n’est pas la médiane normalisée multipliée par un niveau moyen.

## Comparaison économique

Charges communes constantes : blé 440 €/ha, lentille 280 €/ha, aide 0 €/ha, rotation 0 €/ha. Prix départ ferme. Le blé utilise la même procédure automatique pour tous les candidats lentille M0–M3 : M0 exclut la météo pour la lentille seulement. La méthode historique est entièrement sans modèle météo, avec rendements des deux cultures et prix appariés. La référence « moyenne » ne vise pas un quantile de protection.

| Méthode | Succès | Prix médian €/t | Manque moyen €/ha | Manque moyen en échec €/ha | Achat moyen €/ha |
|---|---:|---:|---:|---:|---:|
| moyenne | 30,1 % | 775 | 359 | 513 | 951 |
| historique | 48,6 % | 1 015 | 251 | 488 | 1 301 |
| M0 | 60,1 % | 1 291 | 170 | 426 | 1 623 |
| M1 | 54,9 % | 1 195 | 202 | 448 | 1 484 |
| M2 | 48,6 % | 942 | 267 | 519 | 1 202 |
| M3 | 52,6 % | 1 133 | 214 | 452 | 1 402 |
| auto | 60,1 % | 1 291 | 175 | 439 | 1 609 |

Le rééchantillonnage descriptif des années entières donne pour le succès automatique une plage à 95 % de 37,1 à 83,2 %. Sept blocs annuels et leur dépendance possible limitent fortement son interprétation ; ce n’est pas une garantie fréquentiste ou individuelle.

La référence historique moins coûteuse protège moins souvent. Comparer les prix sans tenir compte des pertes, ou les succès sans tenir compte du prix, conduirait à une conclusion trompeuse. Le manque est max(0, marge blé − marge lentille), pas une perte comptable absolue.

## Grille de protection de la procédure automatique

Cette grille descriptive n’a pas servi à choisir un taux sur les résultats test. Un objectif simulé identique ne signifie pas une protection réelle identique. Les autres méthodes sont disponibles dans le panneau Méthode et sources et dans le JSON.

| Objectif simulé | Succès observé | Prix médian €/t | Manque moyen €/ha |
|---|---:|---:|---:|
| 50 % | 45,7 % | 967 | 269 |
| 60 % | 48,0 % | 1 049 | 237 |
| 70 % | 55,5 % | 1 156 | 206 |
| 80 % | 60,1 % | 1 291 | 175 |
| 90 % | 68,2 % | 1 465 | 142 |
| 95 % | 72,3 % | 1 651 | 122 |

## Campagne 2026 — transfert à l’Île-de-France

La sélection temporelle retient **M0 pour la lentille et M0 pour le blé**. Apprentissage 2010–2020, sélection 2021–2022, calibration 2023–2025. Aucun réentraînement après calibration. Les niveaux franciliens de lentille sont transférés des voisins : ils ne constituent pas une validation locale.

| Département | Prix requis départ ferme €/t |
|---|---:|
| 77 | 3 024 |
| 78 | 2 901 |
| 91 | 2 838 |
| 95 | 3 021 |

En Seine-et-Marne, la variante avec aide conditionnelle de 122 €/ha donne 2 764 €/t, contre 3 024 €/t sans aide. L’éligibilité et l’applicabilité restent à confirmer.

À modèles figés, le rééchantillonnage des années météo/prix donne les quantiles 10–90 % de 2 767 à 3 213 €/t. Cette sensibilité ne couvre pas l’erreur d’estimation des modèles, le transfert territorial, les queues inconnues ni les erreurs des hypothèses économiques.

| Hypothèse de queue | Dépendance résiduelle des cultures | Prix requis 77 €/t |
|---|---|---:|
| linear | independent | 3 024 |
| bounded | independent | 2 978 |
| stress | independent | 3 022 |
| linear | positive | 2 661 |
| linear | negative | 3 357 |

## Acheteur et contrat

Avec les hypothèses acheteur par défaut, le plafond rendu vaut **1 868 €/t**, alors que mobiliser 5 000 t attendues nécessite au moins **2 846 €/t rendu**. Le verdict est donc **accord impossible dans ce scénario**. L’utilisateur peut modifier l’offre, la revente, les pertes au tri et les coûts ; ces entrées ne sont pas des cotations observées.

Le contrat porte sur une campagne 2026. Son prix rendu, la sélection des parcelles et le volume attendu sont partagés avec la carte et le scénario de stress. Le volume n’est pas garanti. La référence lentille nominale 2012–2016 ne décrit pas le marché actuel ; le prix du blé est reconstruit à partir d’Eurostat et d’Agreste.

## Validation et portée

31 tests Python réussis : appels réels d’ajustement, prédicteur figé, rang de calibration, invariance après perturbation du futur, absence d’effet des anciens regroupements, coûts et cohérence du scénario. Le code ne réutilise pas les bornes conformelles comme quantiles simulés.

Les données 2019–2025 ont déjà été examinées pendant le développement. Cette réanalyse rétrospective demande une future validation indépendante ; l’amélioration logicielle ne rend pas les performances scientifiques acquises. Voir [LIMITES](LIMITES.md).
