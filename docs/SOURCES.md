# Sources

Chaque source utilisée, avec son étiquette et sa licence. À tenir à jour au fil de l'eau. Une source citée dans le deck ou l'interface doit figurer ici.

## Données

| Id | Source | Contenu | Étiquette | Licence | Lien |
|---|---|---|---|---|---|
| `agreste_saa` | Agreste, Statistique agricole annuelle 2010–2025 | surfaces, rendements, productions par département | mesuré | Licence Ouverte Etalab [à vérifier sur la page] | https://agreste.agriculture.gouv.fr/agreste-web/download/publication/publie/SAA-SeriesLongues/SAA-SeriesLongues-2010-2025_DonneesProvisoires-DepartementalesRegionales.zip |
| `nasa_power` | NASA POWER | météo journalière | mesuré (réanalyse) | données publiques NASA, citation demandée | https://power.larc.nasa.gov/ |
| `rpg` | IGN, Registre parcellaire graphique 2025, Île-de-France | parcelles déclarées | mesuré | Licence Ouverte Etalab [à vérifier] | https://data.geopf.fr/telechargement/resource/RPG/RPG_4-0__GPKG_LAMB93_R11_2025-01-01 |
| `contours` | gregoiredavid/france-geojson (IGN ADMIN EXPRESS) | contours des départements | mesuré | [à vérifier] | https://github.com/gregoiredavid/france-geojson |
| `comext` | Eurostat Comext, DS-045409 | importations et exportations françaises de lentilles (NC8 07134000) | mesuré | réutilisation Eurostat autorisée avec citation | https://ec.europa.eu/eurostat/comext/newxtweb/ |
| `prix_ble` | Eurostat, apri_pi_outa (AM011100, nominal), calé sur le prix rendu Rouen Agreste 2019-2020 | prix du blé tendre 2010–2025 | reconstruit à partir d’indices Eurostat et d’un ancrage Agreste | réutilisation Eurostat autorisée avec citation | https://ec.europa.eu/eurostat/databrowser/view/apri_pi_outa/default/table |
| `prix_lentille` | Eurostat, apri_ap_crpouta (02991000) | prix de vente de la lentille, France, 2012–2016 | mesuré | réutilisation Eurostat autorisée avec citation | https://ec.europa.eu/eurostat/databrowser/view/apri_ap_crpouta/default/table |
| `rendu_rouen` | Agreste, note de conjoncture grandes cultures | blé tendre rendu Rouen : 178,8 €/t en 2019-2020 | sourcé | Licence Ouverte [à vérifier] | https://agreste.agriculture.gouv.fr/agreste-web/download/publication/publie/SynGcu21367/consyn367202102GdesculturesV2.pdf |
| `douanes` | Douanes, données NC8 | importations 0713 40 (alternative à Comext) | mesuré | [à vérifier] | https://lekiosque.finances.gouv.fr/site_fr/telechargement/telechargement_SGBD.asp |
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
| Charges opérationnelles du blé tendre : 440 €/ha en 2020 | Arvalis, cité par Terre-net | sourcé |
| Charges opérationnelles de la lentille : 280 €/ha (valeurs indicatives) | wiki Triple Performance, fiche lentille | sourcé |
| Aide couplée aux légumineuses à graines, campagne 2025 : 122 €/ha | arrêté du 24 février 2026, Légifrance | sourcé |

Liens :

- https://www.reussir.fr/decarbonation-il-faudrait-supprimer-600-000-ha-de-cereales-au-profit-des-legumineuses-et-du
- https://www.reussir.fr/ladepeche/qualisol-lance-sa-marque-de-legumes-secs-graines-legumineuses-de-france
- https://www.reussir.fr/legumineuses-des-leviers-de-developpement-existent
- https://www.pleinchamp.com/actualite/un-plan-triennal-a-106m-pour-projeter-les-oleoproteagineux-a-2030
- https://agriculture.gouv.fr/dans-la-beauce-la-naissance-dune-filiere
- https://www.terre-net.fr/syndicalisme-agricole/article/223927/les-couts-de-production-ne-seront-pas-couverts-en-2023-alertent-les-cerealiers
- https://wiki.tripleperformance.fr/wiki/Lentille
- https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000053594055

## À noter

- Le chiffre « 20 000 t produites, 35 000 t importées » cité par Qualisol est **antérieur** aux données récentes : 51 558 t produites (Agreste 2025, provisoire) et 39 371 t importées (Comext 2025). Ne pas l'utiliser comme chiffre actuel.
- Ciqual (teneur en protéines) était indisponible le 30/10 (erreur 503) : l'impact protéique reste à chiffrer.
- Toute valeur sans source est marquée **supposé** et vit dans `data/hypotheses.yaml`.

## Références de méthode

Voir [RECHERCHE.md](RECHERCHE.md) pour les articles primaires consultés et les limites de leur application. Les prix lentille 2012–2016 sont une référence historique nominale, non représentative d’une cotation actuelle. L’aide conditionnelle de 122 €/ha ne vaut pas confirmation d’éligibilité : le scénario principal reste à zéro.
