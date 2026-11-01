# Script de démo (4 minutes, coupées net)

Format du guide participant : 4 minutes de présentation arrêtées net, puis 2 minutes de questions. Un membre raconte, un autre pilote. Le parcours tient en six écrans ; un tiers du temps sert à poser le problème, pour un jury qui ne connaît pas forcément la filière. Le texte à dire est dans [PITCH.md](PITCH.md) ; ce document décrit ce qu'on voit et ce que fait la personne au clavier. Tous les chiffres viennent des exports du pipeline ([RESULTATS.md](RESULTATS.md)) et s'affichent à l'écran ; s'ils changent, le pitch et ce script changent avec eux.

Pilotage : `Espace` pour l'écran suivant (`Maj` + `Espace` pour revenir), `←` `→` pour le prix à l'écran 4, `F` pour la carte de France à l'écran 6, `M` pour la méthode. Le menu **Annexes** garde les écrans détaillés pour les questions.

| Temps | Écran | Ce qu'on voit | Au clavier |
|---|---|---|---|
| 0:00–0:25 | **1. Le constat** | dix bols de lentilles, dont cinq importés ; des cargos rejoignent les ports | page rechargée juste avant, ouverte sur l'écran 1 |
| 0:25–1:00 | **2. Le pari** | les récoltes de blé et de lentille, année par année ; l'Île-de-France en ocre | `Espace` |
| 1:00–1:25 | **3. Le contrat** | la filière animée, du champ à l'assiette ; la carte descend vers le silo de la coopérative | `Espace` |
| 1:25–2:40 | **4. Le prix** (démo) | le prix part de 900 €/t et monte ; les parcelles proches du silo passent au vert, les camions arrivent, le compteur monte à 300 t | `Espace`, puis laisser le prix monter seul ; entre 2:10 et 2:20, maintenir `←` jusque vers 1 000 €/t (les orages reviennent), puis `→` jusqu'à 1 600 €/t |
| 2:40–3:20 | **5. La preuve** | la carte de France rejoue 2019–2025, département par département ; dix contrats sans modèle, dix avec | `Espace` |
| 3:20–4:00 | **6. L'impact** | compteurs ; 260 parcelles et leurs camions autour du silo ; la carte de France des prix ; le simulateur | `Espace` ; vers 3:32, `F` ; vers 3:40, clic sur « Simulateur » en haut à droite |

## Pour les questions (menu Annexes)

- **Simulateur** (bouton en haut à droite, ouvert à la fin du pitch) : la réponse à « c'est quoi le produit ? ». Changer le prix de revente ou la protection visée, montrer le bandeau du haut et les parcelles sur la carte.
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
- Version en ligne : https://main.d1lkeu0ybo1cz4.amplifyapp.com/ (déployée par Amplify à chaque push sur `main`). La version hors ligne (`app/dist-single/index.html`) est sur la clé USB ; elle est identique à la version en ligne, polices comprises.
- Sur l'ordinateur partagé : navigateur en plein écran (`F11`). Le panneau de droite réduit seul son texte pour tenir sans défiler, jusqu'à 72 % ; sous 720 px de haut, dézoomer d'un cran (`Ctrl` + `−`).
- Recharger la page juste avant le passage : un site de collecte déplacé dans une annexe ou dans le simulateur reste utilisé par les écrans 3, 4 et 6.
- Vidéo de secours : `docs/video/demo-4min.mp4` ([lien direct](https://github.com/nassim-arifette/hackthefork-hackathon/raw/c4d9aed0fbab8d5895809fcd11e9b52ffdca6ff7/docs/video/demo-4min.mp4)), mêmes six écrans au même minutage, carte de France à 3:42 ; elle ne montre ni le passage `←` `→` ni le simulateur. Si la démo en direct ne répond pas, la lancer et continuer à parler.
