# Limites connues

Ces limites sont annoncées par l'équipe elle-même, dans le deck et pendant les questions. Chiffres : [RESULTATS.md](RESULTATS.md).

| Limite | Conséquence | Ce qu'on fait | Étape suivante |
|---|---|---|---|
| **Rendements départementaux** | la variance réelle à la parcelle est plus forte : le risque est sous-estimé | on le dit ; la fiabilité affichée vaut pour un département moyen | données de rendement des coopératives |
| **Agreste estime souvent la lentille au niveau régional** | 39 départements mesurés, mais 24 séries indépendantes seulement | séries identiques regroupées avant l'entraînement | données de coopératives, autres légumineuses |
| **Peu de lentille en Île-de-France** (environ 730 ha, statut qualité 3) | pas d'effet propre à l'Île-de-France | rendement relatif, niveau emprunté aux départements producteurs voisins | parcelles franciliennes suivies en pilote |
| **Le prix plancher est lui-même incertain** | de 1 132 à 3 007 €/t à 80 % en Seine-et-Marne (bootstrap) | intervalle affiché à côté du prix | plus d'années, données de coopératives |
| **Sept années test seulement** | le taux de contrats tenus est incertain | résultats affichés année par année | autres cultures, autres régions |
| **Années extrêmes absentes de l'entraînement** (2020–2021) | les contrats cèdent ces années-là (44 % et 61 % tenus) | montré à l'écran, pas caché | scénarios de stress, modèles de queue |
| **La météo n'améliore pas la précision du modèle linéaire** | son apport passe par la calibration ; LightGBM est plus précis mais tient moins de contrats | les deux modèles sont comparés à l'écran | variables météo par stade, météo pondérée par les surfaces RPG |
| **Météo au centroïde du département** | la météo des zones cultivées peut différer | assumé en version 1 | moyenne pondérée par les surfaces RPG |
| **Prix du blé reconstitué** | indice Eurostat calé sur un prix rendu Rouen, un peu au-dessus du prix payé au producteur | choix prudent : il surestime la marge du blé, donc P\* | série FranceAgriMer de prix payés aux producteurs |
| **Charges constantes dans le temps** | la flambée des engrais en 2022 n'est pas prise en compte | sensibilité affichée | indice Eurostat des prix des intrants |
| **Aide couplée** | l'éligibilité de la lentille et le montant final restent à confirmer | 122 €/ha (arrêté de février 2026), sensibilité « sans aide » affichée | vérifier la notice Telepac |
| **Le RPG enregistre ce qui est déclaré**, pas ce qui est cultivable | on ne connaît ni les sols ni l'aptitude à la lentille | la courbe d'offre est un potentiel, pas une prévision | GIS Sol, historique des rotations |
| **Délai de retour de la lentille sur une même parcelle** | toutes les parcelles ne peuvent pas porter de la lentille chaque année | le volume visé du contrat reste modeste (5 000 t) | règle agronomique à intégrer |
| **La bruche n'est pas modélisée** | 10 à 20 % de pertes possibles (sourcé) | mentionnée | variable de risque qualité |
| **Un prix plancher n'est pas une assurance** | une récolte effondrée réduit la marge malgré le prix | le modèle en tient compte ; les 20 % non couverts sont visibles | couplage avec une assurance récolte |
