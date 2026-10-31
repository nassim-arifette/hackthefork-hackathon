# Questions et réponses pour la démonstration

| Question | Réponse |
|---|---|
| Quel est le meilleur modèle ? | On compare des candidats définis à l'avance, avec sélection sur une fenêtre distincte de calibration et test. Aucun algorithme n'est universellement meilleur. Les résultats actuels sont dans RESULTATS.md. |
| L'IA améliore-t-elle le contrat ? | Cela reste à démontrer face à M0 et au quantile historique, à protection et coût comparables. Un prix plus élevé peut expliquer davantage de succès. |
| Pourquoi pas un modèle plus complexe ? | Le panel est court et corrélé. Un ensemble de quantiles est évalué, mais la complexité ne remplace pas une validation temporelle. Voir RECHERCHE.md. |
| Quelle marge d'erreur ? | L'erreur absolue médiane est exprimée sur le rendement normalisé, et aussi en q/ha dans l'export. Ce n'est pas « ±33 % ». La couverture empirique est présentée séparément. |
| Le conformal garantit-il 80 % ici ? | Non : les garanties classiques supposent l'échangeabilité, non démontrée ici. Nous figeons le prédicteur calibré et mesurons la couverture passée. |
| Est-ce le marché actuel ? | Non. Les références lentille sont nominales et datent de 2012–2016. L'offre et la revente sont des scénarios hypothétiques modifiables. Le blé est une référence reconstruite. |
| L'aide est-elle acquise ? | Non. Le scénario principal vaut 0 €/ha. Une variante à 122 €/ha est conditionnelle à l'éligibilité et à l'applicabilité. |
| La coopérative peut-elle financer le contrat ? | L'outil calcule son plafond à partir des coûts, pertes, revente et marge minimale saisis. Il peut conclure qu'aucun accord n'existe. |
| Le backtest prouve-t-il une garantie d'exploitation ? | Non : sept années, rendements départementaux, charges fixes et historiques déjà examinés. Une validation indépendante sur des exploitations est nécessaire. |
| Trois campagnes ? | Non. Le calcul actuel porte uniquement sur la campagne 2026. |
