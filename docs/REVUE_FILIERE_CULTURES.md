# Revue filière : les hypothèses à retenir pour les autres légumineuses

**Avis de mentor documenté du 31 octobre 2026.** L'objectif est de choisir des paramètres défendables pour le hackathon et de comparer des contrats. Les valeurs retenues figurent dans [data/cultures.yaml](../data/cultures.yaml). Cet avis repose sur des publications et des hypothèses de travail ; il ne représente pas l'engagement d'un acheteur contacté.

## 1. Les décisions

**Je conserve 500 €/ha pour le pois chiche et 400 €/ha pour la féverole, relève le pois à 450 €/ha et fixe le haricot sec irrigué à 1 000 €/ha.** Le changement principal concerne le haricot : ses 700 €/ha deviennent le budget d'intrants, auquel s'ajoutent 300 €/ha d'eau et d'énergie.

| Culture conventionnelle | Charges centrales | Sensibilité des charges | Référence de prix à afficher |
|---|---:|---|---|
| Pois chiche | **500 €/ha** | 400 / 500 / 600 | **600–620 €/t**, prix payé rapporté pour la récolte 2025 dans la filière Cavac standard. |
| Haricot sec irrigué | **1 000 €/ha** | 700 / 1 000 / 1 300 | **900–1 500 €/t**, intervalle de scénario, centre **1 200 €/t**. |
| Pois protéagineux | **450 €/ha** | 350 / 450 / 550 | **200–260 €/t**, référentiel économique CRIT 2025 ; variante alimentaire à **280 €/t**. |
| Féverole | **400 €/ha** | 300 / 400 / 500 | **200–260 €/t**, même référentiel ; variante alimentaire à **290 €/t**. |

Les prix du tableau ont des statuts différents : paiement observé, référence de plan d'entreprise ou choix de scénario. Le milieu de 200–260 vaut 230 €/t ; ce calcul ne constitue pas une cotation du jour.

## 2. Un périmètre de charges commun

Les charges centrales couvrent semences, fertilisation, protection et dépenses culturales directes. Elles excluent **mécanisation, travail, fermage, frais généraux et tri aval**, comme le scénario de comparaison au blé. Pour le haricot irrigué, les consommations variables d'eau et d'énergie sont incluses ; l'investissement et l'amortissement de l'installation restent exclus.

Un coût complet comprenant récolte et conditionnement ne peut donc pas remplacer directement ce paramètre. Ces postes ont leur place dans un budget complémentaire, avec le même périmètre pour toutes les cultures et un payeur identifié. Le résultat du moteur est une comparaison de marges selon ce périmètre, pas un revenu net d'exploitation.

## 3. Haricot sec : reconstruire le budget plutôt que reprendre celui du blé

### Le scénario central à adopter

| Poste | Hypothèse |
|---|---:|
| Semences | 400 €/ha |
| Fertilisation | 150 €/ha |
| Protection de la culture | 150 €/ha |
| **Intrants** | **700 €/ha** |
| Eau et énergie d'irrigation | 300 €/ha |
| **Total central** | **1 000 €/ha** |

Cette décomposition est une **construction de scénario**, pas un devis recopié. Elle rend explicite ce qui manquait dans les 700 €/ha initiaux : l'irrigation d'une culture conduite avec un accès à l'eau.

Des références publiques existent. Un [retour de filière en Limagne publié en 2019](https://www.pleinchamp.com/actualite/grandes-cultures~comment-produire-du-haricot-sec-en-limagne) mentionne 340 €/ha de semences, 450 €/ha de récolte, et des contrats à 830 €/t pour le blanc et 990 €/t pour le rouge. Ce sont des repères historiques, avec une récolte à tenir hors du paramètre d'intrants actuel.

La [fiche flageolet de Bio Nouvelle-Aquitaine, p. 3](https://www.bionouvelleaquitaine.com/wp-content/uploads/2023/02/Flageolet.pdf) détaille 500 €/ha de semences, 450 d'irrigation, 100 de mécanisation et 250 de récolte, soit 1 300 €/ha. **Ce cas est biologique** : son total ne se transpose pas au haricot conventionnel. Il montre cependant que l'irrigation et la récolte peuvent représenter des postes majeurs.

Je propose deux lectures de sensibilité : 700 / 1 000 / 1 300 €/ha pour le budget global ; ou, à intrants constants, 0 / 300 / 450 €/ha d'irrigation, soit 700 / 1 000 / 1 150 €/ha. Le scénario sans irrigation doit rester associé à des conditions de rendement adaptées ; changer seulement le coût ne simule pas l'effet de l'eau sur la récolte.

### Le prix de travail : 1 200 €/t

Le [barème officiel de l'Indre-et-Loire pour les pertes de sécheresse 2025](https://www.indre-et-loire.gouv.fr/Actions-de-l-Etat/Agriculture-foret-et-developpement-rural/Agriculture/Les-pertes-aides-de-crises-et-indemnisations/Secheresse-de-mai-a-aout-2025), publié pour la procédure de 2026, retient **1 188 €/t en conventionnel** et 2 138 €/t en bio. Ce montant sert à l'indemnisation : il ne décrit pas un prix de marché ni une offre d'achat.

**Je choisis néanmoins 1 200 €/t comme centre de scénario**, avec une plage 900–1 500, en rapprochant ce repère administratif des contrats historiques. Cela fournit une hypothèse économique immédiatement testable. L'interface doit afficher « scénario haricot » et conserver la provenance du repère de 1 188 €/t.

## 4. Pois chiche : les 500 €/ha sont étayés

Le [guide Terres Inovia 2026, p. 4](https://www.terresinovia.fr/sites/default/files/2026-04/guide_culture_pois-chiche_2026_terresinovia.pdf) a été consulté intégralement. Son itinéraire conventionnel totalise **416–583 €/ha**, et sa matrice de marge utilise **480 €/ha**. Les semences représentent 312 €/ha ; l'inoculation peut ajouter jusqu'à 50 €/ha, notamment dans les bassins Nord et Est.

**500 €/ha constitue donc un bon arrondi de travail.** Le poste de désherbage mécanique du tableau vaut zéro en conventionnel ; les 51 €/ha concernent la colonne biologique. La mention générale du désherbage mécanique ne justifie pas de réduire notre budget conventionnel.

Le guide estime l'avantage de précédent jusqu'à 150 €/ha, avec environ 40 unités d'azote économisées sur le blé suivant. Nous conservons 150 comme choix de scénario avec rotation, sous le statut `suppose` ; le plafond publié n'est pas une moyenne mesurée sur nos parcelles.

### Le prix n'est plus un champ vide

Dans un [témoignage publié le 27 juin 2026](https://www.reussir.fr/formats/temoignages/pois-chiche-label-rouge-la-culture-degage-la-meilleure-marge-de-mon), un producteur Pulseo/Cavac rapporte **600–620 €/t effectivement payés pour du pois chiche standard récolté en 2025**. Ce repère est utilisable, en indiquant sa filière et son millésime. Son rendement particulier ne remplace pas la série de rendement du modèle.

Un autre contrat peut enrichir le pitch : [Max Havelaar France, document de janvier 2026, p. 5 et 9](https://www.fairtrade.net/content/dam/fairtrade/max-havelaar-france/label-origine-france/Prix-minimum-Max-Havelaar-France-2025.pdf), publie pour la récolte 2025 un minimum de **769 €/t en conventionnel** dans les deux Charentes, les Deux-Sèvres et la Vienne. S'y ajoute une prime collective de 38 €/t. C'est une filière équitable particulière ; la prime collective reste distincte du paiement individuel du producteur.

## 5. Pois et féverole : deux budgets voisins, avec leurs propres références

### Pois protéagineux : relever à 450 €/ha

Les scénarios du [guide pois conventionnel Terres Inovia 2025, p. 3](https://www.terresinovia.fr/sites/default/files/2025-05/guide-de-culture-pois-conventionnel-2025.pdf) permettent de reconstituer les charges en conservant l'aide de 110 €/ha incluse dans la marge publiée :

```text
Cas à 4,5 t/ha : 4,5 × 250 + 110 − 810 = 425 €/ha
Cas à 3,5 t/ha : 3,5 × 250 + 110 − 500 = 485 €/ha
```

**450 €/ha est l'arrondi retenu**, au milieu de ces deux cas. Ce calcul déduit un budget de références économiques publiées ; il ne mesure pas les charges de chaque exploitation. La sensibilité 350 / 450 / 550 couvre des itinéraires plus sobres ou plus coûteux.

### Féverole : conserver 400 €/ha

Le [guide féverole Terres Inovia 2024, p. 3](https://www.terresinovia.fr/sites/default/files/2025-06/guide-de-culture-feverole-conventionnel-2024.pdf) situe les charges opérationnelles à **300–400 €/ha**. Je retiens le haut de cette plage pour le scénario central et garde 300 / 400 / 500 en sensibilité. Il n'est plus nécessaire de justifier ce chiffre uniquement par sa proximité avec le pois.

### Prix : identifier le débouché

Le [référentiel CRIT Grand Est du 16 avril 2025](https://draaf.grand-est.agriculture.gouv.fr/IMG/pdf/crit_16_avril_2025___annexe_2___referentiel_des_prix_crit_2025.pdf) fournit **200–260 €/t** pour les pois protéagineux et féveroles. Nous conservons cette référence destinée aux plans d'entreprise, sans la présenter comme une cotation actuelle.

Pour une filière alimentaire, ajouter deux variantes explicites : **280 €/t pour le pois et 290 €/t pour la féverole**. Le guide pois 2025, p. 3, utilise 280 €/t pour l'alimentation humaine dans une projection Cerfrance fondée sur le contexte de récolte 2024. Le guide féverole 2024, p. 3, propose une plage indicative alimentaire de 260–320 €/t ; nous en retenons le milieu à 290. Leur reconduction dans le scénario est un choix d'équipe. Ces débouchés supposent leurs critères de qualité ; la prime ne s'applique pas automatiquement à toute la collecte.

## 6. Les hypothèses communes restent des choix exploitables

L'aide demeure **105 €/ha**, montant indicatif 2026 de la [notice Telepac, p. 4](https://www.telepac.agriculture.gouv.fr/telepac/pdf/tas/2026/Dossier-PAC-2026_notice_aides-couplees.pdf). Le bonus de rotation reste **150 €/ha pour chaque culture**, étiqueté `suppose`, avec des variantes à 0 / 100 / 150. Afficher la marge de campagne puis celle avec rotation permet de voir ce que ce pari apporte.

Les fractions non valorisées au prix garanti restent **10 % pour pois chiche et haricot**, **5 % pour pois et féverole**. Elles sont des hypothèses de scénario. Une fraction déclassée peut avoir une valeur dans un autre débouché : une recette secondaire pourra être ajoutée séparément, plutôt que de confondre automatiquement déclassement commercial et disparition de matière.

## 7. Effet du recalcul sur la démonstration

Les exports [data/cultures.json](../data/cultures.json) et [app/src/data/cultures.json](../app/src/data/cultures.json) ont été régénérés avec `pipeline/09_cultures.py`, sur les mêmes données et avec les mêmes graines aléatoires. Avant modification, ce pipeline a reproduit les deux exports existants à l'octet près. Après modification, l'objet lentille complet reste identique. Les valeurs ci-dessous sont **calculées par le modèle**, avec les nouveaux budgets centraux.

| Culture | Ancien P\* en Seine-et-Marne | Nouveau P\* | Prix de comparaison retenu | Scénarios où la culture bat le blé à ce prix |
|---|---:|---:|---:|---:|
| Pois chiche | 1 064 €/t | **1 064 €/t** | 610 €/t, milieu du paiement rapporté 2025 | **27,2 %** |
| Haricot sec | 1 779 €/t | **2 185 €/t** | 1 200 €/t, centre du scénario | **58,9 %** |
| Pois protéagineux | 409 €/t | **427 €/t** | 230 €/t, milieu du référentiel CRIT | **24,0 %** |
| Féverole | 462 €/t | **462 €/t** | 230 €/t, milieu du référentiel CRIT | **23,4 %** |

P\* est le prix qui permet de battre la marge du blé dans 80 % des simulations, avec aide, rotation et fraction non valorisée. Il n'est pas un prix payé observé. Ajouter une référence de prix ne modifie pas P\* : cela permet de calculer la fréquence de réussite à cette référence. Les hausses de P\* du haricot et du pois proviennent des charges révisées.

Les contrats indexés sur le blé tiennent dans **78 à 89 % des cas du backtest 2019–2025**, contre **65 à 70 % pour le prix fixe**, sur les quatre cultures. Ces taux suivent le protocole strict du 31/10 : pour chaque année test, les séries départementales en double sont regroupées avec les seules années antérieures. Le détail par culture et les barèmes recalibrés sont dans [RESULTATS.md](RESULTATS.md) et les exports. Les valeurs de sensibilité du YAML sont des variantes disponibles ; ce recalcul porte sur le scénario central.

**Conséquence pour le pitch :** le haricot est un cas de contrat à forte valeur, dont l'accès à l'eau compte dans le budget. Le pois et la féverole demandent surtout de construire un débouché et une rémunération suffisants face au blé francilien. Un coût mieux documenté ne suffit pas, à lui seul, à rendre la substitution attractive au prix de référence.

**Position à défendre devant le jury :** les coûts du pois chiche, du pois et de la féverole sont ancrés dans des références techniques identifiées. Le haricot dispose d'un budget reconstruit, avec l'irrigation visible et une plage de prix assumée. Chaque hypothèse peut varier sans bloquer la démonstration.
