# Résultats

Calculés par le pipeline (`make export`) le 31 octobre 2026, avec le scénario d'hypothèses de la version 4 (`data/hypotheses.yaml`). Les chiffres de l'application et du deck viennent de ces exports, jamais d'une saisie à la main.

## 1. Le constat, mesuré

| Indicateur | Valeur | Source |
|---|---|---|
| Importations de lentilles, 2025 | 39 371 t | Eurostat Comext, NC8 0713 40 |
| Provenance des importations, 2025 | Canada 45 %, Belgique 37 %, Turquie 6 % (pays d'origine hors UE, d'expédition dans l'UE) | Eurostat Comext |
| Consommation apparente, 2025 | 85 897 t, dont 46 % importées (production + importations − exportations, stocks non comptés) | Agreste SAA, Eurostat Comext |
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

## 3. Le scénario économique

| Paramètre | Valeur | Statut |
|---|---|---|
| Charges opérationnelles du blé | 700 €/ha | supposé, arrondi de 675 €/ha (Cerfrance Nord-Est Île-de-France, cité par Terres Inovia 2025) |
| Charges opérationnelles de la lentille | 500 €/ha | supposé, arrondi de 518 €/ha (guide lentille Terres Inovia 2023) |
| Aide couplée aux légumineuses | 105 €/ha | sourcé, montant indicatif 2026 (notice Telepac) |
| Bénéfice de rotation pour le blé suivant | 150 €/ha | supposé, effet précédent documenté par FiloLeg 2024 |
| Part de la récolte refusée au tri | 10 % | supposé |
| Collecte | 5 €/t de forfait + 0,12 €/t/km, distance × 1,3 | supposé |

**Le prix garanti est payé sur les tonnes acceptées au tri**, comme dans les contrats de collecte : un lot refusé (bruche, impuretés, calibre) n'est pas payé au prix garanti. Agreste mesure la récolte à l'arrivée à la ferme, avant ce tri : le modèle retire donc 10 % du rendement simulé, une seule fois. Le prix plancher s'entend départ ferme ; le forfait et le transport s'ajoutent pour l'acheteur.

## 4. Backtest 2019–2025, sans fuite

Pour chaque année test, le regroupement des séries en double, les modèles, les niveaux et la calibration sont estimés sur les seules années antérieures. Le prix plancher est fixé avec la météo et le prix du blé de ces années, puis jugé sur les rendements et le prix du blé réels.

**Correction du 31/10 (audit de la PR 1).** Le regroupement des séries Agreste identiques utilisait toute la période 2010–2025, donc une information des années testées. Il est maintenant refait chaque année avec le seul passé : en 2019, le modèle apprend sur 32 séries au lieu de 19, car neuf années ne suffisent pas toujours à repérer deux séries copiées. Le taux de contrats tenus passe de 87 % à 78 %. Les cas évalués restent les 133 mêmes ; les prix 2026, qui utilisent légitimement toutes les années jusqu'en 2025, ne changent pas.

| Année | Cas | Prix du blé | Couverture de l'intervalle à 80 % | Contrats tenus (M1) | Contrats tenus (choix automatique) |
|---|---|---|---|---|---|
| 2019 | 17 | 179 €/t | 100 % | 76 % | 71 % |
| 2020 | 18 | 191 €/t | 56 % | **39 %** | 39 % |
| 2021 | 18 | 238 €/t | 61 % | **56 %** | 56 % |
| 2022 | 19 | 338 €/t | 95 % | **68 %** | 63 % |
| 2023 | 20 | 242 €/t | 90 % | 100 % | 100 % |
| 2024 | 20 | 216 €/t | 60 % | 100 % | 95 % |
| 2025 | 21 | 202 €/t | 90 % | 100 % | 95 % |
| **Ensemble** | **133** | | **79 %** | **78 %** pour 80 % visés | 75 % |

| Modèle | Perte pinball | Couverture à 80 % |
|---|---|---|
| M0, tendance seule | 0,1094 | 70 % |
| **M1, régression quantile météo (retenu a priori)** | 0,1105 | 79 % |
| M2, LightGBM quantile | 0,1020 | 77 % |
| Choix automatique sur validation interne | 0,1038 | 70 % |

Erreur médiane sur le rendement relatif d'une année : ±35 %.

### Ce que le modèle apporte : quatre façons de fixer le prix

| Façon de fixer le prix | Contrats tenus (80 % visés) | P\* 2026, Seine-et-Marne |
|---|---|---|
| Moyennes des années passées (référence naïve, sans modèle) | **29 %** | 742 €/t |
| Distribution calibrée, tendance seule, sans météo (M0) | 77 % | 2 932 €/t |
| **Régression quantile avec météo (M1, retenue)** | **78 %** | 1 567 €/t |
| LightGBM avec météo (M2) | 76 % | 1 000 €/t |

- Fixer le prix sur les moyennes ne tient que trois contrats sur dix : un prix moyen protège l'année moyenne, pas la mauvaise.
- Le modèle probabiliste calibré approche la promesse de 80 % : 78 %, soit 104 contrats tenus sur 133. Il fait mieux que la tendance seule (77 %) pour un prix 2026 presque deux fois plus bas (1 567 contre 2 932 €/t) : c'est là qu'est l'apport de la météo, plus que dans le taux.
- Le prix 2026 change fortement d'un modèle à l'autre : c'est une incertitude de modèle, affichée à côté de l'incertitude statistique.
- Exploration non retenue (`pipeline/explore_regularisation.py`) : une régularisation choisie en validation interne est plus précise que la tendance seule, mais l'intervalle ne couvre plus qu'environ 71 % des cas.

### Lecture

- **La promesse est presque tenue** : 78 % pour 80 % visés, sur 7 années seulement ; l'écart de deux points représente deux à trois contrats. L'objectif est d'être proche de 80 %, pas de 100 % : au-dessus, l'acheteur paie trop ; en dessous, l'agriculteur est trompé.
- Les contrats cèdent surtout en **2020 et 2021**, deux effondrements de la lentille absents de l'entraînement, puis en **2022**, quand le prix du blé atteint 338 €/t.
- **La calibration fonctionne** : 79 % des récoltes tombent dans l'intervalle à 80 %, contre 70 % pour la tendance seule.
- **La météo n'améliore pas la précision du modèle linéaire** (pinball −1 % face à la tendance). LightGBM fait mieux (+7 %), mais il tient moins de contrats et n'a pas été choisi a priori.
- **Le rendement d'une année reste difficile à prévoir** (±35 %). C'est la raison d'être d'un prix calibré sur le risque plutôt que sur une prévision.
- La PR 1 montre aussi qu'une forêt aléatoire quantile (QRF), avec une correction du prix calibrée sur le passé, baisse le prix d'environ 10 % à protection égale dans les bassins producteurs ; elle ne fait pas mieux sur les départements qui servent de référence à l'Île-de-France. Le modèle de l'application reste M1.

## 5. Prix plancher, campagne 2026

| Département | P\* (8 années sur 10) | Prix d'équilibre médian | Rendement lentille moyen simulé | Dont accepté au tri | Rendement d'une année sur dix |
|---|---|---|---|---|---|
| Seine-et-Marne | 1 567 €/t | 715 €/t | 1,59 t/ha | 1,43 t/ha | 0,48 t/ha |
| Yvelines | 1 445 €/t | 674 €/t | 1,61 t/ha | 1,45 t/ha | 0,50 t/ha |
| Essonne | 1 450 €/t | 674 €/t | 1,60 t/ha | 1,44 t/ha | 0,50 t/ha |
| Val-d'Oise | 1 540 €/t | 718 €/t | 1,61 t/ha | 1,45 t/ha | 0,50 t/ha |

**Incertitude sur P\*** (Seine-et-Marne, rééchantillonnage des années, 40 tirages) : de 1 099 à 2 877 €/t à 80 %, médiane 1 742 €/t.

### Le prix de la sécurité (Seine-et-Marne)

| Années gagnantes visées | 5 sur 10 | 6 | 7 | 8 | 9 | 9,5 |
|---|---|---|---|---|---|---|
| P\* | 715 | 871 | 1 132 | 1 567 | 2 632 | 4 397 €/t |

À la référence historique 2012–2016 (milieu de la fourchette, 715 €/t), la lentille rapporte au moins autant que le blé **5 années sur 10**. À 900 €/t, 6,1 années sur 10 ; à 1 000 €/t, 6,5.

### Sensibilités (Seine-et-Marne)

| Hypothèse | P\* |
|---|---|
| Prix du blé fixé de 160 à 280 €/t | 1 070 à 2 348 €/t |
| Part refusée au tri de 0 à 20 % | 1 411 à 1 763 €/t |
| Bénéfice de rotation de 200 à 0 €/ha | 1 500 à 1 773 €/t |
| Charges du blé de 800 à 600 €/ha | 1 432 à 1 703 €/t |
| Charges de la lentille de 400 à 600 €/ha | 1 432 à 1 703 €/t |
| Aide couplée à 122, 105 ou 0 €/ha | 1 546, 1 567 ou 1 709 €/t |
| Hypothèses de la version 3 (charges 440 / 280 €/ha, aide 122 €/ha, sans rotation ni refus au tri) | 1 622 €/t |

### Là où la lentille tient le mieux

| Département | P\* |
|---|---|
| Pyrénées-Orientales | 558 €/t |
| Hérault | 842 €/t |
| Gard | 900 €/t |
| Indre | 1 115 €/t |
| Cher | 1 183 €/t |

Le prix plancher baisse là où le blé rend peu (Pyrénées-Orientales : 33 q/ha) ou là où la lentille rend bien face au blé (Indre : 18 q/ha de lentille pour 62 q/ha de blé). Ce classement applique partout les charges franciliennes : il compare des rendements, pas des économies locales.

L'écran 6 de l'application (onglet « La France ») montre les 24 départements classés, de 558 €/t (Pyrénées-Orientales) à 2 238 €/t (Haute-Loire). Agreste publie un seul rendement pour 21 autres départements, estimé avec l'un des 24 : la carte leur donne, en teinte pâle, le prix du département qui les représente. Les autres n'ont pas de série utilisable (moins de 50 ha de lentilles, ou rendement non mesuré).

## 6. Le contrat de démonstration

**Contrat proposé : barème par tranches, 1 635 €/t pour la première tonne acceptée par hectare, 750 €/t pour la deuxième, 650 €/t au-delà**, départ ferme, sur trois campagnes. Il protège autant qu'un prix unique de 1 567 €/t pour 18 % de moins en moyenne (§7). La lettre d'accompagnement reprend ce barème.

Pour la carte et les volumes, l'application raisonne en prix rendu au site de collecte : **1 600 €/t**, le P\* de la Seine-et-Marne arrondi au-dessus. Une parcelle bascule si ce prix, moins le forfait de collecte et le transport, couvre le P\* de son département.

| | Pilote | Ambition de bassin |
|---|---|---|
| Tonnes acceptées visées | 300 t | 5 000 t |
| Surface nécessaire | 216 ha | 3 502 ha |
| Parcelles éligibles les plus proches du site | 28, à moins de 3,2 km | 260, à moins de 9,8 km |
| Part des importations 2025 | 0,8 % | 12,7 % |
| Protéines potentielles (25 % des tonnes) | 75 t | 1 250 t |
| Azote minéral non apporté (180 kg N/ha de blé remplacé) | 39 t N | 630 t N |
| Émissions directes de N₂O évitées (0,755 t CO₂e/ha) | 163 t CO₂e | 2 644 t CO₂e |

Les distances sont routières (vol d'oiseau × 1,3). Les compteurs d'impact excluent la fabrication des engrais et les émissions indirectes.

### Rejouer deux années à 1 600 €/t (Seine-et-Marne)

| Année | Marge lentille sous contrat | Marge blé | Parcelles qui tiennent |
|---|---|---|---|
| 2016, le blé perd 53 % | 1 757 €/ha | −84 €/ha | toutes |
| 2020, la lentille perd 38 % | 1 181 €/ha | 771 €/ha | toutes |

### Déplacer le site de collecte

Un clic sur la carte déplace le site ; distances, parcelles retenues et coût de collecte se recalculent dans le navigateur, avec les formules du pipeline. La recherche du meilleur emplacement parcourt une grille de points, affinée deux fois.

| Volume | Site du scénario | Meilleur point de la grille |
|---|---|---|
| Pilote, 300 t | 2,4 km en moyenne, 5,3 €/t de collecte | 0,7 km, 5,1 €/t |
| Ambition, 5 000 t | 7,1 km, 5,9 €/t | 4,7 km, 5,6 €/t |

Le gain reste de quelques dixièmes d'euro par tonne, face à un prix garanti de plus de 1 000 €/t : avec ces coûts, le site se choisit pour la logistique (silo, accès), pas pour le prix.

### Les sites de collecte qui existent déjà

`pipeline/11_sites.py` liste, dans la base Sirene, les établissements actifs des entreprises du commerce de gros de céréales (NAF 46.21Z), codés commerce de grains (46.21Z) ou entreposage (52.10B), à moins de 15 km d'une parcelle francilienne : **352 établissements, dont 171 de coopératives** (extraction du 31/10/2026, hors entrepreneurs individuels). Sirene ne distingue pas un silo d'un bureau ou d'un magasin : ce sont des sites candidats, capacités inconnues.

| Volume | Site du scénario | Meilleur établissement existant |
|---|---|---|
| Pilote, 300 t | 2,4 km en moyenne | Vivescia, Chenoise-Cucharmoy : 1,0 km |
| Ambition, 5 000 t | 7,1 km | Vivescia, Maison-Rouge : 4,8 km |

Distances : moyenne pondérée par les tonnes des parcelles de blé les plus proches qui réunissent le volume. Le meilleur site existant fait aussi bien que le meilleur point de la grille, à quelques centaines de mètres près : le contrat peut s'appuyer sur un établissement qui travaille déjà le grain. Dans la zone du Maillon, les 152 parcelles de légumineuses déclarées en 2025 (1 053 ha) sont à 6,4 km en moyenne de l'établissement existant le plus proche, 12,4 km au plus ; 91 % de leur surface à moins de 10 km.

## 7. Comparer les contrats

Calcul de `pipeline/07_contrats.py` sur les mêmes 20 000 années que le prix plancher (Seine-et-Marne), et backtest de `03_backtest.py` sur les 133 cas 2019–2025. Coût moyen : sommes versées par l'acheteur par tonne acceptée, hors collecte et tri. Année faible : 0,43 t/ha acceptées, une année sur dix.

### Les contrats publiés, face au blé francilien

| Contrat | Années gagnantes (simulation) | Coût moyen | Contrats tenus (backtest) |
|---|---|---|---|
| Unéal, 900 €/t (décembre 2023) | 6,1 sur 10 | 900 €/t | 57 % |
| NatUp 2023–2024 reconstitué : 900 / 700 / 600 €/t par tranche d'une tonne par hectare | 5,9 sur 10 | 818 €/t | 55 % |
| Proposition du dossier pilote : 1 000 / 750 / 650 €/t, 30 €/t pour un lot pré-nettoyé | 6,4 sur 10 | 928 €/t | 65 % |

Les barèmes publiés protègent environ 6 années sur 10 face au blé francilien : ils partagent aussi le risque par les volumes, la qualité et le choix des bassins, que ce calcul ne mesure pas.

### Trois façons de garantir 8 années sur 10

| Contrat calibré | Coût moyen | Année faible | Perte moyenne les années perdantes | Contrats tenus (backtest) | Coût réalisé (backtest) |
|---|---|---|---|---|---|
| Prix unique : 1 567 €/t | 1 567 €/t | 1 567 €/t | 581 €/ha | 78 % | référence |
| **Tranches : 1 635 €/t la première tonne par hectare, puis 750 et 650** | **1 283 €/t (−18 %)** | 1 635 €/t | 568 €/ha | **79 %** | **−19 %** |
| Prix de base 900 €/t et prime de 491 €/ha | 1 243 €/t (−21 %) | 2 037 €/t | 426 €/ha | 74 % | −39 % |

Dans le backtest, chaque forme est recalibrée chaque année sur les seules années passées, comme le prix unique. Les coûts réalisés portent sur les départements producteurs, d'où la comparaison en écart au prix unique.

**Lecture :**

- **Le barème par tranches protège autant que le prix unique pour nettement moins cher.** Il paie cher les premières tonnes, celles qui manquent les mauvaises années, et moins le surplus des bonnes. En backtest, il tient même un peu plus de contrats (79 % contre 78 %), pour un coût réalisé inférieur de 19 %.
- **La prime à l'hectare est la moins chère en moyenne** et réduit la perte de l'agriculteur les années perdantes. Mais l'acheteur la paie même sans récolte (2 037 €/t l'année faible) et elle protège mal quand le prix du blé flambe : 37 % des contrats tenus en 2022, 74 % sur l'ensemble, sous la cible de 80 %.
- **Le prix unique coûte cher parce qu'il surpaie les bonnes années.** Son avantage : un coût par tonne connu d'avance pour l'acheteur.

### Le plancher indexé sur le prix du blé

Plancher = m × prix du blé de la récolte, m calibré sur les mêmes années simulées pour la même promesse : **m = 7,44**, 80 % des années gagnantes, coût moyen 1 519 €/t, 1 540 €/t l'année faible ; 82 % des contrats tenus en backtest.

| Prix du blé | 160 €/t | 200 €/t | 240 €/t | 280 €/t |
|---|---|---|---|---|
| Prix fixe nécessaire pour 8 années sur 10 | 1 070 €/t | 1 497 €/t | 1 922 €/t | 2 348 €/t |
| Plancher indexé, 7,44 × blé | 1 190 €/t | 1 488 €/t | 1 785 €/t | 2 083 €/t |

Un prix fixe ne tient que si le blé reste dans la moyenne ; le plancher indexé suit le blé et reste proche du prix nécessaire, mais l'acheteur porte alors le risque de prix : de 357 à 625 k€ d'achat pour 300 t selon le blé.

### Les mauvaises années, contrat par contrat (backtest strict)

| Contrat | 2020 | 2021 | 2022 | 2019–2025 |
|---|---|---|---|---|
| Unéal 2023, 900 €/t | 50 % | 50 % | 16 % | 57 % |
| NatUp 2023–2024, 900 / 700 / 600 | 44 % | 50 % | 5 % | 55 % |
| Proposition du dossier pilote | 61 % | 50 % | 16 % | 65 % |
| Prix unique calibré | 39 % | 56 % | 68 % | 78 % |
| Barème par tranches calibré | 39 % | 56 % | 68 % | 79 % |
| Prix de base et prime à l'hectare | 50 % | 50 % | 37 % | 74 % |

En 2020 et 2021, la lentille s'effondre : aucun contrat ne dépasse 61 %. En 2022, le blé flambe : les barèmes publiés tombent entre 5 et 16 %, les contrats calibrés en tiennent 68 %.

### Le budget de l'acheteur, pilote de 300 t

| Par campagne | Prix unique | Tranches | Indexé |
|---|---|---|---|
| Achat des lentilles (moyenne des années simulées) | 470 k€ | 385 k€ | 456 k€ |
| Tri, 180 €/t reçue, 333 t reçues | 60 k€ | 60 k€ | 60 k€ |
| Collecte, 5 €/t + 0,12 €/t/km, 2,4 km en moyenne | 2 k€ | 2 k€ | 2 k€ |
| **Total** | **532 k€, 1 773 €/t** | **447 k€, 1 489 €/t** | **517 k€, 1 725 €/t** |

Achat : **modèle**. Tri et collecte : **supposé**, conventions du jeu synthétique du pilote, sans devis (tri optique d'après Bio Hauts-de-France). Séchage, stockage et conditionnement exclus.

### Une offre pour les assureurs

Même distribution de récolte (Seine-et-Marne, rendement moyen simulé 1,59 t/ha), récolte valorisée à 1 567 €/t, prime pure hors chargements :

| Seuil garanti | Années avec sinistre | Prime pure | Capital garanti |
|---|---|---|---|
| 60 % du rendement moyen | 25 % | 162 €/ha | 1 495 €/ha |
| 70 % | 30 % | 231 €/ha | 1 744 €/ha |
| 80 % | 35 % | 312 €/ha | 1 993 €/ha |

## 8. Suivi en saison, prototype Sentinel-2

`pipeline/08_sentinel.py` rejoue la saison 2025 sur les 8 parcelles de lentille déclarées au RPG 2025 (au moins 4 ha) les plus proches du site : 148 images Sentinel-2 L2A du 1er mars au 15 août 2025, NDVI médian des pixels valides (couche SCL), parcelle réduite de 10 m. Entre 19 et 25 dates utiles par parcelle, sur 37 à 43 images.

| Indicateur | Valeur |
|---|---|
| NDVI au sol nu, début avril | 0,14 à 0,17 |
| Pic de végétation | 0,85 à 0,93, du 13 au 18 juin |
| Récolte visible | chute sous 0,3 fin juillet |
| Parcelles conformes au groupe en mai-juin | 6 sur 8 |
| Parcelles à surveiller (écart de −0,07 et −0,08) | 2 sur 8, sous le groupe en mai, au niveau mi-juin |

Les seuils de statut (−0,05 et −0,10 d'écart à la médiane du groupe) sont des choix de l'équipe : sans rendement à la parcelle, on ne sait pas encore quel écart de NDVI coûte combien de quintaux. Le prototype dit où aller voir, pas ce que la parcelle va produire.

**Réflectances vérifiées.** Les métadonnées Earth Search annoncent un décalage de +1 000 sur les valeurs, et certaines images sont marquées « non corrigées ». Pourtant, sur toutes les images vérifiées, le rouge descend sous 1 000 sur la végétation (292 en médiane sur une lentille en juin), ce qui serait impossible avec ce décalage. Le NDVI est donc calculé sur les valeurs brutes. Appliquer le décalage donnait des NDVI de 1,3 à 1,5, physiquement impossibles.

## 9. Le même moteur sur d'autres légumineuses

`pipeline/09_cultures.py` applique le même calcul au pois chiche, au haricot sec, au pois protéagineux et à la féverole : modèle quantile M1 appris sur les séries Agreste de chaque culture et la météo de ses départements, même modèle du blé que la lentille, mêmes 20 000 années. La lentille passe par le même chemin et retrouve exactement ses chiffres (1 567 €/t, tranches 1 635 / 750 / 650, 78 % en backtest). Le backtest regroupe les séries avec le seul passé, comme celui de la lentille (§4). Hypothèses propres à chaque culture : `data/cultures.yaml`, actualisées après la [revue filière du 31/10](REVUE_FILIERE_CULTURES.md), puis exports recalculés. Charges centrales : pois chiche 500, haricot sec irrigué 1 000, pois 450 et féverole 400 €/ha.

| Culture | Séries (couples) | Variabilité nationale | Rendement en Île-de-France | P\* Seine-et-Marne | Contrats tenus, prix fixe | Contrats tenus, indexé sur le blé |
|---|---|---|---|---|---|---|
| Lentille | 24 (294) | 0,20 | 17,5 q/ha, voisins | 1 567 €/t | 78 % | 82 % |
| Pois chiche | 18 (200) | 0,11 | 16,6 q/ha, voisins | 1 064 €/t | 65 % | 78 % |
| Haricot sec | 13 (156) | 0,10 | 19,1 q/ha, voisins | 2 185 €/t | 70 % | 89 % |
| Pois protéagineux | 83 (1 161) | 0,15 | 38,7 q/ha, mesuré | 427 €/t | 66 % | 82 % |
| Féverole | 69 (1 006) | 0,23 | 33,6 q/ha, mesuré | 462 €/t | 68 % | 82 % |

Backtest 2019–2025 sur les départements producteurs : 133, 100, 71, 493 et 446 cas. Le contrat indexé fixe le plancher à m\* fois le prix du blé de la récolte, m\* calibré sur les seules années passées ; pour 2026 en Seine-et-Marne, m\* vaut 7,44 (lentille), 5,03 (pois chiche), 10,55 (haricot), 1,99 (pois) et 2,17 (féverole).

**Lecture :**

- **L'indexation améliore le backtest de toutes les cultures, nettement pour les quatre autres.** Le prix fixe y tient 65–70 % des contrats, contre 78–89 % pour le plancher indexé ; pour la lentille, l'indexation fait passer de 78 à 82 %. Les échecs du prix fixe se concentrent en 2021–2022 (pois : 18 % puis 7 % de contrats tenus ; féverole : 37 % puis 2 % ; pois chiche : 8 % puis 13 %), ce qui motive le transfert du risque de prix du blé à l'acheteur. Ce constat ne classe pas toutes les cultures comme moins variables que la lentille : le coefficient national de la féverole est plus élevé.
- **Le pois chiche demande un plancher d'un tiers plus bas que la lentille** (1 064 contre 1 567 €/t), avec un rendement francilien emprunté comparable et une variabilité nationale plus faible. À 610 €/t, milieu du prix payé rapporté pour la filière Cavac standard 2025, il bat le blé dans 27,2 % des scénarios franciliens.
- **Le pois et la féverole restent loin du blé francilien** : 427 et 462 €/t pour 8 années sur 10, contre 200 à 260 €/t dans le référentiel de plan d'entreprise CRIT 2025. Au milieu de cette plage, 230 €/t, ils battent le blé dans 24,0 % et 23,4 % des scénarios. Ces fréquences sont des sorties du modèle, pas des statistiques nationales de rentabilité.
- **Le haricot sec irrigué** atteint 2 185 €/t avec 1 000 €/ha de charges, contre 1 779 €/t avec 700 €/ha. Le budget inclut 300 €/ha d'eau et d'énergie ; les rendements restent ceux des séries Agreste, sans distinguer l'irrigation. Au prix de scénario de 1 200 €/t, il bat le blé dans 58,9 % des simulations. Le repère administratif à 1 188 €/t qui étaye ce choix n'est pas une offre d'achat.
- Le barème par tranches, mis à l'échelle du rendement de chaque culture, coûte de 8 à 22 % de moins que le prix unique à protection égale.

## 10. Le Maillon vu du ciel, prototype Sentinel-2

`pipeline/10_maillon.py` cherche les légumineuses à graines d'une campagne sans attendre le RPG, publié l'année suivante. Zone de 24 × 24 km autour du site de collecte (tuile 31UDP), parcelles d'au moins 1 ha : 3 659 en 2025, dont 152 légumineuses (1 053 ha) ; 3 674 en 2024, dont 127 (915 ha). Images Sentinel-2 L2A du 1er avril au 31 juillet à moins de 95 % de nuages sur la tuile : 28 dates utiles en 2025, 17 en 2024. Pour chaque parcelle réduite de 10 m : NDVI et NDMI médians des pixels classés végétation ou sol nu, une image comptant si 60 % des pixels sont valides ; puis médiane par période de 10 jours, interpolée. Classifieur LightGBM à classes pondérées sur ces seules séries, seuil de probabilité 0,5. Chaque résultat est jugé sur des parcelles jamais vues à l'apprentissage ; la version « 10 juin » n'utilise aucune image postérieure.

| Ce que le modèle connaît de 2025 | Saison complète (31 juillet) : retrouvées / justes | Avant récolte (10 juin) : retrouvées / justes |
|---|---|---|
| **Un carré de 4 km sur cinq**, moyenne de cinq tirages | **73 % / 90 %** | **45 % / 69 %** |
| Quatre carrés sur cinq, validation croisée par carrés | 80 % / 92 % | 68 % / 68 % |
| Aucune parcelle : appris sur 2024 et le RPG 2024, protocole prévu | 8 % / 15 % | 15 % / 45 % |
| Aucune parcelle : même transfert, valeurs relatives à la zone, essai après coup | 35 % / 56 % | 11 % / 36 % |

« Retrouvées » : part des légumineuses du RPG 2025 signalées. « Justes » : part des parcelles signalées qui en sont. Avec un carré connu sur cinq, la part retrouvée va de 65 à 82 % selon le tirage en fin de saison, de 39 à 56 % au 10 juin.

**Lecture :**

- **Dans une campagne, quelques parcelles connues suffisent.** Un collecteur qui connaît les parcelles d'un carré sur cinq, celles de ses adhérents par exemple, repère en fin de saison près des trois quarts des légumineuses des autres carrés, et neuf signalements sur dix sont justes. Le RPG de la campagne n'arrive qu'un an plus tard. Au 10 juin, moins de la moitié des légumineuses sont retrouvées.
- **Les féveroles sont bien vues, les pois et les mélanges beaucoup moins.** Sur la carte de l'application (premier tirage, saison complète), 87 féveroles sur 106 sont retrouvées, contre 4 pois sur 15 : le carré connu ne contient que 6 pois. Les 3 mélanges de céréales et de légumineuses sont manqués. Les fausses alertes sont surtout des céréales de printemps (orge, avoine), du maïs et du trèfle.
- **D'une année sur l'autre, le modèle ne tient pas encore.** Appris sur 2024, il ne retrouve que 8 % des légumineuses de 2025. Deux causes sont mesurées. Le printemps 2024 a été très nuageux : 4 dates utiles par parcelle en médiane, contre 16 en 2025. La signature a aussi changé : en 2024, le NDVI médian du blé passe sous 0,5 le 27 juin, celui des féveroles d'hiver pas avant le 31 juillet ; en 2025, ils y passent les 22 et 26 juin. Après l'échec du protocole prévu, deux variantes ont été essayées. L'alignement des saisons sur le temps thermique (degrés-jours depuis le 1er janvier, NASA POWER) n'apporte rien : 6 à 9 % retrouvées, essai non conservé dans le pipeline. Les valeurs relatives à la zone le même jour portent la part retrouvée à 35 % en fin de saison, mais n'aident pas au 10 juin. Ces variantes ont été choisies après avoir vu 2025 : elles orientent la suite, elles ne prouvent rien.
- **Aucune lentille d'au moins 1 ha dans la zone en 2025** (2 en 2024) : le modèle repère la famille des légumineuses à graines, ici des féveroles et des pois, pas l'espèce.
- **Pour se passer des parcelles connues** : plusieurs campagnes d'apprentissage, une phénologie relative (levée et maturité comparées aux céréales voisines) et le radar Sentinel-1, insensible aux nuages.

## 11. Ce que ça veut dire

1. **Garantir 8 années sur 10 coûte plus du double du prix d'équilibre médian** (1 567 contre 715 €/t). Une moyenne sous-estime fortement le prix qu'il faut garantir : c'est le cœur du message.
2. **À la référence historique, la lentille ne gagne qu'une année sur deux.** C'est exactement le verrou que décrit le Track 3.
3. **Les contrats publiés sont plus bas** (Unéal : 900 €/t en 2023 ; NatUp : 900 / 700 / 600 €/t par tranche en 2023–2024). Dans notre modèle, ils protègent environ 6 années sur 10 face au blé francilien. **À protection égale, un barème par tranches coûte 18 % de moins qu'un prix unique** (19 % en backtest) : c'est la forme de contrat à proposer.
4. **Le prix plancher est très sensible au prix du blé.** Un contrat indexé sur le prix du blé (multiplicateur médian de 3,44, de 7,44 pour 8 années sur 10, soit 1 488 €/t avec un blé à 200 €/t) déplacerait ce risque vers l'acheteur sans rendre le contrat beaucoup moins cher.
5. **Le prix plancher est lui-même incertain** : seize années ne suffisent pas à cerner les mauvaises années. Les données de rendement des coopératives sont la première chose à obtenir en pilote.
6. **Le moteur est générique, la forme du contrat ne l'est pas** : barème par tranches pour la lentille, dont le risque vient surtout du rendement ; plancher indexé sur le blé pour le pois chiche, le haricot, le pois et la féverole, dont le risque vient surtout du prix du blé.
7. **La promesse se vérifie en backtest strict** : 78 % pour 80 % visés. Le chiffre est moins flatteur que les 87 % annoncés le matin du 31/10, mais il est mesuré sans aucune information des années testées.
8. **Le satellite peut mesurer l'effet du contrat un an avant le RPG, à condition de connaître quelques parcelles** : avec un carré de 4 km sur cinq, 73 % des légumineuses retrouvées et 90 % de signalements justes en fin de saison. Appris sur l'année précédente seule, il n'en retrouve que 8 %.
9. **Le contrat s'appuie sur la collecte qui existe** : 352 établissements du commerce de grains à moins de 15 km des parcelles franciliennes, dont un à 1,0 km en moyenne des parcelles du pilote. Les clients possibles sont nombreux : 142 coopératives agricoles et 28 unions de coopératives font le commerce des grains en France (Sirene).

## Historique

- Version 1 (hypothèses provisoires, prix du blé fixe, 39 séries comptées comme indépendantes) : 85 % de contrats tenus, P\* de 1 377 €/t en Seine-et-Marne.
- Version 2 (prix du blé mesuré et rééchantillonné, charges et aide sourcées) : 82 %, 1 435 €/t.
- Version 3 (30/10, séries estimées ensemble regroupées) : 86 %, 1 622 €/t, avec un intervalle de confiance sur P\*.
- Version 4 (31/10, hypothèses économiques revues, paiement sur les tonnes acceptées au tri, forfait de collecte, comparaison des contrats) : 87 %, 1 567 €/t. Le modèle et le protocole sont inchangés ; les hypothèses viennent de la revue documentée de [QUESTIONS.md](QUESTIONS.md), fixées avant le recalcul. Avec les hypothèses de la version 3, le pipeline actuel redonne 1 622 €/t.
- Version 4.1 (31/10, après-midi, backtest strict) : regroupement des séries en double refait chaque année avec le seul passé, à la suite de l'audit de la PR 1. Contrats tenus : 87 → 78 % (M1), 81 → 77 % (M0), 77 → 76 % (M2). Prix 2026 inchangés.
- Le Maillon vu du ciel (31/10, après-midi) : `10_maillon.py`, RPG 2024 et 2025, 51 images Sentinel-2 ; annexe « Vu du ciel » de l'application. Aucun chiffre existant ne change.
- Revue des autres cultures (31/10) : haricot 700 → 1 000 €/ha et pois 400 → 450 €/ha, prix de référence et provenances complétés. Recalcul de `09_cultures.py` : P\* haricot 1 779 → 2 185 €/t, pois 409 → 427 €/t. La totalité de l'objet lentille exporté est identique à la version précédente.
- Version 4.2, actuelle (31/10, soir) : contrat indexé, offre d'assurance et budget de l'acheteur exportés par `07_contrats.py` ; carte de France des prix ; sites de collecte existants et clients possibles (`11_sites.py`, Sirene). Aucun chiffre existant ne change.
