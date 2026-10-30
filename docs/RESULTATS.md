# Premiers résultats (30/10/2026, soir)

Calculés par le pipeline sur les vraies données. Les charges, le prix du blé, le bonus de rotation et le coût de transport sont des **hypothèses provisoires** (`data/hypotheses.yaml`) : les prix plancher en dépendent directement.

## Données

| | Valeur |
|---|---|
| Panel lentille utilisable (statuts 1–2, ≥ 50 ha, sans doublons) | 492 départements × années, 39 départements |
| Panel blé tendre d'hiver utilisable | 1 455 départements × années, 91 départements |
| Météo NASA POWER | 43 départements, 2010–2025 |
| Parcelles RPG retenues | 20 922 (blé tendre d'hiver et lentille, ≥ 1 ha) |

## Backtest 2019–2025 (sans fuite)

Rendement lentille relatif, intervalle à 80 % calibré par conformal. P\* calculé avec les seules années antérieures, puis comparé à l'année réelle.

| Année | Départements | Couverture M1 | Pinball M0 | Pinball M1 | Pinball M2 | Contrats tenus |
|---|---|---|---|---|---|---|
| 2019 | 29 | 100 % | 0,052 | 0,060 | 0,066 | 76 % |
| 2020 | 32 | 66 % | 0,091 | 0,089 | 0,099 | **56 %** |
| 2021 | 32 | 63 % | 0,104 | 0,114 | 0,099 | **63 %** |
| 2022 | 33 | 97 % | 0,088 | 0,093 | 0,098 | 97 % |
| 2023 | 34 | 91 % | 0,094 | 0,087 | 0,087 | 100 % |
| 2024 | 34 | 59 % | 0,195 | 0,179 | 0,176 | 100 % |
| 2025 | 35 | 86 % | 0,104 | 0,113 | 0,079 | 100 % |
| **Global** | **229 cas** | **80 %** (M0 : 71 %) | **0,105** | **0,106** | **0,101** | **85 %** pour 80 % visés |

### Lecture honnête

- **La fiabilité visée est atteinte globalement** (85 % pour 80 %), mais elle repose sur 7 années seulement. Les contrats cèdent en **2020 et 2021**, deux années d'effondrement de la lentille absentes de l'entraînement.
- **La calibration fonctionne** : l'intervalle à 80 % couvre le réel dans 80 % des cas, contre 71 % pour la baseline.
- **Le modèle météo linéaire (M1) ne bat pas la baseline en précision** (pinball −0,7 %). Le challenger LightGBM (M2) fait mieux (+3,8 %). M1 reste le modèle principal parce qu'il a été choisi **avant** de voir les résultats ; passer à M2 maintenant reviendrait à choisir sur les années test. À retester proprement : choix du modèle sur une validation interne aux années d'entraînement.
- **Piste d'amélioration** : variables météo plus fines (stade de floraison, pluie à la récolte), météo pondérée par les surfaces RPG plutôt qu'au centroïde.

## Prix plancher, campagne 2026 (hypothèses provisoires)

| Département | P\* (80 %) | Prix d'équilibre médian | Rendement lentille moyen simulé |
|---|---|---|---|
| Seine-et-Marne | 1 377 €/t | 778 €/t | 1,59 t/ha |
| Yvelines | 1 261 €/t | 730 €/t | 1,61 t/ha |
| Essonne | 1 281 €/t | 733 €/t | 1,60 t/ha |
| Val-d'Oise | 1 357 €/t | 777 €/t | 1,60 t/ha |

### Le prix de la sécurité (Seine-et-Marne)

| Fiabilité | 50 % | 60 % | 70 % | 80 % | 90 % | 95 % |
|---|---|---|---|---|---|---|
| P\* | 778 | 918 | 1 103 | 1 377 | 1 878 | 2 587 €/t |

Sensibilités : prix du blé 160 → 280 €/t fait passer P\* de 1 034 à 2 063 €/t ; un bonus de rotation de 200 €/ha le baisse à 1 154 €/t.

### Ce que ça veut dire

- Avec ces hypothèses, **sécuriser 8 années sur 10 coûte presque deux fois le prix d'équilibre médian**. C'est le cœur du message : une moyenne sous-estime fortement le prix qu'il faut garantir.
- **Le transport différencie peu les parcelles** à l'intérieur d'un département (0,12 €/t/km × quelques dizaines de km) : la courbe d'offre est presque une marche. Le prix est décidé par le risque, pas par la distance.
- Les valeurs absolues dépendent des hypothèses provisoires. Elles doivent être revues avec des références sourcées avant d'être présentées.
