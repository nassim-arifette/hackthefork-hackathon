# Script de démo (4 minutes, coupées net)

Format du guide participant : 4 minutes de présentation arrêtées net, puis 2 minutes de questions. Un membre raconte, un autre pilote. Le parcours tient en six écrans ; un tiers du temps sert à poser le problème, pour un jury qui ne connaît pas forcément la filière. Tous les chiffres viennent des exports du pipeline ([RESULTATS.md](RESULTATS.md)) et s'affichent à l'écran ; s'ils changent, ce script change avec eux.

Pilotage : `Espace` pour l'écran suivant (`Maj` + `Espace` pour revenir), `←` `→` pour le prix à l'écran 4, `F` pour la carte de France à l'écran 6, `M` pour la méthode. Le menu **Annexes** garde les écrans détaillés pour les questions.

| Temps | Écran | Ce qu'on voit | Ce qu'on dit |
|---|---|---|---|
| 0:00–0:25 | **1. Le constat** | dix bols de lentilles, dont cinq importés ; des cargos rejoignent les ports | « Près d'une lentille sur deux mangée en France vient de l'étranger : 39 000 tonnes par an. Nos champs pourraient les produire. Pourquoi les agriculteurs n'en sèment-ils pas ? » |
| 0:25–1:00 | **2. Le pari** | les récoltes de blé et de lentille, année par année ; l'Île-de-France en ocre | « Voici 20 762 parcelles de blé en Île-de-France. Avec le blé, l'agriculteur sait ce qu'il va gagner. La lentille varie deux fois plus : en 2020, sa récolte a chuté de 38 %. Une mauvaise année efface sa marge. Rester au blé, c'est le choix raisonnable. » |
| 1:00–1:25 | **3. Le contrat** | la filière animée, du champ à l'assiette ; la carte descend vers le silo de la coopérative | « La coopérative, l'entreprise des agriculteurs qui collecte, trie et revend leurs récoltes, peut leur garantir un prix minimum avant les semis. Trop bas, l'agriculteur perd et arrête ; trop haut, la coopérative perd. Notre utilisatrice est sa responsable filière. Sa question : quel prix ? » |
| 1:25–2:40 | **4. Le prix** (démo) | le prix part de 900 €/t et monte ; les parcelles proches du silo passent au vert, les camions arrivent, le compteur monte à 300 t | « 900 €/t, c'est le prix payé par Unéal en 2023 : l'agriculteur gagne moins qu'en blé 4 années sur 10, ce sont ces orages. Notre outil calcule le prix qui le protège 8 années sur 10, en rejouant 20 000 années de météo et de prix du blé : 1 567 €/t en Seine-et-Marne. Les parcelles les plus proches du silo basculent, les camions arrivent : 300 tonnes sur 28 parcelles. Et en payant plus cher la première tonne, celle qui manque les mauvaises années, on protège autant pour 18 % de moins. » |
| 2:40–3:20 | **5. La preuve** | la carte de France rejoue 2019–2025, département par département ; dix contrats sans modèle, dix avec | « On a remonté le temps : chaque année, le modèle n'apprend que sur les années d'avant, puis on regarde la vraie récolte. Un prix fixé sur la moyenne aurait tenu 3 contrats sur 10 ; le nôtre en tient 8, 78 % pour 80 % promis. Notre modèle, une régression quantile sur la météo, prévoit les mauvaises années, pas la moyenne. LightGBM, plus précis en moyenne, en tient moins. » |
| 3:20–4:00 | **6. L'impact** | compteurs ; 260 parcelles et leurs camions autour du silo ; à 3:42, touche `F` : la carte de France des prix | « À l'échelle d'un bassin : 5 000 tonnes, 13 % des importations, 1 250 tonnes de protéines, 630 tonnes d'azote minéral évitées. Les coopératives paient à chaque campagne : il y en a 170 qui font le commerce des grains. Prochaine étape : un pilote de 300 tonnes avec une coopérative, puis le pois chiche, le haricot et la France entière : voici le prix, département par département. Le Contrat qui Tient. » |

## Pour les questions (menu Annexes)

- **Le prix, en détail** : courbe de fiabilité, contrats existants, prix plancher par département, site de collecte déplaçable.
- **Deux mauvaises années, rejouées** : 2016 (le blé s'effondre) et 2020 (la lentille s'effondre).
- **Le test, en détail** : intervalles prédits et récoltes réelles, comparaison des modèles, poids de la météo.
- **La proposition de contrat** : barème par tranches, lettre rédigée par Bedrock, comparaison des contrats, autres légumineuses.
- **La saison, vue par satellite** et **Vu du ciel** : prototypes Sentinel-2.

## Règles

- Répéter au chronomètre au moins trois fois samedi soir et deux fois dimanche matin, dont une fois devant quelqu'un d'extérieur.
- À l'écran 4, laisser le prix monter seul : les camions partent quand il atteint 1 600 €/t livré au silo.
- Si un chiffre n'est pas à jour, la phrase est retirée, jamais remplacée par une estimation.
- Jamais d'éditeur ni de terminal à l'écran.
- La version hors ligne (`app/dist-single/index.html`) est sur la clé USB ; elle est identique à la version en ligne, polices comprises.
- Sur l'ordinateur partagé : navigateur en plein écran (`F11`). Le panneau de droite réduit seul son texte pour tenir sans défiler, jusqu'à 72 % ; sous 720 px de haut, dézoomer d'un cran (`Ctrl` + `−`).
- Vidéo de secours : `docs/video/demo-4min.mp4`, même minutage que ce script ; si la démo en direct ne répond pas, la lancer et continuer à parler.
