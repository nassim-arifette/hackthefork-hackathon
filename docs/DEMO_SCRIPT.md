# Script de démo (4 minutes, coupées net)

Un membre raconte, un autre pilote. Tous les chiffres ci-dessous viennent des exports du pipeline ([RESULTATS.md](RESULTATS.md)) ; s'ils changent, ce script change avec eux.

Pilotage : `Espace` pour l'étape suivante, `←` `→` pour le prix, `1` et `2` pour l'année à l'étape 3, `M` pour la méthode.

| Temps | Étape à l'écran | Ce qu'on dit |
|---|---|---|
| 0:00–0:35 | **1. Le verrou** : carte de France des surfaces en lentille, courbe des rendements | « La France importe 39 000 tonnes de lentilles par an. Pourquoi les agriculteurs n'en sèment-ils pas plus ? Regardez cette courbe : le rendement de la lentille varie deux fois plus que celui du blé. En 2020, il perd plus d'un tiers. Une mauvaise année efface la marge. » |
| 0:35–0:50 | transition vers l'Île-de-France | « Notre utilisatrice est responsable filière d'une coopérative. Elle veut proposer un contrat lentille. Sa question : à quel prix garanti l'agriculteur gagne-t-il au moins autant qu'en blé, huit années sur dix ? » |
| 0:50–1:45 | **2. Le prix** : la bascule s'anime, puis le curseur | « Voici les 20 762 parcelles de blé d'Île-de-France. Au prix de marché, entre 650 et 780 €/t, la lentille ne gagne que 4,7 années sur 10 : rien ne bascule. Il faut monter à 1 622 €/t en Seine-et-Marne pour tenir 8 années sur 10. Ce prix, c'est notre modèle qui le calcule, en rejouant 20 000 années de météo et de prix du blé. » |
| 1:45–2:25 | **3. L'épreuve** : 2016 puis 2020 | « 2016 : le blé perd 53 % en Seine-et-Marne. Avec le contrat, la lentille rapporte 2 149 €/ha contre 176 pour le blé. 2020 : c'est la lentille qui s'effondre. Le contrat tient encore ici, mais ailleurs en France, il n'a tenu que dans 44 % des cas. » |
| 2:25–3:10 | **4. La preuve** : la révélation année par année | « On a coupé les données en 2019 : le modèle n'a jamais vu la suite. Sur 133 cas, le contrat a tenu 86 % du temps pour 80 % promis. Et on a comparé deux modèles d'apprentissage : LightGBM prédit mieux l'année moyenne, mais ses contrats ne tiennent que 77 % du temps. Pour protéger un revenu, c'est la mauvaise année qu'il faut bien prédire. » |
| 3:10–3:40 | **5. Le contrat** : la proposition et les 236 parcelles autour du site | « Résultat : une proposition prête à signer. 5 000 tonnes, 13 % des importations, sur les 236 parcelles les plus proches du site. Et ce que coûte la sécurité : garantir 8 années sur 10 coûte plus du double du prix d'équilibre médian. » |
| 3:40–4:00 | retour au titre | « Les coopératives paient par campagne. Prochaine étape : un pilote avec leurs données de rendement, qui resserreront l'incertitude sur le prix. Puis toutes les cultures sous contrat, et les assureurs. Le Contrat qui Tient. » |

## Règles

- Répéter au chronomètre au moins trois fois samedi soir et deux fois dimanche matin.
- Si un chiffre n'est pas à jour, la phrase est retirée, jamais remplacée par une estimation.
- Jamais d'éditeur ni de terminal à l'écran.
- La version hors ligne (`app/dist-single/index.html`) est sur la clé USB ; elle est identique à la version en ligne, polices comprises.
