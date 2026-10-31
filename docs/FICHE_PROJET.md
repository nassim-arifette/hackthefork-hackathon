# Fiche projet · Le Contrat qui Tient

**Hack the Fork Paris 2026 · Track 3, souveraineté et filières**

## Le problème

La France importe 39 371 tonnes de lentilles par an (Eurostat, 2025) alors qu'elle veut doubler ses surfaces de légumineuses d'ici 2030. Les agriculteurs en sèment peu parce que le rendement de la lentille varie deux fois plus que celui du blé (Agreste, 2010–2025) : une mauvaise année efface la marge. Les coopératives proposent des contrats à prix minimum, mais ce prix se fixe à l'expérience, sans mesure de la protection qu'il offre, alors que c'est la mauvaise année qui fait perdre l'agriculteur.

## La solution

Le Contrat qui Tient calcule, pour le responsable filière d'une coopérative, le prix plancher qui rapporte à l'agriculteur au moins autant que le blé 8 années sur 10, et montre sur la carte quelles parcelles basculent à ce prix.

- Un modèle d'apprentissage probabiliste relie la météo (NASA POWER) à la distribution du rendement du blé et de la lentille, sur seize ans de données Agreste.
- Une simulation rejoue 20 000 années de météo et de prix du blé, et en déduit le prix plancher, payé sur les tonnes acceptées au tri.
- Le backtest historique, avec entraînement sur les seules années antérieures, donne 87,2 % de contrats tenus sur 133 cas, contre 29,3 % pour un prix calculé sur les moyennes. Ses regroupements Agreste utilisent toutefois 2010–2025 ; un benchmark distinct les reconstruit avant chaque année test.
- La carte des 20 762 parcelles de blé d'Île-de-France (RPG 2025) montre la bascule et le volume mobilisable.

Premier résultat : aux prix observés de 2012 à 2016, la lentille ne bat le blé francilien qu'une année sur deux ; pour 8 sur 10, il faut 1 568 €/t départ ferme en Seine-et-Marne, avec une incertitude affichée (1 099 à 2 877 €/t). Le prix contractuel d'Unéal en 2023, 900 €/t, protège 6 années sur 10 dans le même modèle. À protection égale, un barème par tranches (1 635 €/t la première tonne par hectare, puis 750 et 650) coûte 18 % de moins qu'un prix unique, et tient autant de contrats en backtest pour 22 % de moins.

## Le modèle économique

- **Clients** : coopératives et conditionneurs de légumes secs, qui fixent ce prix à chaque campagne.
- **Offre** : étude pilote, puis abonnement par campagne et par bassin (montants à tester en pilote).
- **Adoption** : pilote d'une campagne avec une coopérative qui monte une filière légumineuses ; ses données de rendement resserrent l'incertitude sur le prix.
- **Extension** : toutes les cultures sous contrat (pois chiche, haricot, chanvre), puis les assureurs agricoles, qui ont besoin de la même distribution de rendement.

## Impact

Au site fictif initial, à 1 600 €/t rendu, le scénario de 300 t sélectionne 28 parcelles entières : 309,7 t acceptées attendues sur 216,42 ha. L'ambition de 5 000 t sélectionne 5 011,6 t sur 3 501,83 ha, soit environ 13 % des importations 2025, 1 253 t de protéines végétales, 630 t d'azote minéral non apporté et 2 644 t CO₂e d'émissions directes évitées. Ce sont des potentiels sous hypothèses, sans engagement des producteurs ni capacité industrielle vérifiée ; la cible agricole est une marge au moins égale au blé dans 80 % des simulations.

## Données

Ouvertes et traçables : Agreste, IGN (RPG), NASA POWER, Eurostat. Chaque chiffre affiché porte son statut : mesuré, sourcé, supposé ou modèle.
