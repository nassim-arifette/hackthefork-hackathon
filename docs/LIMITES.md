# Limites connues

Ces limites sont annoncées par l'équipe elle-même, dans le deck et pendant les questions.

| Limite | Conséquence | Ce qu'on fait | Étape suivante |
|---|---|---|---|
| **Rendements départementaux** | la variance réelle à la parcelle est plus forte : le risque est sous-estimé | on le dit ; la fiabilité affichée vaut pour un département moyen | données de rendement de coopératives, ou satellite |
| **Peu de lentille en Île-de-France** (environ 730 ha, statut qualité 3, valeurs imputées) | le modèle ne peut pas apprendre un effet propre à l'Île-de-France | entraînement sur le panel national, application avec la météo locale | données de coopérative sur des parcelles franciliennes |
| **Séries estimées ensemble** (ex. Aube et Marne) | moins d'information indépendante qu'il n'y paraît | regroupement des séries identiques | — |
| **Petit nombre d'années test** (7 années, 2019–2025) | le taux de contrats tenus est incertain | résultats affichés année par année | plus d'années ou de cultures |
| **Années extrêmes absentes de l'entraînement** (2020–2021 pour la lentille) | le modèle peut sous-estimer le risque d'effondrement | on montre les années où le contrat n'a pas tenu | modèles de queue, scénarios de stress |
| **Le RPG enregistre ce qui est déclaré**, pas ce qui est cultivable | on ne connaît pas les sols ni l'aptitude réelle à la lentille | la courbe d'offre est un potentiel, pas une prévision | GIS Sol, historique de rotations |
| **Charges, prix futur du blé, transport, bonus de rotation** sont des hypothèses | P\* en dépend directement | paramètres modifiables et analyse de sensibilité | références de coopératives |
| **La bruche** n'est pas modélisée | pertes de 10 à 20 % possibles (sourcé) | mentionnée | variable de risque qualité |
| **Un prix plancher n'est pas une assurance** | si le rendement s'effondre, la marge baisse quand même | le modèle en tient compte ; les 20 % non couverts sont visibles | couplage avec une assurance récolte |
| **Adoption** : tous les agriculteurs éligibles ne signeront pas | la courbe d'offre surestime les volumes réels | taux d'adoption en hypothèse | enquête auprès d'agriculteurs |
| **Le modèle météo linéaire ne bat pas la baseline en précision** (backtest : pinball −0,7 %) | l'apport de la météo passe surtout par la calibration | on l'affiche ; LightGBM fait +3,8 % mais n'a pas été choisi a priori | variables météo plus fines, sélection de modèle sur validation interne |
| **Météo au centroïde du département** | la météo des zones cultivées peut différer | assumé en version 1 | moyenne pondérée par les surfaces RPG |
| **Prix du blé constant** dans la simulation | le risque de prix du blé n'est pas encore simulé | sensibilité affichée | série FranceAgriMer rééchantillonnée avec l'année météo |
