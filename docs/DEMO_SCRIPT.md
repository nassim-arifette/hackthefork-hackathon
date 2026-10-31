# Script de démo (4 minutes, coupées net)

Un membre raconte, un autre pilote. Tous les chiffres ci-dessous viennent des exports du pipeline ([RESULTATS.md](RESULTATS.md), version 4) ; s'ils changent, ce script change avec eux.

Pilotage : `Espace` pour l'étape suivante, `←` `→` pour le prix, `1` et `2` pour l'année à l'étape 3, `M` pour la méthode.

| Temps | Étape à l'écran | Ce qu'on dit |
|---|---|---|
| 0:00–0:35 | **1. Le verrou** : carte de France des surfaces en lentille, courbe des rendements | « La France importe 39 000 tonnes de lentilles par an. Pourquoi les agriculteurs n'en sèment-ils pas plus ? Regardez cette courbe : le rendement de la lentille varie deux fois plus que celui du blé. En 2020, il perd plus d'un tiers. Une mauvaise année efface la marge. » |
| 0:35–0:50 | transition vers l'Île-de-France | « Notre utilisatrice est responsable filière d'une coopérative. Elle veut proposer un contrat lentille. Sa question : à quel prix garanti l'agriculteur gagne-t-il au moins autant qu'en blé, huit années sur dix ? » |
| 0:50–1:45 | **2. Le prix** : la bascule s'anime, puis le curseur | « Voici les 20 762 parcelles de blé d'Île-de-France. Aux prix de 2012 à 2016, entre 650 et 780 €/t, la lentille ne gagne qu'une année sur deux : rien ne bascule. Pour huit années sur dix, il faut 1 568 €/t départ ferme en Seine-et-Marne, payés sur les tonnes acceptées au tri. Ce prix, c'est notre modèle qui le calcule, en rejouant 20 000 années de météo et de prix du blé. Unéal payait 900 €/t en 2023 : face au blé francilien, c'est six années sur dix. » |
| 1:45–2:25 | **3. L'épreuve** : 2016 puis 2020 | « 2016 : le blé perd 53 % en Seine-et-Marne. À 1 600 €/t rendu au site initial, collecte moyenne déduite, la marge lentille de référence est de 1 743 €/ha ; le blé perd 84 €/ha. En 2020, la lentille s'effondre. Le contrat tient encore ici, mais dans les départements producteurs il n'a tenu qu'une fois sur deux. » |
| 2:25–3:10 | **4. La preuve** : la révélation année par année | « Pour chaque année, on entraîne le modèle sur les années antérieures. Le backtest historique donne 87,2 % de contrats tenus, contre 29,3 % pour les moyennes et 81,2 % pour la tendance probabiliste. Sa limite : les regroupements de séries sont calculés sur toute la période. Le benchmark strict les reconstruit aussi dans le temps. » |
| 3:10–3:40 | **5. Le contrat** : le pilote, puis l'ambition | « Voici une proposition à discuter avec une filière. Au site initial et à 1 600 €/t rendu, la cible de 300 tonnes sélectionne 28 parcelles entières, soit 309,7 tonnes attendues. L'ambition de 5 000 tonnes représente environ 13 % des importations. Le barème paie davantage la première tonne et protège autant dans les simulations pour 18 % de moins. Les volumes restent un scénario, sans engagement des producteurs. » |
| (si le temps le permet) | **6. La saison** : le replay 2025 démarre seul | « Et pendant la saison : 148 images Sentinel-2 sur les huit parcelles de lentille les plus proches du site. Six suivent le groupe, deux sont sous le groupe en mai : on sait où aller voir. » |
| 3:40–4:00 | retour au titre | « Les coopératives paient par campagne. Prochaine étape : un pilote avec leurs données de rendement, qui resserreront l'incertitude sur le prix. Puis toutes les cultures sous contrat, et les assureurs. Le Contrat qui Tient. » |

## Règles

- Répéter au chronomètre au moins trois fois samedi soir et deux fois dimanche matin.
- Si un chiffre n'est pas à jour, la phrase est retirée, jamais remplacée par une estimation.
- Jamais d'éditeur ni de terminal à l'écran.
- La version hors ligne (`app/dist-single/index.html`) est sur la clé USB ; elle est identique à la version en ligne, polices comprises.
