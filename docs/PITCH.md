# Pitch et démo : les 4 minutes

Le texte à dire et la démo à piloter, écran par écran. 4 minutes de présentation arrêtées net, puis 2 minutes de questions. Une personne parle, l'autre pilote le clavier.

- **Chaque geste suit une phrase**, pas l'horloge : la personne au clavier écoute la phrase indiquée, puis agit.
- **Les heures sont des limites**, pas des rendez-vous : on avance dès que le texte d'un écran est dit. L'écran 6 a besoin de 55 secondes : il doit commencer au plus tard à 2:55.
- Le texte compte environ 445 mots, soit à peu près 3 min 40 à un débit posé, gestes compris : il reste une vingtaine de secondes avant l'arrêt.

Application : https://main.d1lkeu0ybo1cz4.amplifyapp.com/ ; réponses aux questions : [PITCH_NOTES.md](PITCH_NOTES.md) ; tout le projet : [DOSSIER.md](DOSSIER.md). Les chiffres viennent des exports du pipeline ([RESULTATS.md](RESULTATS.md)) ; leur statut est donné en fin de document.

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

## Pour les questions (menu Annexes)

- **Simulateur** : la réponse à « c'est quoi le produit ? ». Changer une hypothèse et montrer le bandeau du haut : protection à 7 années sur 10 → 1 132 €/t ; sans aide couplée → 1 709 €/t ; 20 % refusés au tri → 1 763 €/t. Un clic sur la carte, ou sur un site existant, déplace la collecte.
- **Le prix, en détail** : courbe de fiabilité, contrats existants, prix plancher par département.
- **Deux mauvaises années, rejouées** : 2016 (le blé s'effondre) et 2020 (la lentille s'effondre).
- **Le test, en détail** : intervalles prédits et récoltes réelles, comparaison des modèles, poids de la météo.
- **La proposition de contrat** : barème par tranches, lettre au producteur, comparaison des contrats, sites de collecte existants, autres légumineuses.
- **La saison, vue par satellite** et **Vu du ciel** : prototypes Sentinel-2.

Après les questions, recharger la page avant l'équipe suivante si l'ordinateur est partagé.

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
