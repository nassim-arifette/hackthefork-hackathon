# Sources

Chaque source utilisée, avec son étiquette et sa licence. À tenir à jour au fil de l'eau. Une source citée dans le deck ou l'interface doit figurer ici. Les références de la revue du 31/10 sont détaillées, page par page, dans [QUESTIONS.md](QUESTIONS.md), [CONTRAT_SIMULATION.md](CONTRAT_SIMULATION.md) et [PILOTE_300T.md](PILOTE_300T.md).

## Données

| Id | Source | Contenu | Étiquette | Licence | Lien |
|---|---|---|---|---|---|
| `agreste_saa` | Agreste, Statistique agricole annuelle 2010–2025 | surfaces, rendements, productions par département | mesuré | Licence Ouverte Etalab [à vérifier sur la page] | https://agreste.agriculture.gouv.fr/agreste-web/download/publication/publie/SAA-SeriesLongues/SAA-SeriesLongues-2010-2025_DonneesProvisoires-DepartementalesRegionales.zip |
| `nasa_power` | NASA POWER | météo journalière | mesuré (réanalyse) | données publiques NASA, citation demandée | https://power.larc.nasa.gov/ |
| `rpg` | IGN, Registre parcellaire graphique 2025, Île-de-France | parcelles déclarées | mesuré | Licence Ouverte Etalab [à vérifier] | https://data.geopf.fr/telechargement/resource/RPG/RPG_4-0__GPKG_LAMB93_R11_2025-01-01 |
| `contours` | gregoiredavid/france-geojson (IGN Admin Express COG 2018) | contours des départements | mesuré | Licence Ouverte (Etalab), selon le dépôt | https://github.com/gregoiredavid/france-geojson |
| `comext` | Eurostat Comext, DS-045409 | importations et exportations françaises de lentilles (NC8 07134000) | mesuré | réutilisation Eurostat autorisée avec citation | https://ec.europa.eu/eurostat/comext/newxtweb/ |
| `prix_ble` | Eurostat, apri_pi_outa (AM011100, nominal), calé sur le prix rendu Rouen Agreste 2019-2020 | prix du blé tendre 2010–2025 | mesuré | réutilisation Eurostat autorisée avec citation | https://ec.europa.eu/eurostat/databrowser/view/apri_pi_outa/default/table |
| `prix_lentille` | Eurostat, apri_ap_crpouta (02991000) | prix de vente de la lentille, France, 2012–2016 | mesuré | réutilisation Eurostat autorisée avec citation | https://ec.europa.eu/eurostat/databrowser/view/apri_ap_crpouta/default/table |
| `rendu_rouen` | Agreste, note de conjoncture grandes cultures | blé tendre rendu Rouen : 178,8 €/t en 2019-2020 | sourcé | Licence Ouverte [à vérifier] | https://agreste.agriculture.gouv.fr/agreste-web/download/publication/publie/SynGcu21367/consyn367202102GdesculturesV2.pdf |
| `sentinel2` | Copernicus Sentinel-2 L2A, catalogue Earth Search (Element 84), COG sur AWS | NDVI de 8 parcelles de lentille, mars à août 2025 | mesuré (satellite) | données Copernicus en accès libre, citation « Copernicus Sentinel data 2025 » | https://earth-search.aws.element84.com/v1 |
| `pilote_300t` | Jeu de l'équipe, `data/pilote_300t` | 140 lots de lentilles 2019–2025 d'une coopérative fictive | synthétique | — | [README du jeu](../data/pilote_300t/README.md) |
| `douanes` | Douanes, données NC8 | importations 0713 40 (alternative à Comext) | mesuré | [à vérifier] | https://lekiosque.finances.gouv.fr/site_fr/telechargement/telechargement_SGBD.asp |
| `cantines` | Registre national des cantines | sites de restauration collective | mesuré | [à vérifier] | https://www.data.gouv.fr/api/1/datasets/r/3f73d129-6b24-45cd-95e9-9bacc216d9d9 |
| `hestia` | HESTIA | facteurs d'impact environnemental | sourcé | CC BY 4.0 | s3://hestia-aggregated-data |

## Références techniques du scénario de la version 4

| Affirmation | Source | Étiquette |
|---|---|---|
| Rendement « en récolte, au stade arrivée ferme », production « récoltée et commercialisable » | Agreste, méthodologie de la SAA, p. 3 | sourcé |
| Charges opérationnelles de la lentille : 518 €/ha (arrondi à 500) | Terres Inovia, guide de culture lentille 2023 | sourcé, via la revue du 31/10 |
| Charges du blé déduites à 675 €/ha (arrondi à 700) : 8,5 t/ha × 200 €/t − 1 025 €/ha de marge brute | Terres Inovia, guide pois 2025, projection Cerfrance Nord-Est Île-de-France | sourcé, via la revue du 31/10 |
| Aide couplée aux légumineuses à graines : 105 €/ha indicatifs en 2026, lentilles alimentaires éligibles ; 122 €/ha en 2025 | notice Telepac 2026, p. 4 ; arrêté du 24 février 2026 | sourcé |
| Effet précédent de la lentille : +7 q/ha de blé, −55 kg N/ha | FiloLeg / Agro-Transfert, synthèse 2024 | sourcé |
| Protéines : 28,4 % de la matière sèche, 12,6 % d'eau | Terres Inovia / Terres Univia, qualité des graines, récolte 2024 | sourcé |
| Azote minéral sur blé tendre en Île-de-France : environ 177 kg N/ha | DRIAAF, Mémento 2025, p. 26 (enquête 2021) | sourcé |
| N₂O direct : EF1 = 0,010 ; PRG100 = 267 | GIEC 2019, vol. 4, tab. 11.1 ; errata AR6 du 7/10/2025 | sourcé |
| Unéal : lentilles valorisées à 900 €/t (partenariat Vivien Paille) | Unéal, décembre 2023 | sourcé |
| NatUp : 900 €/t la première tonne par hectare, 700 la deuxième, 600 au-delà (récoltes 2023 et 2024) | Union Agricole, entretien du 18 septembre 2023 | sourcé, barème reconstitué |
| NatUp : 1 000 € la première tonne par hectare, contrat triennal ; 558 t collectées en 2025 | NatUp, communiqué du 18 septembre 2025 | sourcé |
| Bruche : 10 à 20 % de pertes de rendement | Réussir | sourcé |
| Structure de coût du transport (kilomètres, temps, immobilisation) | CNR, enquête longue distance 2013 | sourcé, tarifs non repris |

Les PDF Terres Inovia n'ont pas pu être rouverts depuis l'environnement de développement (accès refusé) : leurs chiffres viennent de la revue du 31/10, à relire avant le pitch.

## Autres légumineuses (`data/cultures.yaml`)

| Affirmation | Source | Étiquette |
|---|---|---|
| Pois chiche : charges opérationnelles le plus souvent de 400 à 500 €/ha, économie jusqu'à 150 €/ha sur la culture suivante | Terres Inovia, guide de culture pois chiche 2026 | sourcé, via les extraits de recherche |
| Pois chiche, pois et haricots secs parmi les légumineuses à graines de l'aide couplée | DDT des Hautes-Pyrénées, liste des cultures 2023 | sourcé, liste à confirmer pour 2026 |
| Pois protéagineux et féveroles : 200 à 260 €/t | DRAAF Grand Est, référentiel des prix CRIT 2025 | sourcé |
| Pois : postes de charges de 2018 (semences 60, fertilisation 60 à 80, herbicides 80 à 120, fongicides 40 €/ha) | Chambre d'agriculture Centre-Val de Loire | sourcé, ancien |
| Féverole : charges proches de celles du pois | Terres Inovia, guide de culture féverole | sourcé, via les extraits de recherche |
| Haricot sec : aucune référence publique de charges ni de prix trouvée le 31/10 | — | supposé |

Liens : https://www.terresinovia.fr/sites/default/files/2026-04/guide_culture_pois-chiche_2026_terresinovia.pdf ; https://www.hautes-pyrenees.gouv.fr/contenu/telechargement/13616/94119/file/20230307_liste_des_cultures_aides_couplees_2023.pdf ; https://draaf.grand-est.agriculture.gouv.fr/IMG/pdf/crit_16_avril_2025___annexe_2___referentiel_des_prix_crit_2025.pdf ; https://wiki.tripleperformance.fr/images/fr/8/86/CA_Centre_Val_de_Loire_-_Panneau_Cultures_Avenir_2018_-10_Cultures.pdf

## Contexte

| Affirmation | Source | Étiquette |
|---|---|---|
| Contrats pluriannuels à prix minimum en légumes secs (Qualisol) | Réussir, La Dépêche | sourcé |
| Objectif Terres Univia : 1 million d'hectares de légumineuses en 2030 | Pleinchamp | sourcé |
| Filière légumineuses en Beauce, avec prime filière et assurance rendement | agriculture.gouv.fr | sourcé |
| Légumineuses : environ 4 % des terres agricoles, objectif de doublement en 2030 | guide participant Hack the Fork 2026 | sourcé |

## Hypothèses de la version 3, conservées pour comparaison

| Affirmation | Source | Étiquette |
|---|---|---|
| Charges opérationnelles du blé tendre : 440 €/ha en 2020 | Arvalis, cité par Terre-net | sourcé |
| Charges opérationnelles de la lentille : 280 €/ha (valeurs indicatives) | wiki Triple Performance, fiche lentille | sourcé |
| Effet du pois sur le blé suivant : +7 q/ha, −33 kg N/ha | Réussir, citant Intercéréales et Terres Univia | sourcé |

Liens :

- https://agreste.agriculture.gouv.fr/agreste-web/download/methode/S-SAA/Methodologie_Statistique-Agricole-Annuelle.pdf
- https://www.terresinovia.fr/sites/default/files/2025-06/guide-de-culture-lentille-2023.pdf
- https://www.terresinovia.fr/sites/default/files/2025-05/guide-de-culture-pois-conventionnel-2025.pdf
- https://www3.telepac.agriculture.gouv.fr/telepac/pdf/tas/2026/Dossier-PAC-2026_notice_aides-couplees.pdf
- https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000053594055
- https://filoleg.fr/wp-content/uploads/2024/12/Synthese-technico-economique-insertion-LAG.pdf
- https://driaaf.ile-de-france.agriculture.gouv.fr/IMG/pdf/memento_agricole_idf_2025_v2.pdf
- https://www.ipcc.ch/report/ar6/wg1/downloads/report/IPCC_AR6_WGI_Errata.pdf
- https://uneal.com/cms_filiere-lentille-uneal
- https://www.union-agricole.fr/natup-souhaite-augmenter-les-surfaces-de-lentilles
- https://natup.coop/download/5775/
- https://www.reussir.fr/legumineuses-des-leviers-de-developpement-existent
- https://www.reussir.fr/decarbonation-il-faudrait-supprimer-600-000-ha-de-cereales-au-profit-des-legumineuses-et-du
- https://www.reussir.fr/ladepeche/qualisol-lance-sa-marque-de-legumes-secs-graines-legumineuses-de-france
- https://www.pleinchamp.com/actualite/un-plan-triennal-a-106m-pour-projeter-les-oleoproteagineux-a-2030
- https://agriculture.gouv.fr/dans-la-beauce-la-naissance-dune-filiere
- https://www.terre-net.fr/syndicalisme-agricole/article/223927/les-couts-de-production-ne-seront-pas-couverts-en-2023-alertent-les-cerealiers
- https://wiki.tripleperformance.fr/wiki/Lentille

## À noter

- Le chiffre « 20 000 t produites, 35 000 t importées » cité par Qualisol est **antérieur** aux données récentes : 51 558 t produites (Agreste 2025, provisoire) et 39 371 t importées (Comext 2025). Ne pas l'utiliser comme chiffre actuel.
- Ciqual était indisponible le 30/10 (erreur 503) : la teneur en protéines vient de la fiche qualité Terres Inovia / Terres Univia (récolte 2024).
- Toute valeur sans source est marquée **supposé** et vit dans `data/hypotheses.yaml`.
