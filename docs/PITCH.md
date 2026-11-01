# Pitch et démo : les 4 minutes

Le texte à dire et la démo à piloter, écran par écran. 4 minutes de présentation arrêtées net, puis 2 minutes de questions. Une personne parle, l'autre pilote le clavier.

- **Chaque geste suit une phrase**, pas l'horloge : la personne au clavier écoute la phrase indiquée, puis agit.
- **Les heures sont des limites**, pas des rendez-vous : on avance dès que le texte d'un écran est dit. L'écran 6 a besoin de 55 secondes : il doit commencer au plus tard à 2:55.
- Le texte compte environ 445 mots, soit à peu près 3 min 40 à un débit posé, gestes compris : il reste une vingtaine de secondes avant l'arrêt.

Application : https://main.d1lkeu0ybo1cz4.amplifyapp.com/ ; tout le projet : [DOSSIER.md](DOSSIER.md). Les chiffres viennent des exports du pipeline ([RESULTATS.md](RESULTATS.md)) ; leur statut est donné dans « Les chiffres cités ». Les questions du jury et leurs réponses sont en fin de document.

## Avant de passer

- [ ] Ordinateur commun branché au projecteur et testé ; secteur branché, mise en veille et notifications coupées.
- [ ] Application ouverte depuis un favori, en plein écran (`F11`). Sous 720 px de haut, dézoomer d'un cran (`Ctrl` + `−`) ; le panneau de droite réduit seul son texte jusqu'à 72 %.
- [ ] **Page rechargée juste avant le passage** : elle s'ouvre sur l'écran 1, avec le site de collecte du scénario. Un site déplacé dans une annexe ou dans le simulateur resterait utilisé par les écrans 3, 4 et 6.
- [ ] Clé USB : la version hors ligne (`app/dist-single/index.html`, identique à la version en ligne, polices comprises) et la vidéo de secours (`docs/video/demo-4min.mp4`).
- [ ] Chronomètre visible par la personne qui parle.
- [ ] Jamais d'éditeur ni de terminal à l'écran.

Commandes : `Espace` écran suivant, `Maj` + `Espace` écran précédent, `←` `→` prix à l'écran 4, `F` carte de France à l'écran 6, `M` méthode, `Échap` pour la fermer ; bouton « Simulateur » et menu « Annexes » en haut à droite.

## Le déroulé

### 1 · Le constat · 0:00 → 0:20 au plus tard

**À l'écran** : dix bols de lentilles, dont cinq importés ; des cargos rejoignent les ports ; la provenance des importations.

> « Près d'une lentille sur deux mangée en France vient de l'étranger : 39 000 tonnes en 2025, surtout du Canada. Nos champs pourraient les produire. Alors pourquoi les agriculteurs n'en sèment-ils pas ? »

**Au clavier** : `Espace` après « …n'en sèment-ils pas ? »

### 2 · Le pari · → 0:45 au plus tard

**À l'écran** : les récoltes de blé et de lentille, année par année ; les parcelles de blé d'Île-de-France en ocre.

> « Parce que c'est un pari. Avec le blé, l'agriculteur sait ce qu'il va gagner. La lentille, elle, varie deux fois plus : en 2020, sa récolte a chuté de 38 %. Une seule mauvaise année efface sa marge. Alors, rester au blé, c'est le choix raisonnable. »

**Au clavier** : `Espace` après « …le choix raisonnable. »

### 3 · Le contrat · → 1:10 au plus tard

**À l'écran** : la filière animée, du champ à l'assiette ; la carte descend vers le site de collecte.

> « La solution existe : un contrat. La coopérative, l'entreprise des agriculteurs qui collecte et revend leurs récoltes, peut leur garantir un prix minimum avant les semis. Mais lequel ? Trop bas, l'agriculteur perd et ne recommence pas. Trop haut, c'est la coopérative qui perd. Notre utilisatrice, c'est sa responsable filière, et c'est sa question. »

**Au clavier** : `Espace` après « …et c'est sa question. »

### 4 · Le prix : la démo · → 2:15 au plus tard

**À l'écran** : le prix part de 900 €/t et monte seul, en six secondes, jusqu'à 1 600 €/t livré au silo ; les orages rouges disparaissent, les parcelles proches du silo passent au vert, les camions arrivent, le compteur monte à 300 t. Ne rien toucher pendant la montée.

> « Voici notre outil. À 900 euros la tonne, le prix payé par une coopérative en 2023, la lentille rapporte moins que le blé 4 années sur 10 : ce sont ces orages. L'outil calcule le prix qui protège l'agriculteur 8 années sur 10 : 1 567 euros en Seine-et-Marne. Et ces 8 années-là, il gagne en moyenne 1 555 euros de plus par hectare qu'avec du blé. À ce prix, les parcelles les plus proches du silo basculent : 300 tonnes, 28 parcelles. »

**Au clavier**, après « …28 parcelles. » : maintenir `←` jusque vers 1 000 €/t.

> « Si la coopérative paie moins, regardez : les orages reviennent, les parcelles repassent au blé. »

**Au clavier**, après « …repassent au blé. » : maintenir `→` jusqu'à 1 600 €/t.

> « Et l'outil trouve le contrat le moins cher : payer plus cher la première tonne, celle qui manque les mauvaises années, protège autant pour 18 % de moins. »

**Au clavier** : `Espace` après « …18 % de moins. »

### 5 · La preuve · → 2:55 au plus tard

**À l'écran** : la carte de France rejoue 2019–2025, département par département ; dix contrats sans modèle, dix avec.

**Si l'écran 5 commence après 2:15**, s'arrêter à « …pas la moyenne. » et sauter la phrase sur LightGBM.

> « Est-ce que ça tient vraiment ? On a remonté le temps : chaque année de 2019 à 2025, le modèle n'apprend que sur le passé, fixe le prix, puis on regarde la vraie récolte. Un prix calculé sur les moyennes aurait tenu 3 contrats sur 10. Le nôtre en tient 8 : 78 % pour 80 % promis. Notre IA, une régression quantile, apprend sur 16 ans de météo à prévoir les mauvaises années, pas la moyenne : LightGBM, plus précis en moyenne, en tient moins. »

**Au clavier** : `Espace` après « …en tient moins. »

### 6 · L'impact et le passage à l'échelle · → 3:50 au plus tard

**À l'écran** : les compteurs du bassin de 5 000 t, 260 parcelles et leurs camions ; puis la carte de France des prix ; puis le simulateur.

> « Si un bassin atteint 5 000 tonnes : 13 % des importations, 1 250 tonnes de protéines, 630 tonnes d'azote minéral en moins, et des agriculteurs protégés 8 années sur 10 au lieu de 6. »

**Au clavier** : `F` après « …au lieu de 6. »

> « Le même calcul marche partout. »

**Au clavier** : clic sur « Simulateur », en haut à droite, après « …partout. »

> « Nos charges sont des moyennes. Le produit, c'est ce simulateur : la coopérative y entre ses propres chiffres et obtient son contrat, ses parcelles et son budget. Nos clients, ce sont les 170 coopératives qui font le commerce des grains en France. Elles paient un abonnement par campagne, bien moins que les 85 000 euros que le bon contrat leur fait économiser sur un pilote de 300 tonnes. Prochaine étape : ce pilote. Le Contrat qui Tient. »

Silence. Ne rien ajouter.

## Les phrases repères

On apprend les transitions, pas le texte mot à mot :

1. « Alors pourquoi les agriculteurs n'en sèment-ils pas ? »
2. « Parce que c'est un pari. »
3. « La solution existe : un contrat. Mais lequel ? »
4. « Voici notre outil. »
5. « Est-ce que ça tient vraiment ? »
6. « Si un bassin atteint 5 000 tonnes… »
7. « Le Contrat qui Tient. »

## Si la démo plante

1. Rester calme : « Je vous montre la version enregistrée pendant qu'on relance. »
2. Lancer `docs/video/demo-4min.mp4` en plein écran. Elle est muette et garde son propre minutage : écran 2 à 0:25, écran 3 à 1:00, écran 4 à 1:25, écran 5 à 2:40, écran 6 à 3:20, carte de France à 3:42. Suivre ses changements d'écran.
3. Dire le même texte, en sautant ce qu'elle ne montre pas : « Si la coopérative paie moins… » et la phrase sur le simulateur. Garder les clients, l'abonnement, la prochaine étape et le nom.
4. Si le direct revient, le reprendre.

## Règles

- Répéter au chronomètre deux ou trois fois, dont une devant quelqu'un d'extérieur.
- À l'écran 4, laisser le prix monter seul : les camions partent quand il atteint 1 600 €/t livré au silo.
- Si un chiffre n'est pas à jour, la phrase est retirée, jamais remplacée par une estimation.
- Version en ligne déployée par Amplify à chaque mise à jour de `main` ; version hors ligne identique.

## Les chiffres cités

| Dans le pitch | Valeur exacte | Statut | Source |
|---|---|---|---|
| près d'une lentille sur deux, 39 000 t importées en 2025, surtout du Canada | 46 % de la consommation apparente ; 39 371 t, dont 45 % du Canada | sourcé | Eurostat Comext ; Agreste SAA |
| la lentille varie deux fois plus | coefficient de variation du rendement national 0,20, contre 0,09 pour le blé, 2010–2025 | mesuré | Agreste SAA |
| en 2020, sa récolte a chuté de 38 % | rendement national de 8,2 q/ha, 38 % sous la moyenne 2015–2019 | mesuré | Agreste SAA |
| 900 €/t, moins que le blé 4 années sur 10 ; protégés 8 années sur 10 au lieu de 6 | prix Unéal 2023 ; à ce prix, la lentille bat le blé 6 années sur 10 | sourcé (prix), modèle (fréquence) | Unéal ; 20 000 années simulées |
| 1 567 €/t, 8 années sur 10 | prix départ ferme, Seine-et-Marne, payé sur les tonnes acceptées au tri ; 1 600 €/t à l'écran, livré au silo | modèle | 20 000 années simulées (météo NASA POWER, prix du blé 2010–2025) |
| 1 555 €/ha de plus ces 8 années | écart moyen lentille − blé les années gagnantes | modèle | 20 000 années simulées |
| 300 t, 28 parcelles | 216 ha, à moins de 3,2 km du site de collecte | modèle ; site fictif annoncé comme tel | RPG 2025 (IGN) |
| 18 % de moins | barème 1 635 / 750 / 650 €/t, 1 283 €/t en moyenne contre 1 567 €/t | modèle | 20 000 années simulées |
| 3 contrats sur 10 contre 8 ; 78 % pour 80 % promis | 29 % et 78 % de 133 contrats, 2019–2025 | mesuré (backtest strict) | récoltes Agreste SAA, météo NASA POWER |
| une régression quantile, 16 ans de météo | modèle M1, choisi avant le backtest ; météo 2010–2025 | sourcé (météo) | NASA POWER ; [MODELE.md](MODELE.md) |
| LightGBM en tient moins | 76 % | mesuré (backtest strict) | idem |
| 5 000 t, 13 % des importations | 12,7 % des importations 2025 | supposé (ambition de bassin) | Eurostat Comext |
| 1 250 t de protéines, 630 t d'azote minéral | 25 % de protéines ; 180 kg N/ha de blé remplacé | sourcé (coefficients), appliqué à un volume supposé | Terres Inovia ; Agreste, Mémento DRIAAF 2025 |
| nos charges sont des moyennes | 700 €/ha pour le blé, 500 €/ha pour la lentille, arrondis de références publiées | supposé | Cerfrance Nord-Est Île-de-France ; Terres Inovia |
| 170 coopératives | 142 coopératives agricoles et 28 unions du commerce de gros de céréales | mesuré | Sirene (Insee), 31/10/2026 |
| un abonnement par campagne | étude pilote à 3 000 €, puis 10 000 € par campagne et par bassin | supposé, à valider avec les premiers clients | [QUESTIONS.md](QUESTIONS.md) |
| 85 000 € par campagne sur 300 t | achat 470 k€ au prix unique, 385 k€ au barème par tranches | modèle | 20 000 années simulées |

## Les questions (2 minutes)

Répondre en une phrase, chiffre compris ; détailler seulement si le jury relance. N'ouvrir une annexe que si elle répond mieux qu'une phrase : elle est indiquée sous la réponse. Si la réponse n'est pas connue, le dire franchement et dire quelle donnée la donnerait. Chiffres : [RESULTATS.md](RESULTATS.md) ; contexte complet : [DOSSIER.md](DOSSIER.md).

### Ce qu'il faut faire passer

En une phrase : « Le Contrat qui Tient calcule le prix minimum d'un contrat lentille qui rapporte à l'agriculteur au moins autant que le blé 8 années sur 10, et montre quelles parcelles basculent à ce prix. »

1. **Le verrou est mesuré** : la lentille varie deux fois plus que le blé ; aux prix de 2012–2016, elle ne gagne qu'une année sur deux face au blé francilien.
2. **Le prix est calibré sur le risque, et vérifié** : 78 % des contrats tenus pour 80 % promis, sur des années jamais vues.
3. **L'outil trouve le bon contrat** : le barème par tranches protège autant pour 18 % de moins.
4. **Il y a un client qui paie** : la coopérative, à chaque campagne ; 170 coopératives et unions font le commerce des grains.

### Les annexes à ouvrir

- **Simulateur** : changer une hypothèse et montrer le bandeau du haut. Protection à 7 années sur 10 → 1 132 €/t ; sans aide couplée → 1 709 €/t ; 20 % refusés au tri → 1 763 €/t.
- **Le prix, en détail** : courbe de fiabilité, contrats existants, prix plancher par département.
- **Deux mauvaises années, rejouées** : 2016 (le blé s'effondre) et 2020 (la lentille s'effondre), touches `1` et `2`.
- **Le test, en détail** : fourchettes prédites et récoltes réelles, comparaison des modèles, poids de la météo.
- **La proposition de contrat** : barème par tranches, lettre au producteur, comparaison des contrats, sites de collecte existants, autres légumineuses.
- **La saison, vue par satellite** et **Vu du ciel** : prototypes Sentinel-2.

Après les questions, recharger la page avant l'équipe suivante si l'ordinateur est partagé.

### Le produit et l'utilisatrice

**C'est quoi, le produit ?**
L'application : le parcours des six écrans et le simulateur. La responsable filière y entre ses charges, son tri, la protection voulue, son volume et son prix de revente ; elle obtient le barème à proposer, ses parcelles, son budget et l'écart avec l'import, recalculés en direct sur les 20 000 années simulées.
*À montrer : le simulateur.*

**Qui est l'utilisatrice, et quelle décision prend-elle ?**
La responsable filière d'une coopérative, ou d'un conditionneur, qui développe la lentille. Avant les semis, elle décide à quel prix minimum proposer un contrat de trois campagnes, pour combien de tonnes et à quelles parcelles.

**C'est quoi une coopérative, et pourquoi voudrait-elle cet outil ?**
L'entreprise des agriculteurs adhérents, qui en sont propriétaires : elle collecte leurs récoltes, les trie, les stocke, les revend, et signe les contrats de production. Elle veut des volumes d'origine France pour ses clients et des rotations plus diversifiées pour ses adhérents, sans surpayer ni perdre ses surfaces après une mauvaise année.

**C'est quoi un conditionneur, et où sont les distributeurs ?**
Le conditionneur nettoie, calibre et ensache les légumes secs : Vivien Paille avec Unéal, Lunor chez NatUp. Il vend aux magasins, à la restauration collective et aux industriels. La chaîne : agriculteur, coopérative, conditionneur, magasin ou cantine.

**D'où viennent les lentilles importées ?**
Du Canada pour 45 %, de Belgique pour 37 % (pays d'expédition, qui en produit peu), de Turquie pour 6 % (Comext 2025).

### L'agriculteur

**Pourquoi accepterait-il « au moins autant que le blé 8 années sur 10 », alors qu'avec le blé il pourrait gagner plus ?**
Parce que 8 sur 10 est un plancher, pas la moyenne. Ces 8 années, la lentille sous contrat rapporte en moyenne 1 555 €/ha de plus que le blé de la même année ; les 2 autres, 581 €/ha de moins. En moyenne, +1 128 €/ha au prix unique et +722 €/ha avec le barème par tranches, pour une marge de blé de 869 €/ha. Sans contrat assez haut, il reste au blé : à 900 €/t, la lentille ne gagne que 6 années sur 10.

**Pourquoi pas 10 années sur 10 ? Le but, c'est un prix élevé ?**
Non : le but est le prix le plus bas qui tient la promesse. Protéger plus coûte vite très cher : 1 132 €/t pour 7 années sur 10, 1 567 pour 8, 2 632 pour 9, 4 397 pour 9,5, car les mauvaises années de lentille sont rares mais profondes. Au-dessus de 80 % de contrats tenus, la coopérative surpaie ; en dessous, l'agriculteur est trompé. La coopérative choisit son niveau dans le simulateur.
*À montrer : annexe « Le prix, en détail », courbe de fiabilité.*

**Il fait lentille et blé la même année ?**
Pas sur la même parcelle : une parcelle donne une récolte par an. La lentille est semée vers mars et récoltée fin juillet ; le blé suivant est semé en octobre et récolté l'été d'après. Sur l'exploitation, oui : quelques parcelles en lentille, les autres restent en blé. La décision se prend à l'automne, avant de semer le blé : d'où un prix garanti avant les semis.

**Un contrat de trois campagnes, alors que la lentille ne revient pas chaque année sur la même parcelle ?**
Le contrat engage l'exploitation, pas une parcelle : chaque année, la lentille va sur une autre parcelle. Le délai de retour n'est pas encore dans le modèle ; c'est pour ça que les volumes visés restent modestes : 216 ha pour le pilote, 3 502 ha pour le bassin, face à 117 000 ha de blé en Seine-et-Marne.

**« La lentille fixe l'azote de l'air et améliore le blé suivant », ça veut dire quoi ?**
Des bactéries sur ses racines captent l'azote de l'air : la lentille n'a pas besoin d'engrais azoté. Le blé qui la suit rend plus avec moins d'engrais : +7 q/ha et −55 kg d'azote par hectare (FiLoLeG / Agro-Transfert). On en compte 150 €/ha dans la marge ; sans ce bénéfice, le prix passerait à 1 773 €/t.

**Vous payez quelles tonnes ? Et la bruche ?**
Les tonnes acceptées au tri, comme dans tout contrat de collecte : un lot refusé (bruche, impuretés, calibre) ne touche pas le prix garanti. On retire 10 % de la récolte, une seule fois. À 0 % de refus, le prix serait de 1 411 €/t ; à 20 %, de 1 763 €/t.

**Ça finit au bétail ?**
Non : des lentilles pour l'alimentation humaine, achetées par un conditionneur de légumes secs.

**Et si une année comme 2016 ou 2020 revenait ?**
À 1 600 €/t en Seine-et-Marne : en 2016, quand le blé perd 53 %, la lentille sous contrat rapporte 1 757 €/ha contre −84 €/ha pour le blé ; en 2020, quand la lentille perd 38 %, 1 181 €/ha contre 771. Les parcelles tiennent les deux années.
*À montrer : annexe « Deux mauvaises années, rejouées ».*

**Un prix plancher, c'est une assurance ?**
Non. Il protège la marge face au blé 8 années sur 10 ; une récolte effondrée reste un risque. Les deux se complètent : avec la même distribution de récolte, une assurance rendement à 70 % coûterait 231 €/ha de prime pure en Seine-et-Marne, avec un sinistre 3 années sur 10.

### La coopérative, l'import et le business

**Qui paie 1 567 €/t ?**
Personne en moyenne : c'est le prix unique, le cas le plus cher. Avec le barème par tranches, la coopérative paie 1 283 €/t pour la même protection, 1 489 €/t avec le tri et la collecte. L'import coûtait 1 069 €/t en 2025 et 1 250 €/t en 2022.

**1 567 €/t, c'est plus du double des prix observés !**
Oui, et c'est le résultat : garantir 8 années sur 10 face au blé francilien coûte cher. 900 €/t, le prix d'Unéal en 2023, ne protège que 6 années sur 10. Les leviers sont dans l'outil : forme du contrat, niveau de protection, aide couplée, autres bassins.

**Alors ce n'est pas intéressant pour la coopérative, face à l'import ?**
En Île-de-France, le pilote coûte plus que l'import : 420 €/t de plus qu'en 2025, environ 290 €/t sur 2022–2024. Trois leviers. Un débouché qui paie l'origine France : l'écart fait environ 21 centimes par sachet de 500 g, et achète trois ans de prix stable, alors que l'import a pris 53 % entre 2020 et 2022. Un bassin moins cher : 558 €/t dans les Pyrénées-Orientales, 842 dans l'Hérault, 900 dans le Gard. Un niveau de protection plus bas : 1 132 €/t pour 7 années sur 10.

**Comment l'import s'insère dans votre idée ?**
Le contrat remplace une part des volumes, pas tout : 13 % pour un bassin de 5 000 t. Le reste reste importé, mais la filière dépend moins d'un prix qui a bondi de 53 % en deux ans et d'un fournisseur, le Canada, qui fait 45 % des volumes.

**Qui vous paie, et combien ?**
Les coopératives et les conditionneurs, par campagne. Hypothèses à tester : une étude pilote à 3 000 €, puis un abonnement à 10 000 € par campagne et par bassin. La valeur : sur un pilote de 300 t, le barème par tranches économise 85 k€ par campagne face au prix unique.

**Quelle taille de marché ?**
142 coopératives agricoles et 28 unions font le commerce des grains en France (Sirene) ; le secteur coopératif agricole pèse 2 100 entreprises et 118 Md€ (Coop FR, chiffres 2024). Si les 170 s'abonnaient pour un seul bassin, ce serait 1,7 M€ par an (calcul illustratif). Le marché grandit avec les cultures et les bassins.

**Combien coûte le pilote à la coopérative ?**
Pour 300 t avec le barème par tranches : 385 k€ d'achat en moyenne, 60 k€ de tri et 2 k€ de collecte, soit 447 k€, ou 1 489 €/t acceptée. Tri et collecte sont des hypothèses, sans devis.

**Les contrats existants sont moins chers : ils ont tort ?**
Non : ils partagent aussi le risque autrement (volumes, qualité, choix des bassins). Face au blé francilien, le barème NatUp 2023–2024 protège 5,9 années sur 10, le prix Unéal 6,1. En 2022, quand le blé flambe, ils ne tiennent que 5 à 16 % des contrats, contre 68 % pour les contrats calibrés.

**Alors quel contrat proposer ?**
Un barème par tranches : 1 635 €/t la première tonne par hectare, puis 750 et 650. Même protection que 1 567 €/t sur toutes les tonnes, 18 % moins cher en moyenne ; en backtest, 79 % de contrats tenus pour 19 % de moins. La première tonne est celle qui manque les mauvaises années.
*À montrer : annexe « La proposition de contrat ».*

**Et une prime à l'hectare ?**
La moins chère en moyenne (900 €/t plus 491 €/ha), mais l'acheteur la paie même sans récolte, et elle cède quand le blé flambe : 37 % des contrats tenus en 2022, 74 % sur l'ensemble, sous la cible.

**Et si le prix du blé flambe ?**
Le vrai prix du blé de chaque année est rejoué, 2022 compris (338 €/t). Un plancher indexé (7,44 fois le prix du blé) suit le blé et tient 82 % des contrats en backtest, mais la coopérative porte alors ce risque : de 357 à 625 k€ d'achat pour 300 t selon le blé.

**Vous avez un partenaire ?**
Pas encore, et nous ne le cachons pas. Candidats identifiés, non contactés : NatUp et Lunor en premier (558 t collectées en 2025, contrat triennal publié), puis Unéal et Vivien Paille, Cibèle et Axéréal pour le tri, Valfrance pour un terrain francilien. Le message à NatUp est prêt.

**Les prochaines étapes ?**
Un pilote de 300 t : comparer d'abord, sur une collecte existante, le barème du partenaire et nos variantes, puis dimensionner une campagne 2027. Ses données de rendement font passer le calcul du département à la parcelle.

### Le modèle et la preuve

**Où est l'IA ?**
Un modèle d'apprentissage probabiliste : une régression quantile qui apprend, sur 294 couples département × année, comment la météo déplace la distribution du rendement. Il est calibré par prédiction conforme, rejoué sur 20 000 années pour en tirer le prix, et validé sur des années jamais vues.

**Que perdrait l'outil sans l'IA ?**
Un prix calculé sur les moyennes ne tient que 29 % des contrats sur des années jamais vues ; le nôtre, 78 %. La météo apporte surtout un prix plus juste : 1 567 €/t contre 2 932 sans météo, pour un taux comparable.

**Pourquoi pas le modèle le plus précis ?**
LightGBM prédit mieux l'année moyenne (perte pinball de 0,1020 contre 0,1105), mais il sous-estime les mauvaises années : ses contrats ne tiennent que 76 % du temps. Pour protéger un revenu, la mauvaise année compte plus que la précision moyenne. Et nous avions choisi notre modèle avant de voir les résultats.
*À montrer : annexe « Le test, en détail ».*

**Pourquoi des quantiles, et pourquoi la calibration ?**
Les quantiles donnent la mauvaise année, pas seulement l'année moyenne. La calibration garantit que la fourchette à 80 % contient vraiment 80 % des récoltes réelles : 79 % en backtest.

**Pourquoi rejouer des années entières ?**
Pour garder les liens réels entre la météo, les deux récoltes et le prix du blé : chaque année simulée tire la même année historique pour le blé et la lentille, avec le prix du blé de cette année-là.

**Quelles métriques ?**
Le taux de contrats tenus (78 % pour une cible de 80 %), la couverture de la fourchette à 80 % (79 %), la perte pinball, qui mesure la précision des quantiles, et l'erreur médiane sur le rendement d'une année (±35 %). Toutes sont mesurées en backtest strict : 2019–2025, 133 cas.

**Comment marche le backtest ? Pas de fuite ?**
Chaque année de 2019 à 2025, tout est réappris sur les seules années d'avant (regroupement des séries, modèles, calibration) ; le prix est fixé, puis comparé à la vraie récolte et au vrai prix du blé. Les années test ne servent jamais à choisir quoi que ce soit.

**Sur l'écran 5, ça veut dire quoi « vert » et « 100 % » ?**
Chaque département coloré est un contrat test. On se place avant les semis : le modèle fixe le prix avec les seules années d'avant. Puis on regarde la vraie récolte et le vrai prix du blé. **Vert** : la lentille payée à ce prix a rapporté au moins autant que le blé, la promesse est tenue. **Rouge** : elle a rapporté moins. **Gris** : département non testé. Le pourcentage d'une année, c'est la part de départements verts ; les 78 %, la part de vert sur les 133 contrats des sept années. Exemple réel : en 2020, dans le Loiret, prix fixé à 934 €/t, lentille effondrée à 5 q/ha : 175 €/ha, contre 465 €/ha en blé. Rouge.

**Pourquoi 100 % en 2023, 2024 et 2025 ?**
Le modèle venait d'apprendre trois années difficiles (2020–2021 pour la lentille, 2022 pour le blé) : il a fixé des prix hauts, puis les récoltes ont été normales ou bonnes. Ces années-là, la coopérative a payé une protection dont elle n'a pas eu besoin. Ce qui compte, c'est la moyenne : 78 % sur sept ans pour 80 % promis.

**Et 2020, le contrat a cédé ?**
Sur les départements producteurs, il n'a tenu que dans 39 % des cas : le modèle, appris jusqu'en 2019, n'avait jamais vu un effondrement de cette ampleur. C'est pour ça qu'on vise 80 % et pas 100 %, et qu'on le montre au lieu de le cacher. En Île-de-France, au prix de 1 600 €/t, les parcelles tiennent.

**Vous annonciez 87 %, c'est 78 % ?**
Oui : un audit interne a trouvé que le regroupement des séries Agreste en double utilisait toute la période, années testées comprises. Refait avec le seul passé, le taux passe de 87 à 78 %. Nous gardons le chiffre strict : il est proche de la promesse, et c'est le but.

**Quelle marge d'erreur ? Le prix est-il fiable ?**
Le rendement d'une année se prédit à ±35 % : c'est pour ça qu'on calibre un prix sur le risque plutôt que sur une prévision. Le prix lui-même est incertain : de 1 099 à 2 877 €/t à 80 % en Seine-et-Marne. Seize années ne suffisent pas à cerner les mauvaises années : les données d'un pilote sont la première chose à obtenir.

**Vous avez pris en compte la météo ?**
Oui : NASA POWER journalier 2010–2025, 43 départements, six variables (pluie du printemps et de l'été, jours de chaleur, gel tardif, pluie à la récolte, température de mai à juillet). Elles pèsent 61 % de ce que LightGBM a appris, et chaque année simulée rejoue une vraie année météo.

**Et le changement climatique ?**
Le modèle rejoue les années 2010–2025 avec leur tendance ; des extrêmes plus fréquents feraient monter le prix. C'est pour ça que nous montrons les années où le contrat cède et l'incertitude sur le prix. Des scénarios de stress, plus durs que l'historique, sont l'étape suivante du modèle.

**« 8 sur 10 », c'est la fiabilité pour la coopérative ?**
Non : c'est la part des années où la marge en lentille égale ou dépasse celle du blé. Les deux autres années, l'agriculteur peut gagner moins qu'en blé ; la coopérative, elle, paie le prix promis.

**Pourquoi l'Île-de-France, qui produit peu de lentilles ?**
C'est le territoire à conquérir : 117 000 ha de blé en Seine-et-Marne. Le modèle apprend sur les départements producteurs ; le niveau de rendement francilien vient des voisins (Aube, Marne, Yonne, Eure-et-Loir, Loiret). C'est une limite annoncée.

**La SAA donne 727 ha de lentilles en Île-de-France, la carte 1 095 ha ?**
Les deux sont justes : la SAA rattache les terres au siège de l'exploitation, le registre parcellaire à la parcelle. 70 % de l'écart est en Seine-et-Marne, voisine des grands départements producteurs.

**Et à l'échelle de la parcelle ?**
Limite assumée : le modèle est départemental, donc il sous-estime la variance d'une parcelle. Les données de rendement d'une coopérative sont l'étape suivante ; le satellite peut aider.

**Pourquoi regrouper des départements ?**
Agreste estime souvent la lentille au niveau régional : plusieurs départements ont exactement les mêmes chiffres. Les compter comme indépendants gonflerait la confiance : on passe de 39 départements à 24 séries indépendantes.

**Le modèle de langage sert à quoi ? Peut-il inventer des chiffres ?**
Il rédige la lettre de proposition au producteur à partir des chiffres calculés, une seule fois, quand on construit l'application (Amazon Bedrock). Un garde-fou rejette tout texte qui contient un nombre absent des entrées. Il ne produit aucun chiffre, et la démo ne dépend pas du réseau.
*À montrer : annexe « La proposition de contrat », la lettre.*

### Les parcelles, les silos, le satellite

**Que dit l'outil sur les parcelles ?**
Il part des 20 762 parcelles de blé du registre parcellaire 2025. Une parcelle bascule si le prix livré au silo, moins la collecte, couvre le prix plancher ; les plus proches passent en premier. Pour 300 t : 28 parcelles, 216 ha, à moins de 3,2 km. Pour 5 000 t : 260 parcelles, 3 502 ha, à moins de 9,8 km. La courbe d'offre donne les tonnes à chaque prix.

**Et les silos ? Où placer la collecte ?**
Le site du scénario est fictif, mais la collecte existe : 352 établissements du commerce de grains à moins de 15 km des parcelles franciliennes, dont 171 de coopératives (Sirene). Le meilleur pour le pilote, Vivescia à Chenoise-Cucharmoy, est à 1,0 km en moyenne des parcelles retenues. Déplacer le site ne fait gagner que quelques dixièmes d'euro par tonne : il se choisit pour la logistique, pas pour le prix. Sirene ne dit pas si un établissement est un silo, ni sa capacité.

**Comment on déplace le silo ?**
D'un clic, dans le simulateur ou dans l'annexe « La proposition de contrat » : sur la carte, ou sur un site existant (rond noir pour une coopérative, cercle blanc pour un négociant). Parcelles, distances, coût de collecte et budget se recalculent. L'annexe propose aussi « Meilleur emplacement », « Meilleur site existant » et « Revenir au site du scénario ». Recharger la page ensuite : le site déplacé resterait sur les écrans 3, 4 et 6.

**Et pendant la saison ?**
Prototype : la saison 2025 rejouée sur les 8 parcelles de lentille les plus proches du site, avec 148 images Sentinel-2. Six suivent le groupe, deux sont en retard en mai : on sait où aller voir. Le NDVI ne prédit pas encore le rendement ; les données d'un pilote serviront à le caler.
*À montrer : annexe « La saison, vue par satellite ».*

**Le satellite remplace-t-il le registre parcellaire ?**
Pas seul. En connaissant les parcelles d'un carré de 4 km sur cinq, il retrouve 73 % des légumineuses des autres carrés en fin de saison, avec 90 % de signalements justes, un an avant le registre. Appris sur l'année précédente seule, il n'en retrouve que 8 % : le printemps 2024 était trop nuageux, et les féveroles ont mûri plus d'un mois plus tôt en 2025. Nous montrons les deux résultats.
*À montrer : annexe « Vu du ciel ».*

### Les données et la rigueur

**Quelles données ?**
Toutes ouvertes : Agreste (rendements 2010–2025), NASA POWER (météo), registre parcellaire 2025 de l'IGN (20 922 parcelles), Eurostat (commerce, prix du blé et de la lentille), Copernicus Sentinel-2, Insee Sirene. Chaque chiffre affiché porte son statut : mesuré, sourcé, supposé, synthétique ou modèle.

**Qu'est-ce qui est réel, qu'est-ce qui est simulé ?**
Les données sont réelles. Le site de collecte et les lots du pilote de 300 t sont fictifs, et annoncés comme tels. Les charges, le tri et la collecte sont des hypothèses sourcées, avec leur sensibilité. Les camions de la démo sont une animation ; le compteur de tonnes vient du calcul.

**D'où viennent les charges ?**
700 €/ha pour le blé et 500 €/ha pour la lentille, arrondis des références Cerfrance et Terres Inovia ; aide couplée de 105 €/ha (montant indicatif 2026) ; 150 €/ha de bénéfice de rotation. Tout est dans un seul fichier, avec sa source et sa sensibilité : avec des charges du blé à 600 €/ha, le prix passe à 1 703 €/t ; sans aide, à 1 709 €/t.
*À montrer : le simulateur, en changeant une hypothèse.*

**Et les données personnelles ?**
Aucune : Agreste publie des totaux par département, le registre parcellaire public ne dit pas qui exploite une parcelle, et de Sirene, on ne garde que des établissements d'entreprises diffusibles, sans entrepreneurs individuels ni dirigeants.

**Ça passe à l'échelle ?**
Le même moteur donne déjà le prix de 24 départements producteurs et de cinq légumineuses. Un nouveau bassin, c'est relancer le pipeline avec ses parcelles et ses hypothèses ; l'application est un site statique, qui marche aussi hors ligne.

**Comment c'est construit ?**
Un pipeline Python (téléchargement, modèles, simulation, backtest, contrats, export) avec 29 tests automatiques, une application React et deck.gl hébergée sur AWS Amplify, et Amazon Bedrock pour la lettre. Code et données publics.

### La concurrence

**Ça existe déjà ?**
Les contrats à prix minimum, oui : Unéal, NatUp, et Max Havelaar « Origine France », dont le plancher lentille (1 019 €/t pour la récolte 2025) est calculé sur les coûts de production plus un objectif de revenu. Un outil qui calcule ce prix sur le risque face au blé, le vérifie sur les années passées et cible les parcelles, nous ne l'avons pas trouvé.

**Votre concurrent le plus proche ?**
Max Havelaar pour le prix plancher ; FiLoLeG (Chambre d'agriculture des Hauts-de-France) pour la marge face au blé, en scénarios fixes. Ni l'un ni l'autre ne raisonne en probabilité ni ne se vérifie sur les années passées. L'assurance, elle, indemnise une récolte perdue : c'est un complément.

**Qu'est-ce qui empêche Terres Inovia, un assureur ou Max Havelaar de le faire ?**
Rien techniquement : la méthode est publique. Notre avance tient à l'outil fait pour la coopérative, à la vérification sur les années passées et au premier pilote. Ce sont aussi des partenaires naturels.

### La France et les autres cultures

**Et ailleurs en France ?**
Le même calcul donne le prix de 24 départements producteurs, à charges franciliennes : de 558 €/t (Pyrénées-Orientales) à 2 238 €/t (Haute-Loire). C'est la carte de l'écran 6, touche `F`.

**Et les autres légumineuses ?**
Même moteur : pois chiche 1 064 €/t, haricot sec 2 185, pois 427, féverole 462 en Seine-et-Marne. Pour elles, le backtest favorise un plancher indexé sur le blé (78 à 89 % des contrats tenus, contre 65 à 70 % à prix fixe), parce que leur risque vient surtout du prix du blé. Le pois et la féverole demandent 427 et 462 €/t pour battre le blé 8 années sur 10, contre 200 à 260 €/t dans le référentiel de prix CRIT 2025.
*À montrer : annexe « La proposition de contrat », autres légumineuses.*

**Et les assureurs ?**
La même distribution de récolte permet de tarifer une assurance rendement : 231 €/ha de prime pure pour garantir 70 % du rendement moyen en Seine-et-Marne, hors frais de l'assureur.

**Quel impact ?**
Le pilote de 300 t mobilise 216 ha. Un bassin de 5 000 t, 3 502 ha : 13 % des importations, 1 250 t de protéines, 630 t d'azote minéral non apporté et 2 644 t CO₂e d'émissions directes évitées. Pour l'agriculteur, une marge au moins égale au blé 8 années sur 10, contre 6 au prix actuel.
