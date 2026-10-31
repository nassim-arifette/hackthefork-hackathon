# Validation du contrat : objectif, comparaisons et sous-groupes

## Décision à prendre

Pour un département, choisir avant la campagne le prix départ ferme le plus bas tel que la marge lentille soit au moins égale à celle du blé dans 80 % de la distribution des années possibles. Le prix rendu acheteur ajoute ensuite le transport.

`R = (prix_blé × rendement_blé − charges_blé + charges_lentille − aide − bonus_rotation) / rendement_lentille`

Le prix théorique est `Q80(R)`. Les égalités comptent comme des contrats tenus. Les charges et aides sont celles du fichier d'hypothèses, identiques entre modèles : le replay est un scénario économique commun, pas une reconstitution des charges historiques de chaque exploitation. Le bonus de rotation est nul dans ces hypothèses.

**Une baisse de la perte du quantile ne suffit pas à conclure que le produit est meilleur.** Les trois dimensions présentées ensemble sont : protection réalisée, prix proposé et manque à l'hectare. La perte pinball à 0,8 mesure la qualité de prévision du quantile ; elle accompagne la contrainte de protection au lieu de la remplacer.

## Références et cohortes

- **M0** : vraie baseline du repo, tendance linéaire et quantiles empiriques des résidus. Dans le benchmark commun, son identifiant est `trend`.
- **M1** : régression quantile météo initiale de l'application. Dans le benchmark commun, son identifiant est `linear`.
- **QRF** : forêt quantile candidate, avec les versions trois quantiles et 101 quantiles identifiées séparément.
- **Systèmes historiques** : anciens exports M0/M1 complets, qui incluent leur préparation et leur calibration. Ils servent à expliquer l'évolution du produit, pas à isoler un changement de modèle.

Les 133 couples département–année du premier backtest sont tous inclus dans les 192 du benchmark récent. Les résultats sont donc présentés sur les 133 communs, les 59 ajoutés et les 192 au total. Les deux ensembles couvrent 2019–2025. Un cas n'est pas une année indépendante ; plusieurs départements partagent une météo, un prix national et parfois une estimation Agreste.

L'ancienne déduplication utilisait toutes les années 2010–2025, avant filtrage des observations utilisables. La nouvelle reconstruit les groupes à chaque date avec le passé utilisable. Les groupes « anciens/ajoutés » sont un diagnostic rétrospectif, pas une variable de décision future.

## Expérience 1 : expliquer les écarts de protocole

Le script `pipeline/benchmark_protocol_attribution.py` compare :

1. La reproduction du système historique, y compris les tirages et le calibrage, contrôlée contre `data/backtest.json`.
2. Le même système avec les réglages Monte-Carlo communs à 20 000 scénarios.
3. Des étapes intermédiaires isolant le regroupement passé et la préparation météo.
4. La calibration temporelle glissante moderne.
5. Un factoriel séparant quantiles bruts et bornes élargies pour la lentille et le blé : brut/brut, élargi/brut, brut/élargi, élargi/élargi.

Les dernières variantes sont comparées pour M0, M1 et QRF. Les effets de la chaîne sont conditionnels à l'ordre des changements ; le factoriel lentille/blé permet d'observer leur interaction. Utiliser des bornes d'intervalle élargies comme quantiles de simulation est une variante historique à mesurer, pas une justification probabiliste acquise.

## Expérience 2 : sous-groupes et erreurs

Le script `pipeline/analyze_model_groups.py` compare les modèles sur exactement les mêmes décisions dans chaque groupe.

Groupes utilisables avant signature : région administrative ; historique lentille de moins de huit ans ou d'au moins huit ans ; tercile de variabilité historique ; rendement historique inférieur ou supérieur à la médiane. Les niveaux et seuils sont calculés uniquement avec le passé de l'année considérée.

Diagnostics après récolte : rendement lentille inférieur à 60 % de sa moyenne passée ; pluie ou chaleur extrême par rapport au climat historique local ; hausse du prix du blé de plus de 20 % par rapport au dernier prix connu. Ces diagnostics expliquent les échecs, sans servir à choisir un modèle en supposant la crise future connue.

Toutes les modalités sont publiées, y compris celles où QRF perd. Chaque ligne indique nombre de cas, départements et années. Les groupes avec moins de quinze cas ou moins de trois années sont signalés comme peu documentés. Les taux départementaux sont accompagnés du nombre d'années : 80 % sur sept années correspond à au moins six réussites observées.

Les différences entre modèles sont appariées par cas. Les rééchantillonnages portent sur les années entières. Une analyse de sensibilité tient compte des séries Agreste partagées. Les intervalles décrivent la variabilité du replay ; les groupes explorés ne sont pas présentés comme des découvertes confirmées indépendamment.

## Expérience 3 : calibrer directement la décision de prix

Le script `pipeline/benchmark_contract_policies.py` applique les mêmes corrections à M0 et QRF : correction multiplicative ou additive, historique cumulé ou fenêtres fixes, correction globale ou régionale ramenée vers la moyenne globale. Chaque erreur de calibration provient d'une prévision faite avant l'année observée.

La sélection temporelle poursuit explicitement l'objectif du produit : parmi les candidats atteignant 80 % sur les validations antérieures, choisir le moins cher. Si aucun n'atteint le seuil, le repli privilégie la protection et annonce l'absence de candidat admissible. La décision de l'année test ne consulte jamais ses résultats. Une sélection régionale n'est utilisée qu'avec assez de passé ; sinon elle se replie sur la sélection globale.

Les politiques fixes et sélectionnées sont toutes conservées. Le meilleur résultat choisi après lecture de 2019–2025 reste un constat rétrospectif ; la performance de la règle de sélection passée est présentée séparément.

Une seconde expérience teste des quantiles internes de correction à 90 % et 95 %, en plus de 80 %. La cible du produit reste 80 % ; ces corrections supplémentaires mesurent le prix d'une réserve contre la dérive entre années. Les mêmes niveaux sont disponibles pour M0 et QRF. Le sélecteur n'utilise que leurs résultats antérieurs pour choisir une correction.

## Expérience 4 : transfert vers une région sans historique lentille exploité

L'application utilise un transfert pour l'Île-de-France. Un bon backtest dans les départements déjà observés ne suffit pas à évaluer ce cas d'usage.

Le script `pipeline/benchmark_spatial_transfer.py` exclut à tour de rôle une région entière de l'apprentissage lentille, à chaque année. Le niveau lentille est transféré depuis quatre départements analogues choisis sur le climat passé, sans utiliser le rendement lentille de la cible pour fixer ce niveau. Le blé local reste disponible, comme dans l'application. Les séries partagées identifiables dans le passé sont retirées de l'apprentissage pour éviter de laisser un duplicat de la cible.

M0 et QRF utilisent les mêmes donneurs et scénarios. Le test isole le transfert à distributions brutes ; il ne remplace pas une calibration du contrat transféré. Les observations lentille de la région masquée servent à l'évaluation et au contrôle des duplicats, pas aux caractéristiques prédictives ni au niveau transféré.

## Tableau de décision final

Pour chaque modèle, politique et groupe : taux tenu global, moyenne des taux annuels, taux par département, prix médian et moyen, perte du quantile, manque moyen €/ha, queue des manques et pire année. Les variantes dont le prix est plus bas mais la protection insuffisante ne sont pas annoncées comme une réussite de l'objectif de 80 %.

Une amélioration exploitable doit être formulée avec son périmètre : « sur ces départements/années, cette règle disponible avant campagne améliore le prix à protection comparable », ou « elle améliore la protection à prix comparable ». Une moyenne nationale ne constitue pas une validation de 80 % pour chaque département.

Les sources, paramètres, coupures temporelles, sélections, prédictions et contrôles sont archivés dans `experiments/`. Les calculs lourds s'exécutent dans Colab avec copie sur Drive. Les simulations répétées réduisent le bruit Monte-Carlo ; elles n'ajoutent pas d'années agricoles observées.

## Appui méthodologique

- [Gneiting, Making and Evaluating Point Forecasts, 2011](https://www.bundesbank.de/resource/blob/635562/7d3de0f3fc003e5b4864828143f268cf/mL/2012-06-01-eltville-11-gneiting-paper-data.pdf) : le score doit correspondre à la quantité visée ; la pinball est cohérente avec un quantile. Cela justifie Q80 comme cible de score, sans remplacer le contrôle des contrats tenus.
- [Romano, Patterson et Candès, Conformalized Quantile Regression, 2019](https://proceedings.neurips.cc/paper/8613-conformalized-quantile-regression.pdf) : la couverture marginale d'un intervalle repose sur des hypothèses d'échangeabilité. Le résultat ne fournit pas à lui seul une distribution complète de rendement à simuler.
- [Barber et al., Conformal Prediction Beyond Exchangeability, 2023](https://arxiv.org/abs/2202.13415) : dépendance et dérive nécessitent un traitement spécifique. Notre pondération empirique des années n'est pas une implémentation automatique de leurs garanties.
- [Gibbs, Cherian et Candès, Conformal Prediction With Conditional Guarantees](https://arxiv.org/abs/2305.12616) : distinguer couverture globale et couverture de groupes prédéfinis. L'audit régional et départemental s'appuie sur cette distinction ; les corrections régionales testées ici restent des heuristiques mesurées par backtest.
