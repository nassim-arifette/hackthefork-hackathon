# Résultats

Calculés par le pipeline (`make export`) le 30 octobre 2026. Les chiffres de l'application et du deck viennent de ces exports, jamais d'une saisie à la main.

## 1. Le constat, mesuré

| Indicateur | Valeur | Source |
|---|---|---|
| Importations de lentilles, 2025 | 39 371 t | Eurostat Comext, NC8 0713 40 |
| Exportations de lentilles, 2025 | 5 032 t | Eurostat Comext |
| Production de lentilles, 2025 | 51 558 t (provisoire) | Agreste SAA |
| Surface en lentille, 2025 | 33 927 ha | Agreste SAA |
| Coefficient de variation du rendement national 2010–2025 | lentille 0,20 ; blé tendre d'hiver 0,09 | Agreste SAA |
| Prix observés de la lentille, France | 650 à 779 €/t (2012–2016) | Eurostat, prix de vente absolus |
| Prix du blé tendre | 154 €/t (2016) à 338 €/t (2022) | indice Eurostat, calé sur le prix rendu Rouen Agreste 2019-2020 |

## 2. Les données utilisées par le modèle

- **Lentille** : 39 départements mesurés, mais Agreste estime souvent leurs rendements ensemble, au niveau régional. Après regroupement des séries identiques sur au moins 8 années, il reste **24 séries indépendantes**, soit 294 couples département × année.
- **Blé tendre d'hiver** : 1 439 couples sur 90 séries.
- **Météo** : NASA POWER pour 43 départements, 2010–2025.
- **Parcelles** : 20 922 parcelles du RPG 2025 en Île-de-France, dont 20 762 de blé tendre d'hiver.

## 3. Backtest 2019–2025, sans fuite

Pour chaque année test, les modèles, les niveaux et la calibration sont estimés sur les seules années antérieures. Le prix plancher est fixé avec la météo et le prix du blé de ces années, puis jugé sur les rendements et le prix du blé réels.

| Année | Cas | Prix du blé | Couverture de l'intervalle à 80 % | Contrats tenus (M1) | Contrats tenus (choix automatique) |
|---|---|---|---|---|---|
| 2019 | 17 | 179 €/t | 94 % | 94 % | 82 % |
| 2020 | 18 | 191 €/t | 56 % | **44 %** | 44 % |
| 2021 | 18 | 238 €/t | 56 % | **61 %** | 61 % |
| 2022 | 19 | 338 €/t | 89 % | 95 % | 79 % |
| 2023 | 20 | 242 €/t | 95 % | 100 % | 100 % |
| 2024 | 20 | 216 €/t | 70 % | 100 % | 95 % |
| 2025 | 21 | 202 €/t | 90 % | 100 % | 95 % |
| **Ensemble** | **133** | | **79 %** | **86 %** pour 80 % visés | 80 % |

| Modèle | Perte pinball | Couverture à 80 % |
|---|---|---|
| M0, tendance seule | 0,1078 | 74 % |
| **M1, régression quantile météo (retenu a priori)** | 0,1103 | 79 % |
| M2, LightGBM quantile | 0,1014 | 84 % |
| Choix automatique sur validation interne | 0,1024 | 74 % |

Erreur médiane sur le rendement relatif d'une année : ±33 %.

### Lecture

- **La fiabilité visée est atteinte sur l'ensemble** (86 % pour 80 %), mais sur 7 années seulement. Les contrats cèdent en **2020 et 2021**, deux effondrements de la lentille absents de l'entraînement.
- **La calibration fonctionne** : 79 % des récoltes tombent dans l'intervalle à 80 %, contre 74 % pour la tendance seule.
- **La météo n'améliore pas la précision du modèle linéaire** (pinball −2 % face à la tendance). LightGBM fait mieux (+6 %), mais il n'a pas été choisi a priori. Le choix automatique sur validation interne est plus précis mais moins bien calibré, et tient moins de contrats.
- **Le rendement d'une année reste difficile à prévoir** (±33 %). C'est la raison d'être d'un prix calibré sur le risque plutôt que sur une prévision.

## 4. Prix plancher, campagne 2026

| Département | P\* (8 années sur 10) | Prix d'équilibre médian | Rendement lentille moyen simulé | Rendement d'une année sur dix |
|---|---|---|---|---|
| Seine-et-Marne | 1 622 €/t | 743 €/t | 1,59 t/ha | 0,48 t/ha |
| Yvelines | 1 502 €/t | 706 €/t | 1,61 t/ha | 0,50 t/ha |
| Essonne | 1 506 €/t | 707 €/t | 1,60 t/ha | 0,50 t/ha |
| Val-d'Oise | 1 585 €/t | 747 €/t | 1,61 t/ha | 0,50 t/ha |

**Incertitude sur P\*** (Seine-et-Marne, rééchantillonnage des années, 40 tirages) : de 1 132 à 3 007 €/t à 80 %, médiane 1 801 €/t.

### Le prix de la sécurité (Seine-et-Marne)

| Années gagnantes visées | 5 sur 10 | 6 | 7 | 8 | 9 | 9,5 |
|---|---|---|---|---|---|---|
| P\* | 743 | 907 | 1 176 | 1 622 | 2 733 | 4 588 €/t |

Au prix de marché observé (milieu de la fourchette, 715 €/t), la lentille rapporte au moins autant que le blé **4,7 années sur 10**.

### Sensibilités (Seine-et-Marne)

| Hypothèse | P\* |
|---|---|
| Prix du blé fixé de 160 à 280 €/t | 1 180 à 2 334 €/t |
| Bonus de rotation de 0 à 200 €/ha | 1 622 à 1 378 €/t |
| Charges du blé de 440 à 600 €/ha | 1 622 à 1 426 €/t |
| Charges de la lentille de 230 à 340 €/ha | 1 561 à 1 696 €/t |
| Sans aide couplée | 1 770 €/t |

### Là où la lentille tient le mieux

| Département | P\* |
|---|---|
| Pyrénées-Orientales | 914 €/t |
| Gard | 1 189 €/t |
| Indre | 1 222 €/t |
| Hérault | 1 247 €/t |
| Aube (estimée avec les Ardennes, la Haute-Marne et la Marne) | 1 293 €/t |

Le prix plancher baisse là où le blé rend moins (Pyrénées-Orientales : 33 q/ha) ou la lentille mieux (Aube : 21 q/ha).

## 5. Le contrat de démonstration

- Prix garanti rendu au site : 1 660 €/t.
- Volume visé (hypothèse) : 5 000 t, soit 13 % des importations 2025.
- Surface nécessaire : 3 147 ha, soit les 236 parcelles éligibles les plus proches du site, toutes à moins de 9,4 km.

## 6. Ce que ça veut dire

1. **Garantir 8 années sur 10 coûte plus du double du prix d'équilibre médian.** Une moyenne sous-estime fortement le prix qu'il faut garantir : c'est le cœur du message.
2. **Au prix de marché, la lentille ne gagne qu'environ une année sur deux.** C'est exactement le verrou que décrit le Track 3.
3. **Le prix plancher est très sensible au prix du blé.** Un contrat indexé sur le prix du blé (multiplicateur médian de 3,6, de 7,8 pour 8 années sur 10) déplacerait ce risque vers la coopérative ; piste à étudier.
4. **Le prix plancher est lui-même incertain** : seize années ne suffisent pas à cerner les mauvaises années. Les données de rendement des coopératives sont la première chose à obtenir en pilote.

## Historique

- Version 1 (hypothèses provisoires, prix du blé fixe, 39 séries comptées comme indépendantes) : 85 % de contrats tenus, P\* de 1 377 €/t en Seine-et-Marne.
- Version 2 (prix du blé mesuré et rééchantillonné, charges et aide sourcées) : 82 %, 1 435 €/t.
- Version 3, actuelle (séries estimées ensemble regroupées) : 86 %, 1 622 €/t, avec un intervalle de confiance sur P\*. Ces changements viennent de la qualité des données, pas du résultat du backtest : le protocole et le modèle retenu sont restés les mêmes.
