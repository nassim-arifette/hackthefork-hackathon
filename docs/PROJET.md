> Document de contexte antérieur à la correction de validation. Les chiffres et engagements ci-dessous ne décrivent pas le scénario courant. Références à jour : [RESULTATS](RESULTATS.md), [MODELE](MODELE.md) et [DEMO_SCRIPT](DEMO_SCRIPT.md).

# Le projet dans sa globalité

Ce document explique le projet depuis le début : le problème, l'utilisateur, la solution, ce qui la distingue, comment elle se vend et pourquoi elle compte. Il sert de base au deck et à la fiche projet.

---

## 1. Le problème

### Le contexte

- La France veut produire plus de légumineuses pour l'alimentation humaine : elles apportent des protéines végétales et fixent l'azote de l'air, donc demandent moins d'engrais azoté sur la culture suivante.
- Les légumineuses occupent environ 4 % des terres agricoles françaises, avec un objectif de doublement d'ici 2030 (**sourcé**, guide participant). Terres Univia vise 1 million d'hectares (**sourcé**, voir [SOURCES.md](SOURCES.md)).
- Une part importante des lentilles consommées est importée. Le chiffre exact sera tiré des données douanières, code 0713 40 (**à mesurer**).

### Le verrou : le risque de revenu

Prenons un agriculteur de Seine-et-Marne qui cultive du blé.

- Le blé, il le connaît. En Seine-et-Marne, il fait environ 83 q/ha les années normales (**mesuré**, Agreste).
- La lentille varie beaucoup plus. Sur 2010–2025, son coefficient de variation national est de **0,20**, contre **0,09** pour le blé. Dans les principaux départements producteurs, il va de 0,24 à 0,38 (**mesuré**, Agreste SAA).
- En **2020**, le rendement national de la lentille est tombé à 8,2 q/ha, soit **−38 %** par rapport à la moyenne 2015–2019 (**mesuré**).

Une seule mauvaise année peut effacer plusieurs années de marge. L'agriculteur reste donc au blé. Le Track 3 nomme ce verrou : la crainte de perdre du revenu.

### La solution existante, et sa faille

Les contrats pluriannuels à prix minimum existent déjà, par exemple chez Qualisol (**sourcé**). La coopérative garantit un prix plancher et retire le risque de prix bas.

**Mais qui fixe ce prix, et comment ?**

- **Trop bas** : lors d'une mauvaise année, l'agriculteur gagne moins qu'en blé. Il ne renouvelle pas, et la filière perd ses surfaces.
- **Trop haut** : la coopérative paie trop cher, perd sa marge et ne peut plus revendre face aux importations.

Aujourd'hui, ce prix se fixe à l'expérience ou sur des moyennes. Or une moyenne ne dit rien du risque : un contrat qui rapporte « en moyenne » autant que le blé fait perdre de l'argent une année sur deux.

---

## 2. L'utilisateur et sa décision

- **Utilisateur** : le responsable filière d'une coopérative ou d'un conditionneur de légumes secs, acheteur pour l'alimentation humaine.
- **Décision** : « À quel prix plancher proposer un contrat lentille pluriannuel, et à quelles parcelles, pour sécuriser X tonnes sans faire prendre à l'agriculteur un risque plus grand qu'avec le blé ? »
- **Bénéficiaire indirect** : l'agriculteur, dont le revenu est sécurisé.

---

## 3. La solution

L'outil répond à une question précise : **quel prix minimum garantir pour que l'agriculteur gagne au moins autant qu'en blé 8 années sur 10 ?**

1. **Il apprend** comment la météo fait varier les rendements de la lentille et du blé, à partir de 16 ans de données Agreste et de la météo NASA POWER.
2. **Il simule** des milliers d'années possibles en rejouant des années météo historiques. Dans chacune, il compare la marge lentille sous contrat à la marge blé.
3. **Il en déduit le prix** qui fait gagner la lentille dans 80 % des scénarios, puis l'affine par parcelle avec le coût de transport jusqu'à l'acheteur.
4. **Il le prouve** sur des années que le modèle n'a jamais vues (backtest glissant 2019–2025).

Le responsable filière obtient un prix, une carte des parcelles qui acceptent ce prix, une courbe d'offre en tonnes, et une proposition de contrat rédigée en langage clair.

---

## 4. Ce qui différencie le projet

| | Pratique actuelle | Le Contrat qui Tient |
|---|---|---|
| Base du prix | expérience, moyennes | distribution du risque, conditionnée à la météo |
| Promesse à l'agriculteur | « en moyenne, ça rapporte » | « 8 années sur 10, au moins autant que le blé » |
| Ciblage | prospection au cas par cas | carte des parcelles qui basculent à ce prix |
| Preuve | aucune | backtest sur des années jamais vues |

- **Nous ne créons pas le contrat** : il existe déjà. Nous calculons le prix et le ciblage qui le rendent tenable.
- **Nous n'avons pas trouvé** d'outil qui calcule ce prix parcelle par parcelle et le calibre sur le risque. Formulation volontairement prudente.

---

## 5. Pourquoi l'IA est indispensable

Le test du guide participant : « Que perdrait la solution si on retirait la brique IA ? »

Sans modèle qui relie la météo à une **distribution** de rendement, on n'a qu'une moyenne. Et une moyenne ne permet pas de calculer un prix « tenable 8 années sur 10 ». La brique IA est le calcul lui-même, pas un habillage.

Le LLM n'intervient qu'à la fin, pour rédiger la proposition de contrat **à partir des chiffres calculés**. Il ne produit aucun chiffre.

---

## 6. L'impact

À chiffrer en unités physiques, toutes sourcées, au prix choisi :

- **hectares et tonnes** de lentilles pour l'alimentation humaine, comparés aux importations (douanes 0713 40) ;
- **protéines produites**, avec la teneur en protéines de la lentille sèche (Ciqual) ;
- **azote minéral évité** sur la culture suivante, et émissions évitées en CO2e (ADEME Base Empreinte ou HESTIA) ;
- **revenu sécurisé** : une marge au moins égale au blé 8 années sur 10, mesurée en backtest.

Pour le pois, l'effet précédent est sourcé : +7 q/ha sur le blé suivant et −33 kg N/ha (Intercéréales et Terres Univia). Pour la lentille, la valeur reste **à sourcer** chez Terres Inovia ; à défaut, elle est affichée comme hypothèse.

---

## 7. Le modèle économique

### Qui paie

Les coopératives et les conditionneurs de légumes secs. Ils ont le problème, le budget, et prennent cette décision à chaque campagne.

### La valeur, en euros

- **Prix trop haut** : 20 €/t de trop sur 5 000 t contractualisées représentent 100 k€ de marge perdue par campagne (**supposé**, exemple de calcul).
- **Prix trop bas** : après une année comme 2020, les agriculteurs ne renouvellent pas, et la filière doit reconstruire ses surfaces.

### L'offre (hypothèses à tester)

- abonnement par campagne et par coopérative ;
- ou prix à la tonne contractualisée, aligné sur la valeur créée.

Les montants sont des **hypothèses** à valider avec des coopératives.

### Le chemin d'adoption

1. **Pilote** avec une coopérative qui monte déjà une filière légumineuses, par exemple en Beauce, où une filière existe avec prime filière et assurance rendement (**sourcé**).
2. **Coopératives déjà engagées** dans des contrats à prix minimum.
3. **Nouvelles filières** créées dans le cadre du plan protéines : chacune devra fixer un prix.

### Le passage à l'échelle

La lentille seule est un petit marché : environ 34 000 ha en 2025 (**mesuré**). C'est la porte d'entrée. Le même moteur s'applique ensuite :

- **à toutes les cultures sous contrat** : pois chiche, haricot sec, chanvre, sorgho, cultures bas carbone ;
- **aux assureurs agricoles**, qui ont besoin de la même distribution de rendement pour tarifer ;
- **aux industriels de l'agroalimentaire** qui veulent sécuriser un approvisionnement français.

### Risques business

- marché de départ étroit ;
- cycle de vente long dans les coopératives ;
- réponse : un pilote d'une campagne, puis conversion.

---

## 8. Correspondance avec la grille du jury

| Critère | Poids | Ce que le projet apporte |
|---|---|---|
| Impact et durabilité | 30 % | lève le verrou du Track 3 ; impact en hectares, tonnes, azote et importations |
| Rigueur scientifique | 20 % | backtest sans fuite, baseline naïve, couverture mesurée, limites annoncées |
| Usage pertinent de l'IA | 20 % | sans distribution de rendement, pas de prix calibré sur le risque |
| Viabilité économique | 20 % | client identifié qui paie chaque campagne, extension aux assureurs |
| Exécution et pitch | 10 % | démo hors ligne, un parcours unique, chiffres étiquetés |
