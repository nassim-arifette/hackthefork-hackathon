# Recherche méthodologique et choix d'implémentation

Références primaires consultées le 30 octobre 2026. Cette revue guide un protocole explicable pour un petit panel départemental ; elle ne démontre pas qu'un modèle est universellement supérieur. Les résultats effectivement calculés figurent dans [RESULTATS.md](RESULTATS.md), le protocole dans [MODELE.md](MODELE.md).

| Référence | Apport retenu | Application et limites dans ce dépôt |
|---|---|---|
| Romano, Patterson et Candès, 2019, [Conformalized Quantile Regression](https://arxiv.org/abs/1905.03222) | Un estimateur quantile entraîné séparément est corrigé à partir d'erreurs de calibration ; la correction utilise un rang ajusté à la taille d'échantillon. | Le prédicteur, sa normalisation et ses transformations restent figés après apprentissage. La correction ne sert qu'aux intervalles, pas à reconstruire la distribution simulée. L'implémentation autorise uniquement l'élargissement ; elle n'affirme pas les garanties échangeables sur ce panel. |
| Cawley et Talbot, 2010, [On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation](https://jmlr.org/papers/v11/cawley10a.html) | La sélection peut surajuster un critère de validation bruité ; les scores d'évaluation réutilisés pour choisir une méthode deviennent optimistes. | Deux années distinctes servent au choix de M0/M1/M2/M3. Les trois années de calibration et l'année d'évaluation n'interviennent pas dans ce choix. Les modèles et réglages ne sont pas retouchés en fonction du classement de ce nouveau backtest. |
| Fakoor et al., 2023, [Flexible Model Aggregation for Quantile Regression](https://jmlr.org/papers/v24/22-0799.html) | L'agrégation de prévisions quantiles constitue une famille de modèles ; l'ordre des quantiles doit être respecté. | M3 est une moyenne équipondérée des quantiles M0, M1 et M2. Ses poids sont fixes. Ce challenger simple n'implémente pas l'ensemble adaptatif complet de l'article, n'est pas un mélange de distributions et n'est pas supposé meilleur avant évaluation. |
| Barber, Candès, Ramdas et Tibshirani, 2023, [Conformal prediction beyond exchangeability](https://arxiv.org/abs/2202.13415) | La dérive temporelle et la non-échangeabilité remettent en question les garanties conformelles usuelles ; des adaptations nécessitent un cadre explicite. | Le dépôt annonce une couverture empirique. Le découpage temporel évite une fuite, mais ne rend pas les années ou les départements indépendants. Aucune correction pondérée de cet article n'est implémentée. |
| Xu et Xie, 2021, [Conformal prediction interval for dynamic time-series](https://proceedings.mlr.press/v139/xu21h.html) | EnbPI propose une construction séquentielle à partir d'ensembles bootstrap, avec des résultats sous hypothèses de dépendance. | Étudié conceptuellement uniquement. EnbPI n'est ni implémenté ni benchmarké ici : quelques années de données et des dépendances spatiales ne suffisent pas à justifier automatiquement son cadre temporel. |
| Meinshausen, 2006, [Quantile Regression Forests](https://jmlr.org/papers/v7/meinshausen06a.html) | Les forêts quantiles estiment des quantiles de la distribution conditionnelle en utilisant la distribution des observations dans les feuilles. | Étudié conceptuellement uniquement. Aucune forêt quantile n'est implémentée ni comparée dans les résultats de ce dépôt. Ajouter des candidats après examen des scores accroîtrait le risque de sélectionner le bruit. |

## Comparaison réellement exécutée

- M0 : tendance linéaire et quantiles empiriques des résidus, sans météo.
- M1 : régression quantile linéaire régularisée, tendance et six variables météo.
- M2 : LightGBM quantile peu profond, réglages fixes et entraînement déterministe.
- M3 : moyenne des quantiles des trois modèles précédents.
- `auto` : choix par perte quantile moyenne, avec poids égal par année de sélection.
- Références économiques : prix calculé sur les moyennes passées et quantile des prix d'équilibre historiques, avec appariement lentille/blé/prix par département-année.

Le modèle de rendement est évalué avec la météo de l'année test observée rétrospectivement. La décision de prix rejoue uniquement les années antérieures. Les deux diagnostics répondent donc à des questions distinctes. La comparaison économique montre simultanément protection observée, prix, manque de marge et coût d'achat ; un taux de succès supérieur obtenu en payant plus cher n'établit pas à lui seul une meilleure décision.

## Portée de l'étude

Ce travail reste une réanalyse rétrospective de données et de résultats déjà examinés dans les versions précédentes. La séparation temporelle dans le code ne transforme pas l'ensemble 2019–2025 en validation prospective intacte. Une prochaine comparaison confirmatoire devrait figer à l'avance les variables, candidats, paramètres, règles économiques et critères de succès, puis utiliser une nouvelle campagne ou une cohorte réellement tenue à l'écart.

Les distributions entre trois quantiles, les queues, le plancher numérique de rendement et la dépendance résiduelle entre cultures restent des hypothèses. Les sensibilités exportées les rendent visibles ; ni les articles cités, ni une bonne couverture d'intervalle ne valident automatiquement le prix obtenu.
