# Pitch de 4 minutes

Le texte dit pendant les 4 minutes de présentation, arrêtées net, avant les 2 minutes de questions. Il suit les six écrans de l'application ([démo en ligne](https://main.d1lkeu0ybo1cz4.amplifyapp.com/)). Une personne parle, l'autre pilote le clavier ; les indications entre crochets sont pour elle.

Le texte compte environ 430 mots, soit à peu près 3 min 40 à un débit posé, gestes et silences compris : il reste une vingtaine de secondes avant l'arrêt. Ce qu'on voit à chaque écran et les annexes gardées pour les questions sont dans [DEMO_SCRIPT.md](DEMO_SCRIPT.md), les réponses aux questions attendues dans [PITCH_NOTES.md](PITCH_NOTES.md). Les chiffres viennent des exports du pipeline ([RESULTATS.md](RESULTATS.md)) ; leur statut est donné en fin de document.

## 0:00 – 0:25 · Écran 1, le constat

> « Près d'une lentille sur deux mangée en France vient de l'étranger : 39 000 tonnes en 2025, surtout du Canada. Nos champs pourraient les produire. Alors pourquoi les agriculteurs n'en sèment-ils pas ? »

## 0:25 – 1:00 · Écran 2, le pari · [Espace]

> « Parce que c'est un pari. Avec le blé, l'agriculteur sait ce qu'il va gagner. La lentille, elle, varie deux fois plus : en 2020, sa récolte a chuté de 38 %. Une seule mauvaise année efface sa marge. Alors, rester au blé, c'est le choix raisonnable. En Île-de-France, ce sont ces 20 000 parcelles. »

## 1:00 – 1:25 · Écran 3, le contrat · [Espace]

> « La solution existe : un contrat. La coopérative, l'entreprise des agriculteurs qui collecte et revend leurs récoltes, peut leur garantir un prix minimum avant les semis. Mais lequel ? Trop bas, l'agriculteur perd et ne recommence pas. Trop haut, c'est la coopérative qui perd. Notre utilisatrice, c'est sa responsable filière, et c'est sa question. »

## 1:25 – 2:40 · Écran 4, le prix : la démo · [Espace, puis laisser le prix monter seul]

> « Voici notre outil. À 900 euros la tonne, le prix payé par une coopérative en 2023, la lentille rapporte moins que le blé 4 années sur 10 : ce sont ces orages. L'outil calcule le prix qui protège l'agriculteur 8 années sur 10 : 1 567 euros en Seine-et-Marne. Et ces 8 années-là, il gagne en moyenne 1 555 euros de plus par hectare qu'avec du blé. À ce prix, les parcelles les plus proches du silo basculent, les camions arrivent : 300 tonnes, 28 parcelles. »

[Maintenir `←` environ 2 secondes, jusque vers 1 000 €/t.]

> « Si la coopérative paie moins, regardez : les orages reviennent, les parcelles repassent au blé. »

[Maintenir `→` pour revenir à 1 600 €/t.]

> « Et l'outil trouve le contrat le moins cher : payer plus cher la première tonne, celle qui manque les mauvaises années, protège autant pour 18 % de moins. »

## 2:40 – 3:20 · Écran 5, la preuve · [Espace]

> « Est-ce que ça tient vraiment ? On a remonté le temps : chaque année de 2019 à 2025, le modèle n'apprend que sur le passé, fixe le prix, puis on regarde la vraie récolte. Un prix calculé sur les moyennes aurait tenu 3 contrats sur 10. Le nôtre en tient 8 : 78 % pour 80 % promis. Notre modèle apprend sur 16 ans de météo à prévoir les mauvaises années, pas la moyenne. LightGBM, plus précis en moyenne, en tient moins. »

## 3:20 – 4:00 · Écran 6, l'impact et le passage à l'échelle · [Espace]

> « À l'échelle d'un bassin : 5 000 tonnes, 13 % des importations, 1 250 tonnes de protéines et 630 tonnes d'azote minéral en moins dans nos champs. »

[Vers 3:32 : touche `F`.]

> « Le même calcul marche partout : voici le prix, département par département. »

[Vers 3:40 : clic sur « Simulateur », en haut à droite.]

> « Et le produit, c'est ce simulateur : la coopérative entre ses propres chiffres et obtient son contrat, ses parcelles et son budget. Nos clients, ce sont les 170 coopératives qui font le commerce des grains en France. Sur un pilote de 300 tonnes, le bon contrat leur fait économiser 85 000 euros par campagne. Le Contrat qui Tient. »

[Silence. Ne rien ajouter.]

## Les gestes au clavier

1. `Espace` à 0:25, 1:00 et 1:25.
2. Écran 4, entre 2:10 et 2:20 environ : maintenir `←`, puis maintenir `→`.
3. `Espace` à 2:40 et 3:20.
4. `F` vers 3:32.
5. Clic sur « Simulateur » vers 3:40.

Juste avant le passage, recharger la page : elle s'ouvre sur l'écran 1, avec le site de collecte du scénario. Un site déplacé dans une annexe ou dans le simulateur resterait utilisé par les écrans 3, 4 et 6.

## Si la démo plante

Lancer la vidéo de secours (`docs/video/demo-4min.mp4`), qui suit les mêmes six écrans, et dire le même texte en sautant les deux passages qu'elle ne montre pas : « Si la coopérative paie moins… » et la phrase sur le simulateur.

## Si le chrono dépasse 3 min 50 en répétition

Couper d'abord la phrase sur LightGBM, puis celle sur les 20 000 parcelles.

## Les chiffres cités

| Dans le pitch | Valeur exacte | Statut | Source |
|---|---|---|---|
| près d'une lentille sur deux, 39 000 t importées en 2025, surtout du Canada | 46 % de la consommation apparente ; 39 371 t, dont 45 % du Canada | sourcé | Eurostat Comext ; Agreste SAA |
| la lentille varie deux fois plus | coefficient de variation du rendement national 0,20, contre 0,09 pour le blé, 2010–2025 | mesuré | Agreste SAA |
| en 2020, sa récolte a chuté de 38 % | rendement national 38 % sous la tendance | mesuré | Agreste SAA |
| ces 20 000 parcelles | 20 762 parcelles de blé tendre d'hiver en Île-de-France | mesuré | RPG 2025 (IGN) |
| 900 €/t, moins que le blé 4 années sur 10 | prix Unéal 2023 ; la lentille bat le blé 6 années sur 10 | sourcé (prix), modèle (fréquence) | Unéal ; 20 000 années simulées |
| 1 567 €/t, 8 années sur 10 | prix départ ferme, Seine-et-Marne, payé sur les tonnes acceptées au tri ; 1 600 €/t à l'écran, livré au silo | modèle | 20 000 années simulées (météo NASA POWER, prix du blé 2010–2025) |
| 1 555 €/ha de plus ces 8 années | écart moyen lentille − blé les années gagnantes | modèle | 20 000 années simulées |
| 300 t, 28 parcelles | 216 ha, à moins de 3,2 km du site de collecte | modèle ; site fictif annoncé comme tel | RPG 2025 |
| 18 % de moins | barème 1 635 / 750 / 650 €/t, 1 283 €/t en moyenne contre 1 567 €/t | modèle | 20 000 années simulées |
| 3 contrats sur 10 contre 8 ; 78 % pour 80 % promis | 29 % et 78 % de 133 contrats, 2019–2025 | mesuré (backtest strict) | récoltes Agreste SAA, météo NASA POWER |
| 16 ans de météo | 2010–2025 | sourcé | NASA POWER |
| LightGBM en tient moins | 76 % | mesuré (backtest strict) | idem |
| 5 000 t, 13 % des importations | 12,7 % des importations 2025 | supposé (ambition de bassin) | Eurostat Comext |
| 1 250 t de protéines, 630 t d'azote minéral | 25 % de protéines ; 180 kg N/ha de blé remplacé | sourcé (hypothèses), appliqué à un volume supposé | Terres Inovia ; Agreste, Mémento DRIAAF 2025 |
| 170 coopératives | 142 coopératives agricoles et 28 unions du commerce de gros de céréales | mesuré | Sirene (Insee), 31/10/2026 |
| 85 000 € par campagne sur 300 t | achat 470 k€ au prix unique, 385 k€ au barème par tranches | modèle | 20 000 années simulées |
