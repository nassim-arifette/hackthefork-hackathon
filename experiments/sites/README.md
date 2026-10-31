# Sites et approvisionnement : expérience reproductible

`python pipeline/benchmark_sites.py` reproduit `results.csv`, les parcelles sélectionnées et le manifeste SHA-256 des entrées. Aucun appel réseau ni entraînement de modèle n'est nécessaire.

## Deux décisions distinctes

- **Prix rendu uniforme fixé** : seuls les producteurs dont P* départ ferme + collecte nette est au plus égal au prix rendu sont retenus ; les parcelles admissibles les plus proches sont prises entières. L'objectif de localisation est la collecte moyenne. Le prix rendu contient déjà la collecte : coût acheteur = prix rendu + tri net, sans ajouter deux fois le transport. Une économie de collecte augmente ici la part revenant au producteur ; elle ne réduit pas un prix rendu maintenu fixe.
- **Prix départ ferme départementaux différenciés** : P* exporté pour chaque département + collecte + tri. Les parcelles sont prises entières par coût unitaire rendu croissant, sans plafond de prix. Ce régime commercial est une hypothèse supplémentaire ; il ne représente pas le contrat commun par tranches de l'application.

Pour chaque candidat, le même évaluateur calcule la sélection, la distance Haversine × détour, le volume et le coût. Le site courant est candidat ; à paramètres identiques, la recherche ne peut donc dégrader son objectif. La grille de 0,06° × 0,04° est affinée deux fois. Le résultat est le meilleur candidat testé pour cette règle d'approvisionnement, **pas une preuve d'optimum global** : la sélection de parcelles entières est gloutonne et la grille est heuristique.

## Régression de l'ancienne recherche

Ces lignes reproduisent l'ancienne assiette de collecte (sans division brut/net) et les anciens sites optimisés sans prix. Elles servent uniquement à constater le défaut corrigé.

| Cible | Prix rendu | Distance site courant | Distance ancien résultat | Collecte courante → ancien résultat |
|---|---|---|---|---|
| 300 t | 1500 €/t | 41,94 km | 51,15 km | 10,03 → 11,14 €/t |
| 300 t | 1600 €/t | 2,40 km | 0,70 km | 5,29 → 5,08 €/t |
| 5000 t | 1500 €/t | 49,98 km | 66,77 km | 11,00 → 13,01 €/t |
| 5000 t | 1600 €/t | 7,10 km | 4,70 km | 5,85 → 5,56 €/t |

## Recherche corrigée sous prix rendu fixé

L'ancien emplacement est aussi réévalué ci-dessous avec la même conversion brut/net que la recherche corrigée.

| Cible | Prix rendu | Collecte courante → ancien site → recherche | Tonnes attendues sélectionnées | Parcelles | Site théorique retenu |
|---|---|---|---|---|---|
| 300 t | 1500 €/t | 11,15 → 12,37 → 5,66 €/t | 305,0 t | 17 | 2.22829, 48.44568 |
| 300 t | 1600 €/t | 5,88 → 5,65 → 5,65 €/t | 306,2 t | 10 | 2.53429, 49.04568 |
| 5000 t | 1500 €/t | 12,22 → 14,46 → 6,23 €/t | 5 000,7 t | 539 | 1.77229, 48.89408 |
| 5000 t | 1600 €/t | 6,50 → 6,18 → 6,18 €/t | 5 002,2 t | 329 | 3.12829, 48.55168 |

## Coût rendu complet et sensibilités

Coût = règlement agricole au P* départemental + (forfait + coefficient × km routiers + tri) / fraction acceptée. Le budget porte sur toutes les tonnes des parcelles sélectionnées, y compris le surplus ; le dénominateur est ce même volume net sélectionné.

| Cible | Scénario | Coût courant | Coût recherche | Gain | Net sélectionné |
|---|---|---|---|---|---|
| 300 t | central | 1 661,15 €/t | 1 651,68 €/t | 9,47 €/t | 300,2 t |
| 300 t | loss_0 | 1 640,02 €/t | 1 631,11 €/t | 8,91 €/t | 303,9 t |
| 300 t | loss_20 | 1 687,55 €/t | 1 677,40 €/t | 10,15 €/t | 301,7 t |
| 300 t | transport_006 | 1 657,15 €/t | 1 651,62 €/t | 5,54 €/t | 300,2 t |
| 300 t | transport_020 | 1 664,88 €/t | 1 651,76 €/t | 13,12 €/t | 300,2 t |
| 300 t | sorting_100 | 1 572,26 €/t | 1 562,79 €/t | 9,47 €/t | 300,2 t |
| 300 t | sorting_300 | 1 794,48 €/t | 1 785,01 €/t | 9,47 €/t | 300,2 t |
| 5000 t | central | 1 662,20 €/t | 1 652,23 €/t | 9,98 €/t | 5 000,7 t |
| 5000 t | loss_0 | 1 640,88 €/t | 1 631,57 €/t | 9,32 €/t | 5 001,0 t |
| 5000 t | loss_20 | 1 688,86 €/t | 1 678,06 €/t | 10,80 €/t | 5 000,4 t |
| 5000 t | transport_006 | 1 657,86 €/t | 1 651,89 €/t | 5,96 €/t | 5 000,7 t |
| 5000 t | transport_020 | 1 666,66 €/t | 1 652,68 €/t | 13,99 €/t | 5 000,7 t |
| 5000 t | sorting_100 | 1 573,32 €/t | 1 563,34 €/t | 9,98 €/t | 5 000,7 t |
| 5000 t | sorting_300 | 1 795,54 €/t | 1 785,56 €/t | 9,98 €/t | 5 000,7 t |

## Hypothèses et limites

- Site de référence : (2.95, 48.55), fictif. Les points de grille ne constituent pas des silos ou sites de tri identifiés.
- Scénario central : perte 10%, collecte 5 €/t brute + 0.12 €/t brute/km, détour 1.3, tri 180 €/t brute. À 90 % de sortie, 180 €/t brute vaut 200 €/t nette. Le coefficient logistique comprend les retours ; aucune seconde multiplication par deux.
- Tri : [proxy optique en contexte bio](https://www.bio-hautsdefrance.org/systeme_bio/cultures-innovantes-de-nouvelles-opportunites-pour-les-grandes-cultures-bio/), repris du dossier synthétique ; ce n'est pas un devis industriel conventionnel.
- La sensibilité qualité transforme les tonnes exportées par (1−perte)/(1−perte à l'export). Elle conserve les P* exportés : **sensibilité logistique uniquement**, sans recalibration de la protection agricole. Les sensibilités transport et tri modifient un seul paramètre à la fois.
- Les volumes sont des espérances départementales, pas des livraisons garanties. Les hectares et identifiants des parcelles sont observés dans le RPG, mais leur disponibilité, agronomie et rotation ne sont pas vérifiées.
- Aucune capacité disponible de réception, tri ou stockage, aucun engagement commercial, coût fixe, devis routier, donnée de séchage ni récupération des écarts n'est connu ici. Ces postes ne sont pas inventés ; les résultats ne démontrent aucune faisabilité industrielle. Stockage, conditionnement, investissement et frais généraux sont exclus.
- Le pilote initial compare jusqu'à 300 t d'une collecte existante ; il ne crée pas un besoin attesté de site nouveau. Les 5 000 t sont une ambition de scénario.
- Les fichiers exportés de prix plancher restent la source de l'expérience. Le manifeste permet d'identifier exactement leur version ; toute modification de calibration impose de relancer ce script.
