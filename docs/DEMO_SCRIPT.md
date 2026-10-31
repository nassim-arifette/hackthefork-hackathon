# Script de démo (4 minutes, coupées net)

Un membre raconte, un autre pilote. Tous les chiffres ci-dessous viennent des exports du pipeline ([RESULTATS.md](RESULTATS.md), version 4) ; s'ils changent, ce script change avec eux.

Pilotage : `Espace` pour l'étape suivante, `←` `→` pour le prix, `1` et `2` pour l'année à l'étape 3, `M` pour la méthode.

| Temps | Étape à l'écran | Ce qu'on dit |
|---|---|---|
| 0:00–0:35 | **1. Le verrou** : carte de France des surfaces en lentille, courbe des rendements | « La France importe 39 000 tonnes de lentilles par an. Pourquoi les agriculteurs n'en sèment-ils pas plus ? Regardez cette courbe : le rendement de la lentille varie deux fois plus que celui du blé. En 2020, il perd plus d'un tiers. Une mauvaise année efface la marge. » |
| 0:35–0:50 | transition vers l'Île-de-France | « Notre utilisatrice est responsable filière d'une coopérative. Elle veut proposer un contrat lentille. Sa question : à quel prix garanti l'agriculteur gagne-t-il au moins autant qu'en blé, huit années sur dix ? » |
| 0:50–1:45 | **2. Le prix** : la bascule s'anime, puis le curseur | « Voici les 20 762 parcelles de blé d'Île-de-France. Aux prix de 2012 à 2016, entre 650 et 780 €/t, la lentille ne gagne qu'une année sur deux : rien ne bascule. Pour huit années sur dix, il faut 1 567 €/t départ ferme en Seine-et-Marne, payés sur les tonnes acceptées au tri. Ce prix, c'est notre modèle qui le calcule, en rejouant 20 000 années de météo et de prix du blé. Unéal payait 900 €/t en 2023 : face au blé francilien, c'est six années sur dix. » |
| 1:45–2:25 | **3. L'épreuve** : 2016 puis 2020 | « 2016 : le blé perd 53 % en Seine-et-Marne. Avec le contrat, la lentille rapporte 1 757 €/ha ; le blé perd 84 €/ha. 2020 : c'est la lentille qui s'effondre. Le contrat tient encore ici, mais dans les départements producteurs, il n'a tenu qu'une fois sur deux. » |
| 2:25–3:10 | **4. La preuve** : la révélation année par année | « On a coupé les données en 2019 : le modèle n'a jamais vu la suite. Un prix calculé sur les moyennes, sans modèle, n'aurait tenu que trois contrats sur dix. Notre modèle en tient 87 % pour 80 % promis. Et LightGBM, plus précis sur l'année moyenne, n'en tient que 77 % : pour protéger un revenu, c'est la mauvaise année qu'il faut bien prédire. » |
| 3:10–3:40 | **5. Le contrat** : le pilote, puis l'ambition | « Résultat : une proposition prête à signer. Un pilote de 300 tonnes sur les 27 parcelles les plus proches du site. Puis l'ambition : 5 000 tonnes, 13 % des importations, 1 250 tonnes de protéines et 631 tonnes d'azote en moins sur le blé remplacé. Et le bon barème : en payant cher la première tonne, celle qui manque les mauvaises années, on protège autant pour 18 % de moins. » |
| 3:40–4:00 | retour au titre | « Les coopératives paient par campagne. Prochaine étape : un pilote avec leurs données de rendement, qui resserreront l'incertitude sur le prix. Puis toutes les cultures sous contrat, et les assureurs. Le Contrat qui Tient. » |

## Règles

- Répéter au chronomètre au moins trois fois samedi soir et deux fois dimanche matin.
- Si un chiffre n'est pas à jour, la phrase est retirée, jamais remplacée par une estimation.
- Jamais d'éditeur ni de terminal à l'écran.
- La version hors ligne (`app/dist-single/index.html`) est sur la clé USB ; elle est identique à la version en ligne, polices comprises.
