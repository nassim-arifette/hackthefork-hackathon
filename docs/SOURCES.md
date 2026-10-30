# Sources

Chaque source utilisée, avec son étiquette et sa licence. À tenir à jour au fil de l'eau. Une source citée dans le deck ou l'interface doit figurer ici.

## Données

| Id | Source | Contenu | Étiquette | Licence | Lien |
|---|---|---|---|---|---|
| `agreste_saa` | Agreste, Statistique agricole annuelle 2010–2025 | surfaces, rendements, productions par département | mesuré | Licence Ouverte Etalab [à vérifier sur la page] | https://agreste.agriculture.gouv.fr/agreste-web/download/publication/publie/SAA-SeriesLongues/SAA-SeriesLongues-2010-2025_DonneesProvisoires-DepartementalesRegionales.zip |
| `nasa_power` | NASA POWER | météo journalière | mesuré (réanalyse) | données publiques NASA, citation demandée | https://power.larc.nasa.gov/ |
| `rpg` | IGN, Registre parcellaire graphique 2025, Île-de-France | parcelles déclarées | mesuré | Licence Ouverte Etalab [à vérifier] | https://data.geopf.fr/telechargement/resource/RPG/RPG_4-0__GPKG_LAMB93_R11_2025-01-01 |
| `contours` | gregoiredavid/france-geojson (IGN ADMIN EXPRESS) | contours des départements | mesuré | [à vérifier] | https://github.com/gregoiredavid/france-geojson |
| `douanes` | Douanes, données NC8 | importations 0713 40 | mesuré | [à vérifier] | https://lekiosque.finances.gouv.fr/site_fr/telechargement/telechargement_SGBD.asp |
| `cantines` | Registre national des cantines | sites de restauration collective | mesuré | [à vérifier] | https://www.data.gouv.fr/api/1/datasets/r/3f73d129-6b24-45cd-95e9-9bacc216d9d9 |
| `ciqual` | ANSES, Ciqual | teneur en protéines | sourcé | [à vérifier] | https://ciqual.anses.fr/ |
| `hestia` | HESTIA | facteurs d'impact environnemental | sourcé | CC BY 4.0 | s3://hestia-aggregated-data |

## Références techniques et contexte

| Affirmation | Source | Étiquette |
|---|---|---|
| Effet du pois sur le blé suivant : +7 q/ha, −33 kg N/ha | Réussir, citant Intercéréales et Terres Univia | sourcé |
| Contrats pluriannuels à prix minimum en légumes secs (Qualisol) | Réussir, La Dépêche | sourcé |
| Bruche : 10 à 20 % de pertes de rendement | Réussir | sourcé |
| Objectif Terres Univia : 1 million d'hectares de légumineuses en 2030 | Pleinchamp | sourcé |
| Filière légumineuses en Beauce, avec prime filière et assurance rendement | agriculture.gouv.fr | sourcé |
| Légumineuses : environ 4 % des terres agricoles, objectif de doublement en 2030 | guide participant Hack the Fork 2026 | sourcé |

Liens :

- https://www.reussir.fr/decarbonation-il-faudrait-supprimer-600-000-ha-de-cereales-au-profit-des-legumineuses-et-du
- https://www.reussir.fr/ladepeche/qualisol-lance-sa-marque-de-legumes-secs-graines-legumineuses-de-france
- https://www.reussir.fr/legumineuses-des-leviers-de-developpement-existent
- https://www.pleinchamp.com/actualite/un-plan-triennal-a-106m-pour-projeter-les-oleoproteagineux-a-2030
- https://agriculture.gouv.fr/dans-la-beauce-la-naissance-dune-filiere

## À noter

- Le chiffre « 20 000 t produites, 35 000 t importées » cité par Qualisol est **antérieur** aux données Agreste récentes, qui donnent environ 51 600 t produites en 2025 (515 576 q, provisoire). Ne pas l'utiliser comme chiffre actuel.
- Toute valeur sans source est marquée **supposé** et vit dans `data/hypotheses.yaml`.
