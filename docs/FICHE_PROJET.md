> Document de contexte antérieur à la correction de validation. Les chiffres et engagements ci-dessous ne décrivent pas le scénario courant. Références à jour : [RESULTATS](RESULTATS.md), [MODELE](MODELE.md) et [DEMO_SCRIPT](DEMO_SCRIPT.md).

# Fiche projet · Le Contrat qui Tient

**Hack the Fork Paris 2026 · Track 3, souveraineté et filières**

## Le problème

La France importe 39 371 tonnes de lentilles par an (Eurostat, 2025) alors qu'elle veut doubler ses surfaces de légumineuses d'ici 2030. Les agriculteurs en sèment peu parce que le rendement de la lentille varie deux fois plus que celui du blé (Agreste, 2010–2025) : une mauvaise année efface la marge. Les coopératives proposent des contrats à prix minimum, mais ce prix se fixe à l'expérience ou sur des moyennes, alors que c'est la mauvaise année qui fait perdre l'agriculteur.

## La solution

Le Contrat qui Tient calcule, pour le responsable filière d'une coopérative, le prix plancher qui rapporte à l'agriculteur au moins autant que le blé 8 années sur 10, et montre sur la carte quelles parcelles basculent à ce prix.

- Un modèle d'apprentissage probabiliste relie la météo (NASA POWER) à la distribution du rendement du blé et de la lentille, sur seize ans de données Agreste.
- Une simulation rejoue 20 000 années de météo et de prix du blé, et en déduit le prix plancher.
- Un backtest sur des années que le modèle n'a jamais vues mesure la promesse : 86 % des contrats ont tenu pour 80 % visés.
- La carte des 20 762 parcelles de blé d'Île-de-France (RPG 2025) montre la bascule et le volume mobilisable.

Premier résultat : au référence historique nominale 2012–2016, la lentille ne bat le blé qu'environ une année sur deux ; pour 8 sur 10, il faut 1 622 €/t en Seine-et-Marne, avec une incertitude affichée.

## Le modèle économique

- **Clients** : coopératives et conditionneurs de légumes secs, qui fixent ce prix à chaque campagne.
- **Offre** : abonnement par campagne ou prix par tonne contractualisée (montants à tester en pilote).
- **Adoption** : pilote d'une campagne avec une coopérative qui monte une filière légumineuses ; ses données de rendement resserrent l'incertitude sur le prix.
- **Extension** : toutes les cultures sous contrat (pois chiche, haricot, chanvre), puis les assureurs agricoles, qui ont besoin de la même distribution de rendement.

## Impact

Plus de lentilles françaises pour l'alimentation humaine, moins d'importations, moins d'engrais azoté sur la rotation, et un revenu agricole protégé 8 années sur 10.

## Données

Ouvertes et traçables : Agreste, IGN (RPG), NASA POWER, Eurostat. Chaque chiffre affiché porte son statut : mesuré, sourcé, supposé ou modèle.
