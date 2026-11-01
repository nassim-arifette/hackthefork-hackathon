# Le Contrat qui Tient : le dossier complet

Tout le projet dans un seul document, pour le connaître en détail : le problème, la solution, le modèle, les données, les résultats, le business, la concurrence, l'impact, les limites. Les chiffres viennent des exports du pipeline (version 4.3 du 31/10/2026, [RESULTATS.md](RESULTATS.md)) ou des sources de [SOURCES.md](SOURCES.md). Chaque chiffre porte un statut :

- **mesuré** : donnée observée (Agreste, Eurostat, IGN, NASA, Sentinel-2, Sirene) ou résultat de test sur des données réelles ;
- **sourcé** : valeur publiée par un tiers (guide technique, contrat publié, notice officielle) ;
- **supposé** : choix de l'équipe, documenté dans `data/hypotheses.yaml` avec sa sensibilité ;
- **synthétique** : donnée fictive construite pour la démonstration et annoncée comme telle ;
- **modèle** : sortie du calcul.

Hack the Fork Paris 2026, Track 3 : « souveraineté protéique : des champs français aux protéines de demain ». Équipe : Nassim Arifette et Youssef Mir.

---

## 1. En trente secondes

Près d'une lentille sur deux mangée en France est importée. Les agriculteurs pourraient en produire plus, mais la lentille est un pari : sa récolte varie deux fois plus que celle du blé, et une mauvaise année efface la marge. Une coopérative peut retirer ce risque en garantissant un prix minimum avant les semis, mais personne ne sait calculer ce prix sur le risque : aujourd'hui, il se fixe à l'expérience.

**Le Contrat qui Tient** calcule, pour la responsable filière d'une coopérative, le prix minimum qui garantit à l'agriculteur de gagner au moins autant qu'avec le blé 8 années sur 10, propose la forme de contrat la moins chère pour cette protection, et montre quelles parcelles de blé basculent à ce prix.

| Chiffre | Valeur | Statut |
|---|---|---|
| Lentilles importées en 2025 | 39 371 t, 46 % de la consommation apparente | mesuré |
| Variabilité du rendement national, lentille / blé | 0,20 / 0,09 | mesuré |
| Prix minimum pour 8 années sur 10, Seine-et-Marne | 1 567 €/t | modèle |
| Prix payé par Unéal en 2023 | 900 €/t, qui ne protège que 6 années sur 10 | sourcé, modèle |
| Contrats tenus sur des années jamais vues, 2019–2025 | 78 % pour 80 % promis, contre 29 % avec un prix fixé sur les moyennes | mesuré |
| Barème par tranches 1 635 / 750 / 650 €/t | même protection pour 18 % de moins | modèle |
| Pilote de 300 t | 28 parcelles, 216 ha | modèle |
| Clients possibles | 142 coopératives agricoles et 28 unions du commerce de grains | mesuré |

---

## 2. Le problème

### 2.1 Le constat

| Indicateur, 2025 | Valeur | Statut, source |
|---|---|---|
| Importations de lentilles | 39 371 t | mesuré, Eurostat Comext (NC8 0713 40) |
| Provenance | Canada 45 %, Belgique 37 %, Turquie 6 %, Portugal 3 %, États-Unis 2 % | mesuré, Comext ; la Belgique est un pays d'expédition, qui produit peu |
| Exportations | 5 032 t | mesuré, Comext |
| Production française | 51 558 t (provisoire), sur 33 927 ha | mesuré, Agreste SAA |
| Consommation apparente | 85 897 t, dont 46 % importées (production + importations − exportations, stocks non comptés) | mesuré, calcul |
| Prix des lentilles importées | 1 069 €/t (Canada : 960 €/t) ; 819 €/t en 2020, 1 250 €/t en 2022 (+53 %) | mesuré, Comext (valeur à la frontière / tonnes) |

Les importations restent entre 24 000 et 42 000 t par an depuis 1997 (Comext). Les légumineuses occupent environ 4 % des terres agricoles françaises, avec un objectif de doublement d'ici 2030 (sourcé, guide participant) ; Terres Univia vise 1 million d'hectares (sourcé).

### 2.2 Le verrou : le risque de revenu

- La lentille varie deux fois plus que le blé : coefficient de variation du rendement national 2010–2025 de **0,20**, contre **0,09** (mesuré, Agreste).
- En **2020**, le rendement national est tombé à 8,2 q/ha, **38 % sous la moyenne 2015–2019** ; 2021 n'a pas fait mieux, 8,6 q/ha (mesuré).
- Aux prix observés de 2012–2016 (650 à 779 €/t, milieu 715 €/t, Eurostat), la lentille rapporte au moins autant que le blé francilien **5 années sur 10** ; à 900 €/t, 6 années sur 10 (modèle).

Une seule mauvaise année peut effacer plusieurs années de marge. L'agriculteur reste au blé, qu'il connaît : c'est le verrou que nomme le Track 3, la peur de perdre du revenu.

### 2.3 La solution qui existe, et sa faille

Les contrats à prix minimum existent déjà (sourcé) :

- **Unéal** valorise les lentilles à 900 €/t (décembre 2023), en partenariat avec Vivien Paille ;
- **NatUp** paie 900 €/t la première tonne par hectare, 700 la deuxième, 600 au-delà (récoltes 2023 et 2024), puis annonce en 2025 un contrat triennal à 1 000 € la première tonne par hectare, pour 558 t collectées ;
- **Qualisol** propose des contrats pluriannuels à prix minimum en légumes secs.

Mais personne ne dit comment ce prix est calculé. **Trop bas**, l'agriculteur gagne moins qu'en blé une mauvaise année, ne renouvelle pas, et la filière perd ses surfaces. **Trop haut**, la coopérative paie trop et ne peut plus revendre face aux importations. Fixé sur des moyennes, un prix ne tient que **29 %** des contrats sur des années jamais vues (mesuré, backtest) : une moyenne protège l'année moyenne, pas la mauvaise.

---

## 3. L'utilisateur, la filière et la décision

### 3.1 La filière, maillon par maillon

| Maillon | Rôle |
|---|---|
| **Agriculteur** | choisit chaque automne ce qu'il sème ; compare la lentille à son blé |
| **Coopérative agricole** | entreprise qui appartient aux agriculteurs adhérents : elle collecte leurs récoltes, les trie, les stocke et les revend ; elle signe les contrats de production |
| **Négociant** | même métier que la coopérative, mais entreprise privée qui achète aux agriculteurs |
| **Conditionneur** | nettoie, calibre et ensache les légumes secs pour la vente (par exemple Vivien Paille, partenaire d'Unéal, ou Lunor, débouché de NatUp) |
| **Distributeur, restauration** | magasins, cantines, industriels qui achètent les sachets ou les lentilles en vrac |

### 3.2 L'utilisatrice et sa décision

- **Utilisatrice** : la responsable filière d'une coopérative (ou d'un conditionneur) qui développe les légumes secs pour l'alimentation humaine.
- **Décision**, avant les semis : « À quel prix minimum proposer un contrat lentille de trois campagnes, et à quelles parcelles, pour sécuriser X tonnes sans faire prendre à l'agriculteur plus de risque qu'avec le blé ? »
- **Bénéficiaire indirect** : l'agriculteur, dont le revenu est protégé.

### 3.3 Pourquoi une coopérative veut ce contrat

- Ses clients (conditionneurs, marques, restauration collective) demandent de l'origine France traçable ; elle doit sécuriser des volumes sur plusieurs campagnes.
- Diversifier les rotations de ses adhérents : la lentille fixe l'azote de l'air et améliore le blé suivant (+7 q/ha, −55 kg N/ha d'après FiloLeg / Agro-Transfert, sourcé).
- Les aides publiques poussent dans ce sens : aide couplée aux légumineuses à graines de 105 €/ha indicatifs en 2026 (sourcé, Telepac), plan protéines.
- Le risque est de son côté : un prix trop haut lui coûte sa marge (20 €/t de trop sur 5 000 t, c'est 100 k€ par campagne, calcul illustratif), un prix trop bas lui coûte ses surfaces.

---

## 4. La solution

### 4.1 Ce que fait l'outil

Une seule question : **quel prix minimum garantir pour que l'agriculteur gagne au moins autant qu'en blé 8 années sur 10 ?**

1. **Il apprend** comment la météo déplace la distribution des rendements de la lentille et du blé (16 ans d'Agreste et de météo NASA POWER).
2. **Il simule** 20 000 années possibles, en rejouant des années réelles de météo et de prix du blé.
3. **Il en déduit le prix** qui fait gagner la lentille dans 80 % des années simulées, et la forme de contrat la moins chère pour cette protection.
4. **Il cible** les parcelles de blé qui basculent à ce prix, au plus près du site de collecte.
5. **Il le prouve** sur des années que le modèle n'a jamais vues (backtest strict 2019–2025).

La responsable filière obtient un prix, un barème, la carte des parcelles, la courbe d'offre en tonnes, son budget, l'écart avec l'import et une lettre de proposition au producteur.

### 4.2 L'application

En ligne : https://main.d1lkeu0ybo1cz4.amplifyapp.com/ ; hors ligne : `app/dist-single/index.html`, un seul fichier, identique.

**Le parcours, six écrans** (`Espace` pour avancer) :

1. **Le constat** : dix bols de lentilles dont cinq importés, les cargos qui arrivent, la provenance.
2. **Le pari** : les récoltes de blé et de lentille année par année ; 20 762 parcelles de blé en Île-de-France.
3. **Le contrat** : la filière animée ; la carte descend vers le site de collecte.
4. **Le prix** : le prix monte depuis 900 €/t, les parcelles proches basculent, les camions livrent 300 t ; `←` `→` font varier le prix.
5. **La preuve** : la carte de France rejoue 2019–2025 ; dix contrats sans modèle, dix avec.
6. **L'impact** : les compteurs du bassin de 5 000 t ; `F` montre la carte de France des prix.

**Six annexes** (menu « Annexes ») : le prix en détail ; deux mauvaises années rejouées (2016, 2020) ; le test en détail ; la proposition de contrat (barème, lettre, comparaison, sites existants, autres légumineuses) ; la saison vue par satellite ; Vu du ciel.

**Le simulateur** (bouton « Simulateur », adresse `#simulateur`) : la coopérative y entre ses charges de blé et de lentille, l'aide, le bénéfice de rotation, sa part refusée au tri, son coût de tri, la protection voulue, son volume et son prix de revente. Elle obtient en direct le prix, le barème calibré, ce que gagne l'agriculteur, ses parcelles, son budget et l'écart avec l'import, recalculés sur les mêmes 20 000 années que le pipeline. Avec les hypothèses du dossier, il retrouve exactement 1 567 €/t et 1 635 €/t (contrôlé à l'export et dans l'application). Un clic sur la carte, ou sur un site existant, déplace la collecte.

---

## 5. Le modèle, pas à pas

### 5.1 Ce qu'il apprend

- **Cible** : le rendement départemental Agreste 2010–2025, en **rendement relatif** (rendement de l'année / rendement moyen du département) : les départements deviennent comparables, et le modèle se transfère à un département qui produit peu.
- **Lentille** : 39 départements mesurés, mais Agreste estime souvent la lentille au niveau régional ; les séries identiques sont regroupées, il reste **24 séries indépendantes, 294 couples département × année**. **Blé** : 1 439 couples sur 90 séries.
- **Île-de-France** : elle produit peu de lentilles ; le niveau de rendement (17,5 q/ha) est emprunté aux départements producteurs voisins (Aube, Marne, Yonne, Eure-et-Loir, Loiret).
- **Météo** : NASA POWER journalier, 43 départements, six variables agronomiques, en anomalies (écart à la climatologie 2010–2018) : pluie de mars à juillet, pluie d'avril à juin, jours à plus de 30 °C en juin–juillet, jours de gel tardif, pluie à la récolte, température maximale moyenne de mai à juillet. Plus une tendance.

### 5.2 Trois modèles comparés

| Modèle | Rôle | Perte pinball | Couverture de l'intervalle à 80 % | Contrats tenus | P\* 2026, Seine-et-Marne |
|---|---|---|---|---|---|
| Prix fixé sur les moyennes, sans modèle | référence naïve | — | — | 29 % | 742 €/t |
| M0, tendance seule | référence à battre | 0,1094 | 70 % | 77 % | 2 932 €/t |
| **M1, régression quantile sur la météo** | **retenu, choisi avant le backtest** | 0,1105 | 79 % | **78 %** | **1 567 €/t** |
| M2, LightGBM quantile | challenger | 0,1020 | 77 % | 76 % | 1 000 €/t |

- **Régression quantile** : au lieu de prédire le rendement moyen, le modèle prédit trois quantiles (10 %, 50 %, 90 %) : la mauvaise année, l'année médiane, la bonne année. Sept coefficients par quantile, lisibles : au quantile 50 %, une chaleur de mai à juillet supérieure d'un écart-type réduit le rendement relatif de la lentille de 0,078.
- **Pourquoi pas LightGBM, plus précis** : il prédit mieux l'année moyenne mais sous-estime les mauvaises ; ses contrats tiennent moins souvent que promis. Pour protéger un revenu, la justesse de la queue basse compte plus que la précision moyenne. La météo pèse 61 % de ce que LightGBM a appris.
- **Ce qu'apporte la météo** : peu de précision au modèle linéaire (perte pinball −1 % face à la tendance), mais un prix presque deux fois plus juste à protection comparable (1 567 contre 2 932 €/t).

### 5.3 La calibration conforme

Les intervalles bruts sont souvent trop étroits. La calibration conforme (*conformalized quantile regression*) mesure, sur les trois dernières années d'entraînement, de combien il faut élargir l'intervalle pour qu'il contienne vraiment 80 % des récoltes réelles (0,08 en rendement relatif pour la lentille). Résultat en backtest : **79 % des récoltes réelles tombent dans l'intervalle à 80 %**.

### 5.4 La simulation de 20 000 années

Pour chaque scénario : on tire une année réelle entre 2010 et 2025 (tendance projetée en 2026), **la même pour le blé et la lentille**, avec **le prix du blé de cette année-là**. On tire les deux rendements dans leurs distributions conditionnées à la météo de l'année, puis on calcule les deux marges :

```
marge blé       = prix du blé × rendement blé − charges du blé
marge lentille  = P × rendement lentille × (1 − part refusée au tri) − charges de la lentille + aide + bénéfice de rotation
```

Rejouer des années entières conserve les liens réels entre météo, rendements et prix du blé, flambée de 2022 comprise (338 €/t).

### 5.5 Le prix plancher P\*

Dans chaque scénario, on calcule le **prix d'équilibre** : le prix qui rend la marge de la lentille égale à celle du blé. **P\* est le quantile 80 % de ces prix d'équilibre** : le plus petit prix qui suffit dans 80 % des années simulées. Il s'entend départ ferme, payé sur les tonnes acceptées au tri (Agreste mesure la récolte avant le tri ; on retire 10 %, une seule fois).

Pour la carte, l'outil raisonne en prix livré au site de collecte : 1 600 €/t. Une parcelle bascule si ce prix, moins la collecte (5 €/t de forfait + 0,12 €/t/km, distance à vol d'oiseau × 1,3), couvre le P\* de son département. Les parcelles les plus proches sont retenues jusqu'au volume visé.

### 5.6 Les contrats

- **Prix unique** : P\* sur toutes les tonnes. Simple, mais il surpaie les bonnes années.
- **Barème par tranches** : la première tranche est calibrée (par dichotomie) pour donner la même protection, les suivantes sont fixées (750 et 650 €/t). Il paie cher la première tonne par hectare, celle qui manque les mauvaises années.
- **Plancher indexé** : un multiple du prix du blé de la récolte (m = 7,44 pour 8 années sur 10). L'acheteur porte alors le risque du prix du blé.
- **Prime à l'hectare** : un prix de base de 900 €/t plus une prime de 491 €/ha, versée même sans récolte.

### 5.7 Le backtest strict

Pour chaque année de 2019 à 2025 : regroupement des séries, modèles, niveaux et calibration sont estimés sur les seules années précédentes ; le prix est fixé avec la météo et le prix du blé de ces années ; puis on regarde si le contrat a tenu avec la vraie récolte et le vrai prix du blé. 133 cas département × année.

| Année | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | Ensemble |
|---|---|---|---|---|---|---|---|---|
| Contrats tenus (M1) | 76 % | 39 % | 56 % | 68 % | 100 % | 100 % | 100 % | **78 %** |

Les contrats cèdent en 2020 et 2021, deux effondrements de la lentille absents de l'entraînement, et en 2022, quand le blé flambe. Le chiffre a été corrigé de 87 % à 78 % le 31/10 après un audit interne : le regroupement des séries utilisait toute la période, y compris les années testées. L'équipe garde le chiffre strict.

### 5.8 Où est l'IA, et ce qu'on perdrait sans elle

- **Le cœur** : un modèle d'apprentissage probabiliste, qui apprend comment la météo déplace la distribution du rendement, calibré et validé sur des années jamais vues. Sans lui, on n'a qu'une moyenne, et une moyenne ne tient que 29 % des contrats. Avec lui, 78 %.
- **Le satellite** : un classifieur LightGBM sur les séries Sentinel-2 repère les légumineuses d'une campagne un an avant la publication du registre parcellaire (prototype, §7.9).
- **Le modèle de langage** (Amazon Bedrock) : il rédige la lettre de proposition à partir des chiffres calculés, au moment de la construction de l'application. Un garde-fou rejette tout texte contenant un nombre absent des entrées. Il ne produit aucun chiffre, et la démo ne dépend pas du réseau.

### 5.9 L'incertitude, affichée

- Le rendement d'une année se prédit à ±35 % (erreur médiane, mesuré) : c'est pourquoi on calibre un prix sur le risque plutôt que sur une prévision.
- P\* lui-même est incertain : de 1 099 à 2 877 €/t à 80 % en Seine-et-Marne (rééchantillonnage des années, modèle). Seize ans ne suffisent pas pour cerner les mauvaises années.
- Sept années de test seulement : l'écart de 78 à 80 % représente deux à trois contrats.

---

## 6. Les données utilisées

Toutes ouvertes, téléchargées et traitées par le pipeline (`pipeline/00` à `11`), versionnées dans le dépôt sauf le RPG, retéléchargé.

| Donnée | Source | Période, volume | À quoi elle sert | Statut, licence |
|---|---|---|---|---|
| Surfaces, rendements, productions par département | Agreste, Statistique agricole annuelle (SAA) | 2010–2025 (2025 provisoire) ; lentille 39 départements, 24 séries ; blé 90 séries ; pois chiche, haricot, pois, féverole | apprendre les rendements ; constat national | mesuré, Licence Ouverte |
| Météo journalière | NASA POWER | 2010–2025, 43 départements, six variables | expliquer les rendements ; rejouer les années | mesuré (réanalyse), données publiques NASA |
| Parcelles déclarées | IGN, Registre parcellaire graphique (RPG) 2025, Île-de-France | 20 922 parcelles, dont 20 762 de blé tendre d'hiver | carte, parcelles qui basculent, courbe d'offre | mesuré, Licence Ouverte |
| Parcelles déclarées 2024 | RPG 2024, Île-de-France | une zone de 24 × 24 km | étiquettes d'apprentissage de Vu du ciel | mesuré |
| Commerce extérieur des lentilles | Eurostat Comext | importations et exportations 1997–2025, origines 2025, valeur des importations 2010–2025 | constat, provenance, prix de l'import | mesuré, réutilisation autorisée avec citation |
| Prix du blé tendre | Eurostat (indice des prix à la production), calé sur le prix rendu Rouen d'Agreste 2019-2020 | 2010–2025 : 154 €/t (2016) à 338 €/t (2022) | marge du blé, année par année | mesuré |
| Prix de la lentille | Eurostat | 2012–2016 : 650 à 779 €/t | prix de référence historique | mesuré |
| Images satellite | Copernicus Sentinel-2 L2A, catalogue Earth Search (AWS) | 148 images en 2025 pour le suivi de saison ; 51 images (45 dates utiles) en 2024–2025 pour Vu du ciel | NDVI, NDMI, détection des légumineuses | mesuré, accès libre avec citation |
| Établissements du commerce de grains | Insee, base Sirene, API Recherche d'entreprises | 352 établissements à moins de 15 km d'une parcelle francilienne, dont 171 de coopératives ; 142 coopératives et 28 unions en France | sites de collecte existants, taille du marché | mesuré, Licence Ouverte 2.0 |
| Chiffres du secteur coopératif | Coop FR, chiffres 2024 | 2 100 coopératives agricoles, 118 Md€ de chiffre d'affaires | taille du secteur client | sourcé |
| Contours des départements | IGN Admin Express, via france-geojson | France métropolitaine | cartes, centroïdes météo | mesuré, Licence Ouverte |
| Codes de culture | Telepac, notice PAC 2025 | libellés des codes du RPG | affichage | sourcé |
| Lots d'une coopérative | jeu de l'équipe, `data/pilote_300t` | 140 lots fictifs 2019–2025 | démonstration du pilote, jamais utilisés pour l'apprentissage ni le test | synthétique |

**Les hypothèses économiques** (`data/hypotheses.yaml`, chacune avec sa source et sa sensibilité) :

| Paramètre | Valeur | Statut, source |
|---|---|---|
| Charges opérationnelles du blé | 700 €/ha | supposé, arrondi de 675 €/ha (Cerfrance Nord-Est Île-de-France, cité par Terres Inovia 2025) |
| Charges opérationnelles de la lentille | 500 €/ha | supposé, arrondi de 518 €/ha (guide lentille Terres Inovia 2023) |
| Aide couplée aux légumineuses | 105 €/ha | sourcé, montant indicatif 2026 (Telepac) ; 122 €/ha annoncés pour 2023–2025 |
| Bénéfice de rotation pour le blé suivant | 150 €/ha | supposé, effet précédent documenté par FiloLeg 2024 |
| Part de la récolte refusée au tri | 10 % | supposé ; la bruche peut coûter 10 à 20 % (Réussir) |
| Collecte | 5 €/t + 0,12 €/t/km, distance × 1,3 | supposé |
| Tri | 180 €/t reçue | supposé, repère du tri optique en bio, sans devis |
| Protection visée | 8 années sur 10 | supposé, choix de l'équipe, réglable dans le simulateur |
| Protéines de la lentille | 25 % | sourcé, Terres Inovia / Terres Univia, récolte 2024 |
| Azote minéral sur blé en Île-de-France | 180 kg N/ha | sourcé, DRIAAF, Mémento 2025 (177 kg N/ha arrondi) |
| Émissions directes de N₂O évitées | 0,755 t CO₂e/ha | sourcé, GIEC 2019 et AR6 |
| Site de collecte | Seine-et-Marne, un point fictif | synthétique, annoncé comme tel |
| Volumes | pilote 300 t, ambition 5 000 t | supposé ; NatUp a collecté 558 t en 2025 |

[SOURCES.md](SOURCES.md) liste aussi trois sources envisagées qui n'entrent dans aucun résultat : les données des douanes (Comext a été retenu), le registre national des cantines et HESTIA.

---

## 7. Les résultats à connaître

### 7.1 Le prix plancher 2026 (8 années sur 10)

| Département | P\* | Prix d'équilibre médian | Rendement lentille simulé | Une année sur dix |
|---|---|---|---|---|
| Seine-et-Marne | **1 567 €/t** | 715 €/t | 1,59 t/ha (1,43 accepté au tri) | 0,48 t/ha |
| Yvelines | 1 445 €/t | 674 €/t | 1,61 t/ha | 0,50 t/ha |
| Essonne | 1 450 €/t | 674 €/t | 1,60 t/ha | 0,50 t/ha |
| Val-d'Oise | 1 540 €/t | 718 €/t | 1,61 t/ha | 0,50 t/ha |

Garantir 8 années sur 10 coûte plus du double du prix d'équilibre médian : c'est le cœur du message.

### 7.2 Le prix de chaque niveau de sécurité (Seine-et-Marne, modèle)

| Années gagnantes visées | 5 sur 10 | 6 | 7 | 8 | 9 | 9,5 |
|---|---|---|---|---|---|---|
| Prix nécessaire | 715 €/t | 871 | 1 132 | 1 567 | 2 632 | 4 397 |

Les mauvaises années de lentille sont rares mais profondes : protéger plus coûte vite très cher. La coopérative choisit son niveau dans le simulateur.

### 7.3 Les sensibilités (Seine-et-Marne, modèle)

| Hypothèse | P\* |
|---|---|
| Prix du blé fixé de 160 à 280 €/t | 1 070 à 2 348 €/t |
| Part refusée au tri de 0 à 20 % | 1 411 à 1 763 €/t |
| Bénéfice de rotation de 200 à 0 €/ha | 1 500 à 1 773 €/t |
| Charges du blé de 800 à 600 €/ha | 1 432 à 1 703 €/t |
| Charges de la lentille de 400 à 600 €/ha | 1 432 à 1 703 €/t |
| Aide couplée à 122, 105 ou 0 €/ha | 1 546, 1 567 ou 1 709 €/t |

### 7.4 Ailleurs en France

Le même calcul donne le prix de 24 départements producteurs, à charges franciliennes : de **558 €/t** (Pyrénées-Orientales) à **2 238 €/t** (Haute-Loire) ; Hérault 842, Gard 900, Indre 1 115, Cher 1 183 €/t (modèle). Le prix baisse là où le blé rend peu, ou là où la lentille rend bien face au blé.

### 7.5 Les contrats comparés (Seine-et-Marne)

| Contrat | Années gagnantes | Coût moyen pour l'acheteur | Contrats tenus en backtest |
|---|---|---|---|
| Unéal 2023, 900 €/t | 6,1 sur 10 | 900 €/t | 57 % |
| NatUp 2023–2024, 900 / 700 / 600 €/t (reconstitué) | 5,9 sur 10 | 818 €/t | 55 % |
| Prix unique calibré, 1 567 €/t | 8 sur 10 | 1 567 €/t | 78 % |
| **Barème par tranches, 1 635 / 750 / 650 €/t** | **8 sur 10** | **1 283 €/t (−18 %)** | **79 %, coût réalisé −19 %** |
| Plancher indexé, 7,44 × prix du blé | 8 sur 10 | 1 519 €/t | 82 % |
| Base 900 €/t et prime de 491 €/ha | 8 sur 10 | 1 243 €/t (−21 %) | 74 % (37 % en 2022) |

Les barèmes publiés protègent environ 6 années sur 10 face au blé francilien : ils partagent aussi le risque par les volumes, la qualité et le choix des bassins, ce que ce calcul ne mesure pas. En 2022, quand le blé flambe, ils tombent à 5–16 % de contrats tenus, contre 68 % pour les contrats calibrés.

### 7.6 Ce que gagne l'agriculteur (face au blé de la même année)

« 8 années sur 10 » est un plancher, pas la moyenne. Marge moyenne du blé : 869 €/ha (modèle).

| Contrat | Années gagnées | Écart moyen | Les années gagnées | Les années perdues |
|---|---|---|---|---|
| Unéal 2023, 900 €/t | 6 sur 10 | +174 €/ha | +658 €/ha | −592 €/ha |
| Prix unique, 1 567 €/t | 8 sur 10 | +1 128 €/ha | +1 555 €/ha | −581 €/ha |
| **Barème par tranches** | **8 sur 10** | **+722 €/ha** | +1 044 €/ha | −568 €/ha |
| Indexé sur le blé | 8 sur 10 | +1 059 €/ha | +1 455 €/ha | −526 €/ha |

### 7.7 Ce que paie la coopérative : le pilote de 300 t

| Par campagne | Prix unique | Barème par tranches | Indexé |
|---|---|---|---|
| Achat des lentilles (modèle) | 470 k€ | **385 k€** | 456 k€ |
| Tri, 180 €/t reçue (supposé) | 60 k€ | 60 k€ | 60 k€ |
| Collecte (supposé) | 2 k€ | 2 k€ | 2 k€ |
| **Total** | 532 k€, 1 773 €/t | **447 k€, 1 489 €/t** | 517 k€, 1 725 €/t |

Le bon contrat fait économiser **85 k€ par campagne** sur 300 t (470 − 385 k€, modèle). Séchage, stockage et conditionnement sont exclus.

**Face à l'import** : 1 489 €/t, c'est 420 €/t de plus que l'import de 2025 (1 069 €/t), environ 21 centimes par sachet de 500 g ; l'écart tombe vers 290 €/t sur 2022–2024. Les contrats publiés (900 à 1 000 €/t) sont, eux, sous le prix de l'import. Dans les départements où le blé rend moins (Pyrénées-Orientales, Hérault, Gard), le prix garanti rejoint celui de l'import une fois tri et collecte ajoutés.

### 7.8 Les autres légumineuses (même moteur)

| Culture | P\* Seine-et-Marne | Contrats tenus, prix fixe | Contrats tenus, indexé sur le blé |
|---|---|---|---|
| Lentille | 1 567 €/t | 78 % | 82 % |
| Pois chiche | 1 064 €/t | 65 % | 78 % |
| Haricot sec (irrigué) | 2 185 €/t | 70 % | 89 % |
| Pois protéagineux | 427 €/t | 66 % | 82 % |
| Féverole | 462 €/t | 68 % | 82 % |

Le moteur est générique, la forme du contrat ne l'est pas : barème par tranches pour la lentille, dont le risque vient surtout du rendement ; plancher indexé sur le blé pour les quatre autres, dont le risque vient surtout du prix du blé.

### 7.9 Les prototypes satellite

- **Suivi de saison** : 2025 rejoué sur les 8 parcelles de lentille les plus proches du site, 148 images Sentinel-2. Six suivent le groupe, deux sont en retard en mai : l'outil dit où aller voir, pas encore ce que la parcelle va rendre.
- **Vu du ciel** : sur une zone de 24 × 24 km, en connaissant les parcelles d'un carré de 4 km sur cinq, le modèle retrouve 73 % des légumineuses des autres carrés en fin de saison, avec 90 % de signalements justes, un an avant le registre parcellaire (45 % et 69 % au 10 juin). Appris sur l'année précédente seule, il n'en retrouve que 8 % : ce transfert raté est affiché.

### 7.10 La collecte existe déjà

- 352 établissements du commerce de grains à moins de 15 km des parcelles franciliennes, dont 171 de coopératives (Sirene, mesuré). Le meilleur pour le pilote, Vivescia à Chenoise-Cucharmoy, est à 1,0 km en moyenne des parcelles retenues ; le site fictif du scénario, à 2,4 km.
- Le meilleur emplacement ne fait gagner que quelques dixièmes d'euro par tonne : le site se choisit pour la logistique (silo, accès, capacité), pas pour le prix. Sirene ne dit pas si un établissement est un silo.

---

## 8. Le contrat proposé

**Barème par tranches, sur trois campagnes, départ ferme, sur les tonnes acceptées au tri : 1 635 €/t pour la première tonne par hectare, 750 €/t pour la deuxième, 650 €/t au-delà.**

- Même protection qu'un prix unique de 1 567 €/t (8 années sur 10 au moins aussi bien que le blé), pour 18 % de moins en moyenne ; en backtest, 79 % de contrats tenus pour 19 % de moins.
- La première tonne est celle qui manque les mauvaises années : la payer cher protège là où ça compte, sans surpayer les bonnes récoltes.
- Même structure que le barème publié par NatUp (900 / 700 / 600 €/t) : la coopérative ne change pas de logique, elle change de niveau, calculé sur le risque.
- La lettre au producteur (annexe « La proposition de contrat ») reprend le barème et dit ce que le prix garantit et ce qu'il ne garantit pas : un prix plancher n'est pas une assurance récolte.

---

## 9. Le business plan

### 9.1 Le client et pourquoi il paie

- **Client** : les coopératives et les conditionneurs de légumes secs. Ils ont le problème, le budget, et prennent cette décision à chaque campagne.
- **Valeur** : payer le moins possible pour une protection donnée. Sur un pilote de 300 t, le barème par tranches économise 85 k€ par campagne face au prix unique (modèle). Un prix trop haut de 20 €/t sur 5 000 t coûte 100 k€ par campagne (calcul illustratif) ; un prix trop bas fait perdre les surfaces après une année comme 2020.
- **Ce qu'elle ne sait pas faire seule** : relier 16 ans de météo, de rendements et de prix du blé à une probabilité de tenir le contrat, et le vérifier sur des années jamais vues.

### 9.2 L'offre

| Étape | Contenu | Prix |
|---|---|---|
| Étude pilote | le calcul refait avec les rendements et les charges de la coopérative, sur son bassin ; comparaison avec son barème actuel | 3 000 € (supposé, à tester) |
| Abonnement | par campagne et par bassin : prix et barème recalculés avant les semis, parcelles, budget, suivi de saison | 10 000 € par campagne et par bassin (supposé, à tester) |

Ces montants sont des hypothèses, choisies pour obtenir une première vente et mesurer la valeur. Rapportés aux 85 k€ économisés sur un seul pilote de 300 t, ils restent faibles ; le gain doit être démontré chez le client.

### 9.3 Le marché

- **Clients directs** : 142 coopératives agricoles et 28 unions de coopératives ont pour activité principale le commerce de gros de céréales (Sirene, NAF 46.21Z, mesuré). Le code ne dit pas lesquelles collectent des légumes secs ; les conditionneurs ne sont pas comptés.
- **Le secteur** : 2 100 coopératives agricoles, 316 000 sociétaires, 118 Md€ de chiffre d'affaires (Coop FR, chiffres 2024, sourcé).
- **Ordre de grandeur** : si les 170 coopératives et unions s'abonnaient pour un seul bassin, 1,7 M€ par an (calcul illustratif, supposé). Le marché grandit avec les cultures (cinq légumineuses déjà calculées) et les bassins.
- **La lentille seule est un petit marché** : 33 927 ha en 2025 (mesuré). C'est la porte d'entrée, pas la cible finale.

### 9.4 Qui paie le prix de la lentille au bout de la chaîne

Le prix garanti est payé par la coopérative, qui revend au conditionneur, qui vend aux magasins et à la restauration. Avec le barème par tranches, tri et collecte compris, le pilote coûte 1 489 €/t, contre 1 069 €/t pour l'import de 2025. Trois leviers :

- **un débouché qui paie l'origine France** (marques, restauration collective) : l'écart représente environ 21 centimes par sachet de 500 g, et achète trois ans de prix stable, alors que l'import a pris 53 % entre 2020 et 2022 ;
- **un bassin moins cher** : la carte de France montre les départements où le prix garanti rejoint celui de l'import ;
- **un niveau de protection choisi** : 7 années sur 10 coûtent 1 132 €/t au lieu de 1 567.

L'import ne disparaît pas : le contrat remplace une part des volumes (13 % pour un bassin de 5 000 t) et rend le reste moins exposé aux chocs de prix.

### 9.5 Le chemin d'adoption

1. **Pilote de 300 t** avec une coopérative qui monte déjà une filière lentille ([PILOTE_300T.md](PILOTE_300T.md)) : NatUp / Lunor en priorité (558 t collectées en 2025, contrat triennal publié), puis Unéal / Vivien Paille, Cibèle / Axéréal pour le tri, Valfrance pour un terrain francilien. Aucun n'a encore été contacté ; un message à NatUp est prêt.
2. **Phase 1** : comparer, sur une collecte existante, le barème du partenaire et deux variantes calculées. **Phase 2** : dimensionner une campagne 2027.
3. **Conversion** en abonnement, puis les coopératives déjà engagées dans des contrats à prix minimum, puis les nouvelles filières du plan protéines.

### 9.6 Les extensions

- **Autres cultures sous contrat** : pois chiche, haricot sec, pois, féverole sont déjà calculés ; chanvre, sorgho, cultures bas carbone suivent le même moteur.
- **Autres régions** : 24 départements producteurs déjà calculés ; seule la couche parcellaire change.
- **Assureurs agricoles** : la même distribution de récolte tarife une assurance rendement : 231 €/ha de prime pure pour garantir 70 % du rendement moyen en Seine-et-Marne, sinistre 3 années sur 10 (modèle, hors chargements). Le prix plancher couvre la marge, l'assurance la récolte effondrée : les deux se complètent.
- **Industriels de l'agroalimentaire** qui veulent sécuriser un approvisionnement français.
- **Données de saison** (Vu du ciel) : surfaces de légumineuses connues un an avant le registre parcellaire, pour les collecteurs et les interprofessions.

### 9.7 Les risques business

- marché de départ étroit (la lentille) ;
- cycle de vente long dans les coopératives ;
- prix garanti au-dessus de l'import en Île-de-France : il faut un débouché qui paie l'origine ;
- dépendance aux données de rendement des coopératives pour passer du département à la parcelle ;
- une coopérative ou un éditeur de logiciel agricole peut refaire un calcul de moyenne ; refaire le modèle calibré et son backtest demande des compétences de statistique.

Réponse : un pilote d'une campagne, à faible coût, qui produit la preuve chez le client.

---

## 10. Concurrence et alternatives

Recherche documentaire du 1er novembre 2026, une trentaine de pages lues ; chaque ligne renvoie à sa source (liste dans [SOURCES.md](SOURCES.md)).

**En bref** : personne ne relie le prix garanti, la probabilité de battre le blé et la vérification sur les années passées. Les acteurs existants fixent un prix sur les coûts ou à l'expérience, assurent une récolte ou un revenu, ou calculent des marges sans probabilité. Nous nous plaçons entre le conseil technique et l'assurance.

### 10.1 Ceux qui fixent déjà un prix de légumineuse

| Acteur | Ce qu'il fait | Ce qu'il ne fait pas | Pour nous |
|---|---|---|---|
| **Unéal, NatUp, Qualisol** (§2.3) | contrats à prix minimum ou barème par tranches | prix fixé à l'expérience ; dans notre modèle, environ 6 années sur 10 face au blé francilien | clients |
| **Max Havelaar France, « Origine France »** ([Réussir](https://www.reussir.fr/grandes-cultures/commerce-equitable-max-havelaar-garantit-des-prix-planchers-pour-des-bles-et-legumineuses-francais) ; [Réussir, 21/08/2026](https://www.reussir.fr/grandes-cultures/legumineuses-une-filiere-commerce-equitable-max-havelaar-se-structure-dans-le-sud-ouest)) | prix plancher par territoire, contrats de trois ans. Récolte 2025, conventionnel, ex-Poitou-Charentes : lentille 1 019 €/t, plus 51 €/t de prime collective. Calcul : coûts de production, revenu de 1,5 SMIC, surcoût des pratiques exigées. 175 ha et 6 agriculteurs pilotes en 2025 | plancher tiré de coûts moyens : ni risque de rendement, ni probabilité de battre le blé, ni backtest | **le substitut le plus proche** ; partenaire possible. Ordre de grandeur : 1 000 €/t protège 6,5 années sur 10 face au blé de Seine-et-Marne dans notre modèle |
| **Euralis × Bonduelle** ([Euralis, 1/06/2023](https://www.euralis.fr/wp-content/uploads/2023/06/1er-anniversaire-partenariat-Bonduelle-legumes-secs-juin-2023.pdf)) | filière légumes secs depuis 2022 : environ 1 000 ha, 115 agriculteurs dont 40 en lentilles, débouché garanti par contrat de production | prix non publié | canal, pilote possible |
| **Cavac** ([Réussir, 18/10/2018](https://www.reussir.fr/lesmarches/la-cavac-investit-dans-sa-station-de-legumes-secs)) | toutes les surfaces de légumes secs sous contrat (350 producteurs, 3 200 ha en 2018) | méthode de prix non publiée | canal, pilote possible |
| **Hari&Co** ([Réussir, 17/05/2022](https://www.reussir.fr/lesmarches/une-filiere-et-des-plats-cuisines-pour-harico)) | achète toute la production de ses agriculteurs à un prix défini à l'avance (10 agriculteurs, 60 ha bio en 2022) | montant et méthode non publiés | canal |
| **Sabarot**, lentille verte du Puy en AOP ([Pleinchamp, 18/07/2022](https://www.pleinchamp.com/actualite/lentille-verte-du-puy-aop-les-raisons-d-esperer-en-2022)) | contrats annuels d'environ 2 300 à 2 400 €/t | prix négocié, aucun calcul de risque publié | canal ; montre qu'un prix élevé tient avec un signe de qualité |

Aucun contrat lentille public n'a été trouvé chez Terrena ni chez Vivescia.

### 10.2 L'assurance et la gestion du risque

| Acteur | Ce qu'il fait | Ce qu'il ne fait pas | Pour nous |
|---|---|---|---|
| **Assurance récolte multirisque**, réforme de 2023 ([DRAAF Grand Est, novembre 2025](https://draaf.grand-est.agriculture.gouv.fr/IMG/pdf/2511_assurancerecoltes_bro-1.pdf)) | prime subventionnée jusqu'à 70 %, franchise de 20 % ; en grandes cultures, solidarité nationale au-delà de 50 % de pertes ; régime maintenu 2026–2028 | ne couvre ni le prix ni la marge face au blé ; rien de propre aux légumineuses | complément : la récolte effondrée, dans les 2 années sur 10 |
| **Assurance paramétrique** : AXA Climate (germination du colza, près de 80 000 ha en France en 2023), Descartes Underwriting (sécheresse, gel, chaleur) ([GrECo, 9/05/2023](https://greco.services/parametric-insurance-rapeseed-besse-and-greco-sign-an-exclusive-distribution-partnership-agreement/) ; [Descartes](https://descartesunderwriting.com/products/agriculture)) | indemnise sur un indice (météo, satellite, biomasse) | ni légumineuses, ni prix de contrat | partenaires possibles ; notre distribution de récolte sert à tarifer (231 €/ha de prime pure à 70 %) |
| **États-Unis** : Revenue Protection de l'USDA, ouverte à la lentille ([RMA, 2023](https://www.rma.usda.gov/policy-procedure/bulletins-memos/product-management-bulletin/2023/pm-23-015-2023-crop-year-cy-dry)) | garantit le revenu de l'agriculteur, avec un prix projeté et sa volatilité | ne fixe pas de prix de contrat, ne compare pas au blé | l'analogue probabiliste le plus proche |
| **Canada** : Contract Price Option de Saskatchewan Crop Insurance, AgriStability ([Farms.com, 2022](https://www.farms.com/news/saskatchewan-announces-2022-crop-insurance-program-176746.aspx) ; [AAC](https://agriculture.canada.ca/en/programs/agristability)) | la première assure la récolte au prix du contrat signé ; la seconde paie 80 % de la baisse de marge au-delà de 30 %, sur toute l'exploitation | ne calculent pas le prix du contrat | notre prix garanti pourrait devenir le prix assuré |

### 10.3 Les outils de décision et les logiciels

| Acteur | Ce qu'il fait | Ce qu'il ne fait pas | Pour nous |
|---|---|---|---|
| **FiLoLeG**, Chambre d'agriculture des Hauts-de-France et Agro-Transfert ([présentation](https://www.hautsdefrance.chambres-agriculture.fr/fileadmin/user_upload/Hauts-de-France/171_Inst-Hauts-de-France/2-Nos-actions/DAS5-cultures-sources-proteines-vegetales/Flyer_Projet_FILOLEG.pdf)) | marge des rotations avec légumineuses selon des scénarios de prix et de rendement | scénarios fixes : ni probabilité visée, ni backtest, ni barème | **le substitut partiel le plus proche en France** ; partenaire naturel (nous utilisons déjà sa synthèse pour l'effet précédent) |
| **Terres Inovia** ([myVar, Réussir](https://www.reussir.fr/ladepeche/mieux-connaitre-les-varietes-de-lupin-lentille-et-pois-chiche-grace-myvar-de-terres-inovia)) | références techniques (nos charges en viennent), choix des variétés | pas de probabilité, pas de barème | source, validation, canal |
| **Argus Media**, qui a racheté Agritel ([Réussir](https://www.reussir.fr/argus-media-soffre-agritel)) | cotations et conseil sur les marchés des grains | aucune cotation lentille trouvée | source possible pour le prix du blé |
| **Plateformes de contrats** : Bushel, Grain Discovery (DTN), AgriDigital ([Bushel](https://www.bushelpowered.com/blog/investing-in-tech) ; [DTN](https://www.dtn.com/agriculture/grain-discovery/) ; [AgriDigital](https://agridigital.io/)) | contrats numériques, offres et règlements pour les silos et coopératives (Amérique du Nord, Australie) | ne calculent pas de prix garanti | canal de diffusion du contrat |
| **Agronomie numérique** : Xarvio, Hiphen ([Xarvio](https://ag.xarvio.com/field-manager)) | suivi des parcelles, phénotypage | rien sur le prix | fournisseurs de données |

Les logiciels de collecte des coopératives françaises gèrent les contrats et les apports ; aucun calcul de prix garanti n'y a été trouvé, sans examen détaillé.

**Programmes publics** : la stratégie nationale pour les protéines végétales finance encore l'innovation variétale des légumineuses (appel à projets de 10 M€, juillet 2026, [agriculture.gouv.fr](https://agriculture.gouv.fr/ouverture-dun-appel-a-projets-en-faveur-de-linnovation-varietale-des-legumineuses)) ; Cap Protéines+ (2024–2027, 7,5 M€ ; Terres Inovia, Arvalis, Idele, Terres Univia) finance la recherche ([plaquette](https://www.terresinovia.fr/sites/default/files/document_library/20126/3146141/3332226/plaquette-cap-proteines-plus.pdf)). Ce sont des financeurs ou des partenaires, pas des concurrents. Signes de qualité : lentille verte du Puy en AOP, lentille verte du Berry en IGP et Label Rouge (INAO).

### 10.4 Ce qui n'existe pas, et les risques

Nous n'avons trouvé **aucun outil ni service qui calcule le prix garanti rendant une culture de diversification compétitive face au blé avec une probabilité visée, et qui le vérifie sur les années passées**. Le plus proche : Max Havelaar (un vrai plancher, calculé sur les coûts), FiLoLeG (des seuils face au blé, en scénarios fixes), les assurances revenu américaines et canadiennes (probabilistes, mais elles assurent un revenu sans concevoir de contrat).

Les risques, honnêtement :

- Max Havelaar a déjà une méthode de plancher acceptée par des acheteurs et pourrait y ajouter une couche de risque.
- Terres Inovia, Arvalis et les Chambres d'agriculture ont les données et la légitimité : un prix d'intérêt probabiliste est à leur portée.
- Un assureur peut vendre une garantie de marge indexée sur le blé.
- Notre méthode (régression quantile, simulation) est publique et reproductible en quelques semaines. L'avantage tient à la mise en forme pour la coopérative, à la vérification sur les années passées et au premier pilote signé ; sans pilote, il reste fragile.

---

## 11. Ce qui nous différencie

| | Pratique actuelle | Le Contrat qui Tient |
|---|---|---|
| Base du prix | expérience, moyennes, prix du marché | distribution du risque, conditionnée à la météo, avec le prix du blé de chaque année |
| Promesse à l'agriculteur | « en moyenne, ça rapporte » | « 8 années sur 10, au moins autant que le blé », et l'écart chiffré les autres années |
| Forme du contrat | barème choisi à l'expérience | barème calibré : même protection pour 18 % de moins |
| Ciblage | prospection au cas par cas | carte des parcelles qui basculent à ce prix, au plus près d'un site existant |
| Preuve | aucune | backtest strict sur sept années jamais vues : 78 % pour 80 % promis |
| Transparence | — | chaque chiffre étiqueté, données ouvertes, code public, limites affichées |

- **Nous ne créons pas le contrat** : il existe déjà. Nous calculons le prix et la forme qui le rendent tenable, pour l'agriculteur et pour la coopérative.
- **Le chiffre honnête** : 78 % pour 80 % promis, pas 100 %. Au-dessus, la coopérative surpaie ; en dessous, l'agriculteur est trompé.
- **Le plus précis n'est pas le meilleur** : nous avons gardé le modèle qui protège le mieux, pas celui qui prédit le mieux la moyenne, et nous l'avions choisi avant de voir les résultats.

---

## 12. L'impact et la durabilité

| | Pilote, 300 t | Ambition de bassin, 5 000 t |
|---|---|---|
| Surface | 216 ha, 28 parcelles à moins de 3,2 km | 3 502 ha, 260 parcelles à moins de 9,8 km |
| Part des importations 2025 | 0,8 % | 12,7 % |
| Protéines végétales (25 % des tonnes) | 75 t | 1 250 t |
| Azote minéral non apporté (180 kg N/ha de blé remplacé) | 39 t N | 630 t N |
| Émissions directes de N₂O évitées | 163 t CO₂e | 2 644 t CO₂e |

Statut : modèle appliqué à des volumes supposés, coefficients sourcés. Les compteurs excluent la fabrication des engrais et les émissions indirectes.

- **Résilience du revenu** : l'agriculteur est protégé 8 années sur 10, contre 6 au prix de 900 €/t.
- **Résilience de l'approvisionnement** : moins de dépendance à un import dont le prix a pris 53 % entre 2020 et 2022, et qui vient pour 45 % du Canada.
- **Durabilité agronomique** : la lentille ne reçoit pas d'engrais azoté et améliore le blé suivant.

---

## 13. Le passage à l'échelle

| Piste | Ce qu'elle apporte |
|---|---|
| Données de rendement des coopératives | passer du département à la parcelle et corriger la sous-estimation du risque |
| Autres cultures sous contrat | même moteur, nouveaux libellés Agreste ; cinq légumineuses déjà calculées |
| Autres régions | 24 départements déjà calculés (écran 6, touche `F`) |
| Modèle hiérarchique bayésien | partager l'information entre départements peu renseignés |
| Offre assureurs | prime pure sur la même distribution ; chargements à construire avec un assureur |
| Réseau de collecte | 352 établissements autour de l'Île-de-France ; capacités et silos réels à obtenir des coopératives |
| Historique du registre parcellaire | rotations réelles, éligibilité plus fine (délai de retour de la lentille) |
| Satellite | suivi de saison calé sur les rendements du pilote ; Vu du ciel sur plusieurs campagnes, avec le radar Sentinel-1 |

Techniquement, le pipeline se relance avec `make`, et l'application est un site statique : passer à un nouveau bassin, c'est relancer le pipeline avec sa couche parcellaire et ses hypothèses.

---

## 14. Les limites assumées

Détail complet : [LIMITES.md](LIMITES.md).

1. **Rendements départementaux** : la variance réelle à la parcelle est plus forte, le risque est sous-estimé.
2. **Peu de lentille en Île-de-France** (727 ha selon la SAA, 1 095 ha au RPG) : le niveau de rendement est emprunté aux départements voisins.
3. **P\* incertain** : de 1 099 à 2 877 €/t à 80 % ; sept années de test seulement.
4. **Années extrêmes absentes de l'entraînement** : les contrats cèdent en 2020–2022 (39 %, 56 %, 68 %), et c'est montré.
5. **Météo au centroïde du département**, pas sur les parcelles cultivées.
6. **Prix du blé reconstitué**, un peu au-dessus du prix payé au producteur : choix prudent, qui surestime P\*.
7. **Charges supposées, constantes dans le temps** ; sensibilités affichées.
8. **Bénéfice de rotation compté dans la marge de la campagne** : il arrive sur le blé suivant ; sans lui, P\* = 1 773 €/t.
9. **Site de collecte fictif**, distances à vol d'oiseau × 1,3 ; Sirene ne distingue pas un silo d'un bureau.
10. **Un prix plancher n'est pas une assurance** : les 20 % d'années non couvertes sont visibles.
11. **Budget de l'acheteur** : tri et collecte sans devis ; séchage, stockage et conditionnement exclus.
12. **Prix de revente de la coopérative inconnu** : sans débouché qui paie l'origine, le pilote francilien coûte plus que l'import.
13. **Simulateur limité à la Seine-et-Marne** ; il ne charge pas encore les rendements d'une coopérative.
14. **Prototypes satellite** : 8 parcelles et une zone de 24 km ; le transfert d'une année à l'autre ne tient pas encore.

---

## 15. Ce qui est réel, ce qui est simulé

| Élément | Statut |
|---|---|
| Rendements, météo, parcelles, importations, prix du blé, sites Sirene, images satellite | mesuré |
| Résultats du backtest (78 %, 29 %, couverture 79 %) | mesuré, sur des récoltes réelles |
| Charges de référence, aide couplée, protéines, azote, contrats Unéal et NatUp | sourcé |
| Charges centrales arrondies, rotation, part refusée, tri, collecte, volumes, protection visée, prix de l'abonnement | supposé |
| Prix plancher, barèmes, gains de l'agriculteur, budget d'achat, carte de France, prime d'assurance, compteurs d'impact | modèle |
| Site de collecte du scénario, lots du pilote de 300 t, proposition de contrat 2027 du dossier pilote | synthétique |
| Camions et cargos de la démo | animation schématique ; le compteur de tonnes vient du calcul |
| Partenaire | aucun : candidats identifiés, non contactés |

---

## 16. L'architecture technique

- **Pipeline Python** (`pipeline/00` à `11`, `model.py`, `contrats.py`) : téléchargement, nettoyage, modèles, Monte-Carlo, backtest, contrats, export JSON. Relancé avec `make` ; hypothèses dans un seul fichier ; 29 tests automatiques, dont un qui vérifie que les années exportées pour le simulateur redonnent exactement le prix et le barème du pipeline.
- **Application** : Vite, React, TypeScript, deck.gl pour la carte (20 922 parcelles). Aucun appel à un service externe pendant la démo ; version hors ligne en un fichier.
- **Hébergement** : AWS Amplify, déployé à chaque mise à jour du dépôt.
- **Modèle de langage** : Amazon Bedrock, appelé une fois au moment de la construction pour la lettre, avec garde-fou sur les nombres.
- **Satellite** : images Sentinel-2 lues directement sur AWS (catalogue Earth Search), sans téléchargement complet.
- Détail : [ARCHITECTURE.md](ARCHITECTURE.md), [MODELE.md](MODELE.md).

---

## 17. Les questions probables, en une phrase

Réponses complètes : [PITCH_NOTES.md](PITCH_NOTES.md).

| Question | Réponse courte |
|---|---|
| Qui est l'utilisateur ? | La responsable filière d'une coopérative qui développe la lentille, avant les semis. |
| Qui paie ? | La coopérative, par campagne : étude pilote puis abonnement par bassin (montants à tester). |
| Pourquoi elle paierait ? | Le bon contrat lui économise 85 k€ par campagne sur 300 t, à protection égale. |
| L'agriculteur gagnerait plus avec le blé ? | Non : ces 8 années, +1 555 €/ha en moyenne ; les 2 autres, −581 €/ha. |
| Qui paie 1 567 €/t ? | Personne en moyenne : avec le barème, 1 283 €/t ; 1 489 €/t avec tri et collecte, contre 1 069 €/t pour l'import. |
| Où est l'IA ? | Un modèle probabiliste calibré qui relie la météo à la distribution des rendements ; sans lui, 29 % de contrats tenus au lieu de 78 %. |
| Pourquoi pas le modèle le plus précis ? | LightGBM prédit mieux la moyenne mais tient 76 % des contrats : pour protéger un revenu, la queue basse compte plus. |
| Comment vous mesurez la qualité ? | Backtest strict 2019–2025, 133 cas, et couverture de l'intervalle à 80 % (79 %). |
| Qu'est-ce qui est réel ? | Toutes les données sont réelles et ouvertes ; le site de collecte et les lots du pilote sont fictifs ; les charges sont des hypothèses sourcées. |
| Pourquoi pas 10 années sur 10 ? | 9 sur 10 coûte 2 632 €/t, 9,5 sur 10 4 397 €/t : un prix plancher n'est pas une assurance. |
| Ça existe déjà ? | Les contrats à prix minimum, oui : Unéal, NatUp, et Max Havelaar, dont le plancher lentille (1 019 €/t en 2025) est calculé sur les coûts. Un outil qui calcule ce prix sur le risque face au blé, le vérifie sur les années passées et cible les parcelles, nous ne l'avons pas trouvé (§10). |
| Votre concurrent le plus proche ? | Max Havelaar Origine France pour le prix plancher, FiLoLeG pour la marge face au blé : ni l'un ni l'autre ne raisonne en probabilité ni ne se vérifie sur les années passées. |
| Quel impact ? | Pour 5 000 t : 13 % des importations, 1 250 t de protéines, 630 t d'azote minéral en moins. |
| Ça passe à l'échelle ? | Même moteur pour cinq légumineuses et 24 départements ; un nouveau bassin, c'est relancer le pipeline. |
| Quelle taille de marché ? | 170 coopératives et unions du commerce de grains ; un secteur de 118 Md€. |

---

## 18. Les chiffres à savoir par cœur

- **39 371 t** importées en 2025, **46 %** de la consommation, **45 %** du Canada.
- Variabilité **0,20** contre **0,09** ; **2020 : −38 %**.
- **715 €/t** → 5 années sur 10 ; **900 €/t** → 6 ; **1 567 €/t** → 8.
- **+1 555 €/ha** les 8 bonnes années, **−581 €/ha** les 2 autres.
- Barème **1 635 / 750 / 650 €/t**, **−18 %**, **1 283 €/t** en moyenne.
- Backtest : **78 %** pour 80 % promis ; **29 %** avec les moyennes ; LightGBM **76 %** ; 133 cas, 2019–2025.
- **20 000** années simulées ; **16** ans de météo ; **24** séries de lentille, **294** couples.
- Pilote : **300 t**, **28 parcelles**, **216 ha**, **447 k€**, **1 489 €/t**, **85 k€** économisés.
- Import : **1 069 €/t** en 2025, **1 250 €/t** en 2022, **+53 %** depuis 2020.
- Bassin : **5 000 t**, **3 502 ha**, **13 %** des importations, **1 250 t** de protéines, **630 t** d'azote.
- Marché : **142 + 28 = 170** coopératives et unions ; **2 100** coopératives agricoles, **118 Md€**.
- France : de **558 €/t** (Pyrénées-Orientales) à **2 238 €/t** (Haute-Loire), **24** départements.

---

## 19. Glossaire

| Terme | Sens |
|---|---|
| Prix plancher, prix minimum garanti, P\* | prix que la coopérative s'engage à payer au minimum, fixé avant les semis |
| Départ ferme / rendu silo | prix à la sortie de la ferme / prix une fois la récolte livrée au site de collecte, transport compris |
| Tonnes acceptées au tri | récolte qui passe le tri de la coopérative (impuretés, calibre, bruche) ; seule elle est payée au prix garanti |
| Bruche | insecte qui perce les graines de lentille et fait déclasser les lots |
| Barème par tranches | prix différent pour la première tonne par hectare, la deuxième, et au-delà |
| Plancher indexé | prix minimum égal à un multiple du prix du blé de la récolte |
| Marge | produit de la culture moins ses charges opérationnelles (semences, engrais, traitements), en €/ha |
| Aide couplée | aide de la PAC versée par hectare de légumineuses à graines |
| Bénéfice de rotation, effet précédent | gain sur le blé qui suit une légumineuse : plus de rendement, moins d'azote |
| RPG | Registre parcellaire graphique : les parcelles déclarées chaque année à la PAC, avec leur culture |
| SAA, Agreste | Statistique agricole annuelle du ministère de l'Agriculture : surfaces et rendements par département |
| Régression quantile | modèle qui prédit un quantile (la mauvaise année, la médiane, la bonne année) plutôt que la moyenne |
| Perte pinball | mesure d'erreur adaptée aux quantiles |
| Calibration conforme | correction qui garantit qu'un intervalle à 80 % contient vraiment 80 % des valeurs réelles |
| Monte-Carlo | simulation de milliers de scénarios tirés au hasard pour obtenir une distribution |
| Backtest strict | test sur des années passées où le modèle n'utilise que les années d'avant : aucune fuite d'information |
| Couverture | part des récoltes réelles qui tombent dans l'intervalle prédit |
| LightGBM | modèle d'arbres de décision, souvent le plus précis sur des données tabulaires |
| NDVI | indice de végétation calculé sur les images satellite : plus il est haut, plus la culture est verte |
| Sirene, NAF 46.21Z | répertoire des entreprises de l'Insee ; code d'activité du commerce de gros de céréales |
| Consommation apparente | production + importations − exportations |
| Prime pure | coût moyen des sinistres d'une assurance, avant frais et marge de l'assureur |

---

## 20. Liens et documents détaillés

- Démo en ligne : https://main.d1lkeu0ybo1cz4.amplifyapp.com/ (simulateur : `#simulateur`)
- Code et données : https://github.com/nassim-arifette/hackthefork-hackathon
- Vidéo de la démo : `docs/video/demo-4min.mp4`
- Pitch et démo, écran par écran : [PITCH.md](PITCH.md) ; questions : [PITCH_NOTES.md](PITCH_NOTES.md)
- Résultats : [RESULTATS.md](RESULTATS.md) ; modèle : [MODELE.md](MODELE.md) ; limites : [LIMITES.md](LIMITES.md) ; sources : [SOURCES.md](SOURCES.md)
- Pilote et partenaires : [PILOTE_300T.md](PILOTE_300T.md) ; contrat simulé : [CONTRAT_SIMULATION.md](CONTRAT_SIMULATION.md) ; autres cultures : [REVUE_FILIERE_CULTURES.md](REVUE_FILIERE_CULTURES.md)
