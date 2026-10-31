# Résultats

Calculés par le pipeline (`make export`) le 31 octobre 2026, avec le scénario d'hypothèses de la version 4 (`data/hypotheses.yaml`). Les prix garantis exportés sont arrondis à l'euro supérieur ; les coefficients indexés, au centième supérieur. Les médianes et intervalles restent indicatifs. Les chiffres de l'application et du deck viennent de ces exports.

Ce document décrit le moteur historique de l'application et son backtest dit « legacy ». Ses regroupements Agreste sont établis sur toute la période 2010–2025 ; il ne constitue donc pas une validation strictement sans information future. Le benchmark multicultures reconstruit ces regroupements avant chaque année test et conserve une cohorte distincte, documentée dans [AUDIT_MULTILEGUMES.md](AUDIT_MULTILEGUMES.md).

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

## 3. Le scénario économique

| Paramètre | Valeur | Statut |
|---|---|---|
| Charges opérationnelles du blé | 700 €/ha | supposé, arrondi de 675 €/ha (Cerfrance Nord-Est Île-de-France, cité par Terres Inovia 2025) |
| Charges opérationnelles de la lentille | 500 €/ha | supposé, arrondi de 518 €/ha (guide lentille Terres Inovia 2023) |
| Aide couplée aux légumineuses | 105 €/ha | sourcé, montant indicatif 2026 (notice Telepac) |
| Bénéfice de rotation pour le blé suivant | 150 €/ha | supposé, effet précédent documenté par FiloLeg 2024 |
| Part de la récolte refusée au tri | 10 % | supposé |
| Collecte | 5 €/t brute de forfait + 0,12 €/t brute/km, distance × 1,3 | supposé |

**Le prix garanti est payé sur les tonnes acceptées au tri**, comme dans les contrats de collecte : un lot refusé (bruche, impuretés, calibre) n'est pas payé au prix garanti. Agreste mesure la récolte à l'arrivée à la ferme, avant ce tri : le modèle retire donc 10 % du rendement simulé, une seule fois. Le prix plancher s'entend départ ferme. La collecte est facturée sur le brut et divisée par 0,90 pour l'exprimer par tonne acceptée ; elle s'ajoute au prix ferme, ou se déduit une seule fois d'un prix déjà rendu.

## 4. Backtest historique 2019–2025 : entraînement glissant, regroupements sur période complète

Pour chaque année test, les modèles, les niveaux et la calibration sont estimés sur les seules années antérieures. Le prix plancher est fixé avec la météo et le prix du blé de ces années, puis jugé sur les rendements et le prix du blé réels. La sélection des séries conserve cependant les regroupements calculés sur 2010–2025 : les 133 cas ci-dessous sont ceux de cette cohorte historique.

| Année | Cas | Prix du blé | Couverture de l'intervalle à 80 % | Contrats tenus (M1) | Contrats tenus (choix automatique) |
|---|---|---|---|---|---|
| 2019 | 17 | 179 €/t | 94 % | 100 % | 82 % |
| 2020 | 18 | 191 €/t | 56 % | **50 %** | 44 % |
| 2021 | 18 | 238 €/t | 56 % | **61 %** | 61 % |
| 2022 | 19 | 338 €/t | 89 % | 95 % | 74 % |
| 2023 | 20 | 242 €/t | 95 % | 100 % | 100 % |
| 2024 | 20 | 216 €/t | 70 % | 100 % | 95 % |
| 2025 | 21 | 202 €/t | 90 % | 100 % | 95 % |
| **Ensemble** | **133** | | **79 %** | **87,2 %** pour 80 % visés | 79,7 % |

| Modèle | Perte pinball | Couverture à 80 % |
|---|---|---|
| M0, tendance seule | 0,1078 | 74 % |
| **M1, régression quantile météo (retenu a priori)** | 0,1103 | 79 % |
| M2, LightGBM quantile | 0,1014 | 84 % |
| Choix automatique sur validation interne | 0,1024 | 74 % |

Erreur médiane sur le rendement relatif d'une année : ±33 %.

### Ce que le modèle apporte : quatre façons de fixer le prix

| Façon de fixer le prix | Contrats tenus (80 % visés) | P\* 2026, Seine-et-Marne |
|---|---|---|
| Moyennes des années passées (référence naïve, sans modèle) | **29 %** | 742 €/t |
| Distribution calibrée, tendance seule, sans météo (M0) | 81 % | 2 932 €/t |
| **Régression quantile avec météo (M1, retenue)** | **87 %** | 1 568 €/t |
| LightGBM avec météo (M2) | 77 % | 1 001 €/t |

- Fixer le prix sur les moyennes ne tient que trois contrats sur dix : un prix moyen protège l'année moyenne, pas la mauvaise.
- Le modèle probabiliste calibré fait passer au-dessus de 80 %. La météo ajoute six points en backtest, soit 8 cas sur 133 : un écart modeste au regard de sept années test.
- Le prix 2026 change fortement d'un modèle à l'autre : c'est une incertitude de modèle, affichée à côté de l'incertitude statistique.
- Exploration non retenue (`pipeline/explore_regularisation.py`) : une régularisation choisie en validation interne est plus précise que la tendance seule, mais l'intervalle ne couvre plus qu'environ 71 % des cas.

### Lecture

- **La fiabilité visée est atteinte sur l'ensemble** (87 % pour 80 %), mais sur 7 années seulement. Les contrats cèdent en **2020 et 2021**, deux effondrements de la lentille absents de l'entraînement.
- **La calibration fonctionne** : 79 % des récoltes tombent dans l'intervalle à 80 %, contre 74 % pour la tendance seule.
- **La météo n'améliore pas la précision du modèle linéaire** (pinball −2 % face à la tendance). LightGBM fait mieux (+6 %), mais il n'a pas été choisi a priori. Le choix automatique sur validation interne est plus précis mais moins bien calibré, et tient moins de contrats.
- **Le rendement d'une année reste difficile à prévoir** (±33 %). C'est la raison d'être d'un prix calibré sur le risque plutôt que sur une prévision.

## 5. Prix plancher, campagne 2026

| Département | P\* (8 années sur 10) | Prix d'équilibre médian | Rendement lentille moyen simulé | Dont accepté au tri | Rendement d'une année sur dix |
|---|---|---|---|---|---|
| Seine-et-Marne | 1 568 €/t | 715 €/t | 1,59 t/ha | 1,43 t/ha | 0,48 t/ha |
| Yvelines | 1 446 €/t | 674 €/t | 1,61 t/ha | 1,45 t/ha | 0,50 t/ha |
| Essonne | 1 450 €/t | 674 €/t | 1,60 t/ha | 1,44 t/ha | 0,50 t/ha |
| Val-d'Oise | 1 541 €/t | 718 €/t | 1,61 t/ha | 1,45 t/ha | 0,50 t/ha |

**Incertitude sur P\*** (Seine-et-Marne, rééchantillonnage des années, 40 tirages) : de 1 099 à 2 877 €/t à 80 %, médiane 1 742 €/t.

### Le prix de la sécurité (Seine-et-Marne)

| Années gagnantes visées | 5 sur 10 | 6 | 7 | 8 | 9 | 9,5 |
|---|---|---|---|---|---|---|
| P\* | 715 | 872 | 1 133 | 1 568 | 2 633 | 4 398 €/t |

À la référence historique 2012–2016 (milieu de la fourchette, 715 €/t), la lentille rapporte au moins autant que le blé **5 années sur 10**. À 900 €/t, 6,1 années sur 10 ; à 1 000 €/t, 6,5.

### Sensibilités (Seine-et-Marne)

| Hypothèse | P\* |
|---|---|
| Prix du blé fixé de 160 à 280 €/t | 1 070 à 2 348 €/t |
| Part refusée au tri de 0 à 20 % | 1 411 à 1 764 €/t |
| Bénéfice de rotation de 200 à 0 €/ha | 1 500 à 1 773 €/t |
| Charges du blé de 800 à 600 €/ha | 1 432 à 1 703 €/t |
| Charges de la lentille de 400 à 600 €/ha | 1 432 à 1 703 €/t |
| Aide couplée à 122, 105 ou 0 €/ha | 1 547, 1 568 ou 1 710 €/t |
| Hypothèses de la version 3 rejouées par le moteur actuel (charges 440 / 280 €/ha, aide 122 €/ha, sans rotation ni refus au tri) | 1 623 €/t |

### Là où la lentille tient le mieux

| Département | P\* |
|---|---|
| Pyrénées-Orientales | 559 €/t |
| Hérault | 843 €/t |
| Gard | 901 €/t |
| Indre | 1 115 €/t |
| Cher | 1 183 €/t |

Le prix plancher baisse là où le blé rend peu (Pyrénées-Orientales : 33 q/ha) ou là où la lentille rend bien face au blé (Indre : 18 q/ha de lentille pour 62 q/ha de blé). Ce classement applique partout les charges franciliennes : il compare des rendements, pas des économies locales.

## 6. Le contrat de démonstration

**Contrat proposé : barème par tranches, 1 635 €/t pour la première tonne acceptée par hectare, 750 €/t pour la deuxième, 650 €/t au-delà**, départ ferme, sur trois campagnes. Il protège autant qu'un prix unique de 1 568 €/t pour 18 % de moins en moyenne (§7). La lettre d'accompagnement reprend ce barème.

Pour la carte et les volumes, l'application présente un scénario séparé à prix unique rendu au site de collecte : **1 600 €/t**. Une parcelle bascule si ce prix, moins la collecte par tonne acceptée, couvre le P\* de son département. Le tableau ci-dessous correspond au site fictif initial, en mode « Collecte » ; les parcelles sont prises entières, y compris le surplus de volume. Aucun volume n'est engagé par le barème de démonstration.

| | Pilote | Ambition de bassin |
|---|---|---|
| Tonnes acceptées visées | 300 t | 5 000 t |
| Tonnes acceptées attendues sélectionnées | 309,7 t | 5 011,6 t |
| Surface sélectionnée | 216,42 ha | 3 501,83 ha |
| Parcelles éligibles les plus proches du site | 28, jusqu'à 3,23 km | 260, jusqu'à 9,76 km |
| Part des importations 2025 | 0,8 % | 12,7 % |
| Protéines potentielles (25 % des tonnes sélectionnées) | 77 t | 1 253 t |
| Azote minéral non apporté (180 kg N/ha de blé remplacé) | 39 t N | 630 t N |
| Émissions directes de N₂O évitées (0,755 t CO₂e/ha) | 163 t CO₂e | 2 644 t CO₂e |

Les distances sont routières (vol d'oiseau × 1,3). Les compteurs d'impact excluent la fabrication des engrais et les émissions indirectes.

### Rejouer deux années à 1 600 €/t (Seine-et-Marne)

| Année | Marge lentille sous contrat | Marge blé | Parcelles qui tiennent |
|---|---|---|---|
| 2016, le blé perd 53 % | 1 743 €/ha | −84 €/ha | toutes |
| 2020, la lentille perd 38 % | 1 171 €/ha | 771 €/ha | toutes |

La marge de référence du 77 déduit 11,17 €/t de collecte moyenne pondérée par les tonnes de ses parcelles de blé vers le site initial. La carte applique la distance propre à chaque parcelle.

### Déplacer le site de collecte

Un clic sur la carte déplace le site ; distances, parcelles retenues et coût de collecte se recalculent dans le navigateur, avec les formules du pipeline. La recherche du meilleur emplacement parcourt une grille de points, affinée deux fois.

| Volume | Site du scénario | Meilleur point de la grille |
|---|---|---|
| Pilote, 300 t | 2,40 km en moyenne, 5,88 €/t acceptée de collecte | 0,70 km, 5,65 €/t |
| Ambition, 5 000 t | 7,10 km, 6,50 €/t acceptée | 4,70 km, 6,18 €/t |

À prix rendu fixe, le gain de collecte reste de quelques dixièmes d'euro par tonne et revient au producteur ; le coût d'achat rendu reste fixé. Le mode distinct « Coût rendu » autorise des prix ferme départementaux différents et minimise règlement producteur, collecte et tri. Le tri supposé de 180 €/t brute vaut 200 €/t acceptée : avec un prix rendu fixé à 1 600 €/t, le coût rendu et trié est donc 1 800 €/t. Ces recherches sont des grilles heuristiques, sans capacité industrielle ni disponibilité des producteurs vérifiées. Détails et sensibilités : [expérience sites](../experiments/sites/README.md).

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
| Prix unique : 1 568 €/t | 1 568 €/t | 1 568 €/t | 581 €/ha | 87 % | référence |
| **Tranches : 1 635 €/t la première tonne par hectare, puis 750 et 650** | **1 283 €/t (−18 %)** | 1 635 €/t | 568 €/ha | **87 %** | **−22 %** |
| Prix de base 900 €/t et prime de 491 €/ha | 1 243 €/t (−21 %) | 2 037 €/t | 426 €/ha | 79 % | −49 % |

Dans le backtest, chaque forme est recalibrée chaque année sur les seules années passées, comme le prix unique. Les coûts réalisés portent sur les départements producteurs, d'où la comparaison en écart au prix unique.

**Lecture :**

- **Le barème par tranches protège autant que le prix unique pour nettement moins cher.** Il paie cher les premières tonnes, celles qui manquent les mauvaises années, et moins le surplus des bonnes. Même taux de contrats tenus en backtest (87 %), coût réalisé inférieur de 22 %.
- **La prime à l'hectare est la moins chère en moyenne** et réduit la perte de l'agriculteur les années perdantes. Mais l'acheteur la paie même sans récolte (2 037 €/t l'année faible) et elle protège mal quand le prix du blé flambe : 37 % des contrats tenus en 2022, 79 % sur l'ensemble, sous la cible de 80 %.
- **Le prix unique coûte cher parce qu'il surpaie les bonnes années.** Son avantage : un coût par tonne connu d'avance pour l'acheteur.

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

`pipeline/09_cultures.py` applique le même calcul au pois chiche, au haricot sec, au pois protéagineux et à la féverole : modèle quantile M1 appris sur les séries Agreste de chaque culture et la météo de ses départements, même modèle du blé que la lentille, mêmes 20 000 années. La lentille passe par le même chemin et retrouve ses chiffres (1 568 €/t, tranches 1 635 / 750 / 650, 87,2 % en backtest). Hypothèses propres à chaque culture : `data/cultures.yaml`, actualisées après la [revue filière du 31/10, PR3](REVUE_FILIERE_CULTURES.md). Charges centrales : pois chiche 500, haricot sec irrigué 1 000, pois 450 et féverole 400 €/ha. Les exports ci-dessous incluent aussi les arrondis contractuels au plafond.

| Culture | Séries (couples) | Variabilité nationale | Rendement en Île-de-France | P\* Seine-et-Marne | Contrats tenus, prix fixe | Contrats tenus, indexé sur le blé |
|---|---|---|---|---|---|---|
| Lentille | 24 (294) | 0,20 | 17,5 q/ha, voisins | 1 568 €/t | 87,2 % | 86,5 % |
| Pois chiche | 18 (200) | 0,11 | 16,6 q/ha, voisins | 1 065 €/t | 70,0 % | 83,0 % |
| Haricot sec | 13 (156) | 0,10 | 19,1 q/ha, voisins | 2 186 €/t | 71,8 % | 87,3 % |
| Pois protéagineux | 83 (1 161) | 0,15 | 38,7 q/ha, mesuré | 427 €/t | 65,5 % | 82,4 % |
| Féverole | 69 (1 006) | 0,23 | 33,6 q/ha, mesuré | 462 €/t | 67,5 % | 82,3 % |

Backtest historique 2019–2025 sur les départements producteurs, avec regroupements Agreste sur période complète : 133, 100, 71, 493 et 446 cas. Le contrat indexé fixe avant campagne le multiplicateur sans unité m\*, appliqué au prix du blé à la récolte ; le prix payé en €/t reste donc variable. Pour 2026 en Seine-et-Marne, m\* vaut 7,44 (lentille), 5,03 (pois chiche), 10,55 (haricot), 2,00 (pois) et 2,18 (féverole).

**Lecture :**

- **L'indexation améliore le backtest des quatre autres cultures.** Avec les budgets PR3, le prix fixe tient 65,5–71,8 % des contrats, contre 82,3–87,3 % pour le plancher indexé. Pour la lentille, les taux sont 87,2 % et 86,5 %. Les échecs du prix fixe se concentrent notamment en 2021–2022 (pois : 18 % puis 7 % ; féverole : 37 % puis 2 %), ce qui motive le transfert du risque de prix du blé à l'acheteur. Ce constat ne classe pas toutes les cultures comme moins variables que la lentille : le coefficient national de la féverole est plus élevé. Il ne démontre pas une amélioration du seul modèle de rendement.
- **Le pois chiche demande un plancher d'un tiers plus bas que la lentille** (1 065 contre 1 568 €/t), avec un rendement francilien emprunté comparable et une variabilité nationale plus faible. À 610 €/t, milieu du prix payé rapporté pour la filière Cavac standard 2025, il bat le blé dans 27,2 % des scénarios franciliens.
- **Le pois et la féverole restent loin du blé francilien** : 427 et 462 €/t pour 8 années sur 10, contre 200 à 260 €/t dans le référentiel de plan d'entreprise CRIT 2025. Au milieu de cette plage, 230 €/t, ils battent le blé dans 24,0 % et 23,4 % des scénarios. Ces fréquences sont des sorties du modèle, pas des statistiques nationales de rentabilité.
- **Le haricot sec irrigué** atteint 2 186 €/t avec 1 000 €/ha de charges, contre 1 779 €/t avec 700 €/ha. Le budget inclut 300 €/ha d'eau et d'énergie ; les rendements restent ceux des séries Agreste, sans distinguer l'irrigation. Au prix de scénario de 1 200 €/t, il bat le blé dans 58,9 % des simulations. Le repère administratif à 1 188 €/t qui étaye ce choix n'est pas une offre d'achat.
- Le barème par tranches, mis à l'échelle du rendement de chaque culture, coûte de 8 à 22 % de moins que le prix unique à protection égale dans les simulations 2026. Le backtest historique multicultures ne valide pas ces tranches ; le nouveau benchmark les évalue séparément.

La comparaison avec l'ancien scénario doit conserver le changement de budget : avec 400 €/ha de charges, le pois indexé tenait 79,7 % des cas, sous 80 % ; avec les 450 €/ha de PR3 et les prix recalibrés, il tient 82,4 %. La hausse de ce score n'est pas un gain du modèle de rendement.

## 10. Ce que ça veut dire

1. **Garantir 8 années sur 10 coûte plus du double du prix d'équilibre médian** (1 568 contre 715 €/t). Une moyenne sous-estime fortement le prix qu'il faut garantir : c'est le cœur du message.
2. **À la référence historique, la lentille ne gagne qu'une année sur deux.** C'est exactement le verrou que décrit le Track 3.
3. **Les contrats publiés sont plus bas** (Unéal : 900 €/t en 2023 ; NatUp : 900 / 700 / 600 €/t par tranche en 2023–2024). Dans notre modèle, ils protègent environ 6 années sur 10 face au blé francilien. **À protection égale, un barème par tranches coûte 18 % de moins qu'un prix unique** (22 % en backtest) : c'est la forme de contrat à proposer.
4. **Le prix plancher est très sensible au prix du blé.** Un contrat indexé sur le prix du blé (multiplicateur médian de 3,44, de 7,44 pour 8 années sur 10, soit 1 488 €/t avec un blé à 200 €/t) déplacerait ce risque vers l'acheteur sans rendre le contrat beaucoup moins cher.
5. **Le prix plancher est lui-même incertain** : seize années ne suffisent pas à cerner les mauvaises années. Les données de rendement des coopératives sont la première chose à obtenir en pilote.
6. **La forme du contrat change le risque transféré** : l'indexation améliore plusieurs résultats historiques. Les budgets PR3 changent également les prix recalibrés du haricot et du pois ; une sélection de produit doit être évaluée dans le temps, séparément des gains du modèle de rendement et à hypothèses économiques constantes.

## Historique

- Version 1 (hypothèses provisoires, prix du blé fixe, 39 séries comptées comme indépendantes) : 85 % de contrats tenus, P\* de 1 377 €/t en Seine-et-Marne.
- Version 2 (prix du blé mesuré et rééchantillonné, charges et aide sourcées) : 82 %, 1 435 €/t.
- Version 3 (30/10, séries estimées ensemble regroupées) : 86 %, 1 622 €/t, avec un intervalle de confiance sur P\*.
- Version 4, actuelle (31/10, hypothèses économiques revues, paiement sur les tonnes acceptées au tri, forfait de collecte, comparaison des contrats) : 87,2 % sur la cohorte historique, 1 568 €/t après correction de l'arrondi contractuel au plafond. Les hypothèses viennent de la revue documentée de [QUESTIONS.md](QUESTIONS.md). Avec les hypothèses de la version 3, le pipeline actuel exporte 1 623 €/t au plafond ; le chiffre publié à l'époque pour la version 3 reste 1 622 €/t.
- Revue des autres cultures (31/10, PR3) : haricot 700 → 1 000 €/ha et pois 400 → 450 €/ha, prix de référence et provenances complétés. Après recalcul et arrondi au plafond, P\* haricot 1 779 → 2 186 €/t, pois 409 → 427 €/t. Les valeurs économiques de la lentille, du pois chiche et de la féverole sont inchangées ; leurs métadonnées et références peuvent être enrichies sans changer le besoin de paiement.
