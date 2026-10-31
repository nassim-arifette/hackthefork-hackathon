# Fiche projet · Le Contrat qui Tient

**Hack the Fork Paris 2026 · Track 3, souveraineté protéique : des champs français aux protéines de demain**

## Le problème

Près d'une lentille sur deux mangée en France vient de l'étranger : 39 371 tonnes importées en 2025, pour environ 86 000 tonnes consommées, dont 45 % du Canada. Les agriculteurs français pourraient en produire davantage, mais la lentille est risquée. Sa récolte varie deux fois plus que celle du blé, et une mauvaise année, comme 2020 (−38 %), efface la marge. Rester au blé est donc le choix raisonnable.

Les coopératives, qui collectent, trient et revendent les récoltes de leurs agriculteurs, peuvent retirer ce risque avec un contrat : un prix minimum garanti avant les semis. Ce prix se fixe aujourd'hui à l'expérience. Trop bas, l'agriculteur perd les mauvaises années et arrête ; trop haut, la coopérative perd de l'argent.

## La solution

Le Contrat qui Tient calcule, pour le responsable filière d'une coopérative, le prix minimum qui garantit à l'agriculteur de gagner au moins autant qu'avec le blé 8 années sur 10. La carte montre les parcelles qui accepteraient ce prix, au plus près du silo.

- Un modèle d'apprentissage relie la météo de seize années à la récolte de la lentille et du blé. Il prévoit les mauvaises années, pas seulement la moyenne.
- Une simulation rejoue 20 000 années de météo et de prix du blé pour en déduire le prix.
- Testé sur sept années que le modèle n'avait jamais vues : 78 % des contrats ont tenu pour 80 % promis, contre 29 % avec un prix calculé sur la moyenne.
- Un prototype satellite (Sentinel-2) repère aussi les légumineuses du bassin un an avant la publication du registre parcellaire, à condition de connaître une partie des parcelles.

Premier résultat, en Seine-et-Marne : il faut 1 567 €/t pour tenir 8 années sur 10, alors que le prix payé par Unéal en 2023, 900 €/t, ne protège que 6 années sur 10. En payant plus cher la première tonne récoltée par hectare (1 635 €/t, puis 750 et 650), on protège autant pour 18 % de moins.

## Le modèle économique

- **Clients** : les coopératives et les conditionneurs de légumes secs, qui fixent ce prix à chaque campagne. En France, 142 coopératives agricoles et 28 unions de coopératives font le commerce des grains (base Sirene).
- **Offre** : une étude pilote, puis un abonnement par campagne et par bassin ; les montants sont à valider avec les premiers clients.
- **Adoption** : un pilote de 300 t avec une coopérative qui développe une filière lentille ; ses données de rendement rendront le prix plus précis.
- **Extension** : le pois chiche et le haricot pour l'alimentation humaine ; d'autres régions, puisque le même calcul donne déjà un prix pour 24 départements producteurs ; les assureurs agricoles, qui peuvent tarifer une assurance rendement avec la même distribution de récolte.

## L'impact

Pour un pilote de 300 t : 216 ha de lentilles sur les 28 parcelles les plus proches du silo. Pour un bassin de 5 000 t : 3 502 ha, 13 % des importations de 2025, 1 250 t de protéines végétales, 630 t d'azote minéral non apporté et 2 644 t CO₂e d'émissions directes évitées. Pour l'agriculteur : un revenu au moins égal à celui du blé 8 années sur 10.

## Données

Ouvertes et traçables : Agreste, IGN (registre parcellaire), NASA POWER, Eurostat, Copernicus Sentinel-2, Insee (base Sirene). Chaque chiffre affiché porte son statut : mesuré, sourcé, supposé ou issu du modèle.

## Liens

- Démo en ligne : https://main.d1lkeu0ybo1cz4.amplifyapp.com/
- Code et données : https://github.com/nassim-arifette/hackthefork-hackathon
- Vidéo de la démo, 4 minutes : `docs/video/demo-4min.mp4` dans le dépôt
