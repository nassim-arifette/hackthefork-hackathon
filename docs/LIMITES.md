# Limites connues

Ces limites sont annoncées par l'équipe elle-même, dans le deck et pendant les questions. Chiffres : [RESULTATS.md](RESULTATS.md), version 4.

| Limite | Conséquence | Ce qu'on fait | Étape suivante |
|---|---|---|---|
| **Rendements départementaux** | la variance réelle à la parcelle est plus forte : le risque est sous-estimé | on le dit ; la fiabilité affichée vaut pour un département moyen | données de rendement des coopératives |
| **Agreste estime souvent la lentille au niveau régional** | 39 départements mesurés, mais 24 séries indépendantes seulement | séries identiques regroupées avant l'entraînement | données de coopératives, autres légumineuses |
| **Peu de lentille en Île-de-France** (727 ha selon la SAA 2025, statut qualité 3 ; 1 095 ha déclarés au RPG) | pas d'effet propre à l'Île-de-France | rendement relatif, niveau emprunté aux départements producteurs voisins ; écart RPG / SAA audité | parcelles franciliennes suivies en pilote |
| **Le prix plancher est lui-même incertain** | de 1 099 à 2 877 €/t à 80 % en Seine-et-Marne (bootstrap) | intervalle affiché à côté du prix | plus d'années, données de coopératives |
| **Sept années test seulement** | le taux de contrats tenus est incertain | résultats affichés année par année | autres cultures, autres régions |
| **Années extrêmes absentes de l'entraînement** (2020–2021) | les contrats cèdent ces années-là (50 % et 61 % tenus) | montré à l'écran, pas caché | scénarios de stress, modèles de queue |
| **La météo n'améliore pas la précision du modèle linéaire** | son apport passe par la calibration ; LightGBM est plus précis mais tient moins de contrats | les modèles sont comparés à l'écran | variables météo par stade, météo pondérée par les surfaces RPG |
| **Météo au centroïde du département** | la météo des zones cultivées peut différer | assumé en version 1 | moyenne pondérée par les surfaces RPG |
| **Prix du blé reconstitué** | indice Eurostat calé sur un prix rendu Rouen, un peu au-dessus du prix payé au producteur | choix prudent : il surestime la marge du blé, donc P\* | série FranceAgriMer de prix payés aux producteurs |
| **Charges supposées, constantes dans le temps** | 700 et 500 €/ha sont des arrondis de références techniques, pas des comptabilités ; la flambée des engrais de 2022 n'est pas prise en compte | sensibilités affichées (600–800 et 400–600 €/ha) | données de charges des exploitations du pilote |
| **Charges franciliennes partout** | le classement national compare des rendements, pas des économies locales | annoncé sous le classement | charges par bassin |
| **Bénéfice de rotation compté dans la marge de la campagne** | 150 €/ha arrivent sur le blé suivant, pas dans la trésorerie de l'année ; sans lui, P\* = 1 773 €/t | sensibilité de 0 à 200 €/ha affichée | marge de campagne et marge avec rotation affichées séparément |
| **Part refusée au tri fixe** (10 %) | en réalité, elle varie avec la pluie à la récolte et la bruche ; la SAA parle d'une production « récoltée et commercialisable », qui peut déjà exclure une partie des impuretés | sensibilité 0 / 10 / 20 % (1 411 à 1 763 €/t) ; les lots refusés gardent une valeur que le modèle ignore | refus modélisé selon la météo, données de tri du pilote |
| **Aide couplée** | 105 €/ha est un montant indicatif 2026, ajusté selon les surfaces éligibles | sensibilité 0 / 105 / 122 €/ha | montant définitif de la campagne |
| **Barèmes de contrat comparés** | le barème NatUp 2023–2024 est reconstitué depuis un entretien publié ; la proposition 2027 est une hypothèse ; les coûts excluent collecte, tri et séchage | statuts affichés ; coûts du backtest comparés en écart au prix unique | contrat et décomptes réels d'un partenaire |
| **Prime à l'hectare** | versée même sans récolte ; fragile si le prix du blé flambe (79 % de contrats tenus en backtest) | montrée comme option, pas recommandée | clause d'engagement technique, indexation partielle |
| **Le RPG enregistre ce qui est déclaré**, pas ce qui est cultivable | on ne connaît ni les sols ni l'aptitude à la lentille | la courbe d'offre est un potentiel, pas une prévision | GIS Sol, historique des rotations |
| **Délai de retour de la lentille sur une même parcelle** | toutes les parcelles ne peuvent pas porter de la lentille chaque année | volumes modestes : pilote de 300 t, ambition de 5 000 t | règle agronomique à intégrer |
| **Lots du pilote synthétiques** | les 140 lots de `data/pilote_300t` sont fictifs | jamais utilisés pour l'apprentissage ni le backtest | 20 à 50 lots réels anonymisés |
| **Un prix plancher n'est pas une assurance** | une récolte effondrée réduit la marge malgré le prix | le modèle en tient compte ; les 20 % non couverts sont visibles | couplage avec une assurance récolte |
