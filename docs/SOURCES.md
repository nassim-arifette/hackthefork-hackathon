# Sources

Chaque source utilisée, avec son étiquette et sa licence. À tenir à jour au fil de l'eau. Une source citée dans le deck ou l'interface doit figurer ici. Les références de la revue du 31/10 sont détaillées, page par page, dans [QUESTIONS.md](QUESTIONS.md), [CONTRAT_SIMULATION.md](CONTRAT_SIMULATION.md), [PILOTE_300T.md](PILOTE_300T.md) et [REVUE_FILIERE_CULTURES.md](REVUE_FILIERE_CULTURES.md).

## Données

| Id | Source | Contenu | Étiquette | Licence | Lien |
|---|---|---|---|---|---|
| `agreste_saa` | Agreste, Statistique agricole annuelle 2010–2025 | surfaces, rendements, productions par département | mesuré | Licence Ouverte Etalab [à vérifier sur la page] | https://agreste.agriculture.gouv.fr/agreste-web/download/publication/publie/SAA-SeriesLongues/SAA-SeriesLongues-2010-2025_DonneesProvisoires-DepartementalesRegionales.zip |
| `nasa_power` | NASA POWER | météo journalière | mesuré (réanalyse) | données publiques NASA, citation demandée | https://power.larc.nasa.gov/ |
| `rpg` | IGN, Registre parcellaire graphique 2025, Île-de-France | parcelles déclarées | mesuré | Licence Ouverte Etalab [à vérifier] | https://data.geopf.fr/telechargement/resource/RPG/RPG_4-0__GPKG_LAMB93_R11_2025-01-01 |
| `contours` | gregoiredavid/france-geojson (IGN Admin Express COG 2018) | contours des départements | mesuré | Licence Ouverte (Etalab), selon le dépôt | https://github.com/gregoiredavid/france-geojson |
| `comext` | Eurostat Comext, DS-045409 | importations et exportations françaises de lentilles (NC8 07134000) ; importations de 2025 par pays partenaire ; prix des importations (valeur statistique / tonnes), toutes origines et Canada | mesuré | réutilisation Eurostat autorisée avec citation | https://ec.europa.eu/eurostat/comext/newxtweb/ |
| `prix_ble` | Eurostat, apri_pi_outa (AM011100, nominal), calé sur le prix rendu Rouen Agreste 2019-2020 | prix du blé tendre 2010–2025 | mesuré | réutilisation Eurostat autorisée avec citation | https://ec.europa.eu/eurostat/databrowser/view/apri_pi_outa/default/table |
| `prix_lentille` | Eurostat, apri_ap_crpouta (02991000) | prix de vente de la lentille, France, 2012–2016 | mesuré | réutilisation Eurostat autorisée avec citation | https://ec.europa.eu/eurostat/databrowser/view/apri_ap_crpouta/default/table |
| `rendu_rouen` | Agreste, note de conjoncture grandes cultures | blé tendre rendu Rouen : 178,8 €/t en 2019-2020 | sourcé | Licence Ouverte [à vérifier] | https://agreste.agriculture.gouv.fr/agreste-web/download/publication/publie/SynGcu21367/consyn367202102GdesculturesV2.pdf |
| `sentinel2` | Copernicus Sentinel-2 L2A, catalogue Earth Search (Element 84), COG sur AWS | NDVI de 8 parcelles de lentille, mars à août 2025 ; NDVI et NDMI des parcelles de la zone du Maillon, avril à juillet 2024 et 2025 | mesuré (satellite) | données Copernicus en accès libre, citation « Copernicus Sentinel data 2024–2025 » | https://earth-search.aws.element84.com/v1 |
| `rpg_2024` | IGN, Registre parcellaire graphique 2024, Île-de-France | étiquettes d'apprentissage du transfert 2024 → 2025, annexe « Vu du ciel » | mesuré | Licence Ouverte Etalab [à vérifier] | https://data.geopf.fr/telechargement/resource/RPG/RPG_4-0__GPKG_LAMB93_R11_2024-01-01 |
| `telepac_codes` | Telepac, Dossier PAC 2025, notice « Cultures et précisions » | libellés des codes de culture du RPG affichés dans l'application | sourcé | document administratif public | https://www1.telepac.agriculture.gouv.fr/telepac/pdf/tas/2025/Dossier-PAC-2025_notice_cultures-precisions.pdf |
| `sirene` | Insee, base Sirene, via l'API Recherche d'entreprises (DINUM) | établissements actifs des entreprises du commerce de gros de céréales (NAF 46.21Z), codes 46.21Z et 52.10B, autour de l'Île-de-France : sites de collecte existants | mesuré | Licence Ouverte Etalab 2.0 | https://recherche-entreprises.api.gouv.fr/docs/ |
| `coop_fr` | Coop FR, « Les entreprises coopératives françaises – chiffres 2024 » (12 janvier 2026) | coopératives agricoles : 2 100 entreprises, 316 000 sociétaires (estimation), 200 000 salariés, 118 Md€ de chiffre d'affaires, filiales comprises | sourcé | document public | https://www.entreprises.coop/system/files/inline-files/COOP-20260112-Chiffres2024.pdf |
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

Les guides Terres Inovia pois chiche 2026, pois 2025 et féverole 2024 ont été ouverts dans leur intégralité lors de la revue filière du 31/10. Les budgets retenus et leur périmètre sont expliqués dans [REVUE_FILIERE_CULTURES.md](REVUE_FILIERE_CULTURES.md).

## Autres légumineuses (`data/cultures.yaml`)

| Affirmation | Source | Étiquette |
|---|---|---|
| Pois chiche conventionnel : itinéraire à 416–583 €/ha ; matrice de marge à 480 €/ha ; scénario central retenu à 500 €/ha | [Terres Inovia, guide pois chiche 2026, p. 4](https://www.terresinovia.fr/sites/default/files/2026-04/guide_culture_pois-chiche_2026_terresinovia.pdf) | référence publiée ; central supposé, sensibilité 400 / 500 / 600 |
| Pois chiche : 600–620 €/t payés pour la récolte standard 2025 à un producteur Pulseo/Cavac | [Réussir, témoignage du 27 juin 2026](https://www.reussir.fr/formats/temoignages/pois-chiche-label-rouge-la-culture-degage-la-meilleure-marge-de-mon) | sourcé, paiement rapporté dans une filière et une campagne identifiées |
| Pois chiche équitable : minimum conventionnel de 769 €/t pour la récolte 2025, plus 38 €/t de prime collective | [Max Havelaar France, document janvier 2026, p. 5 et 9](https://www.fairtrade.net/content/dam/fairtrade/max-havelaar-france/label-origine-france/Prix-minimum-Max-Havelaar-France-2025.pdf) | sourcé ; contrat de filière spécifique, prime collective distincte du paiement individuel |
| Pois : charges déduites de 425 et 485 €/ha, aide de 110 €/ha incluse dans les marges de la source ; central retenu à 450 €/ha | [Terres Inovia, guide pois 2025, p. 3, projection Cerfrance Nord-Est Île-de-France](https://www.terresinovia.fr/sites/default/files/2025-05/guide-de-culture-pois-conventionnel-2025.pdf) | calcul documenté ; central supposé, sensibilité 350 / 450 / 550 |
| Féverole : charges de semences, fertilisation et traitements à 300–400 €/ha ; central retenu à 400 €/ha | [Terres Inovia, guide féverole conventionnel 2024, p. 3](https://www.terresinovia.fr/sites/default/files/2025-06/guide-de-culture-feverole-conventionnel-2024.pdf) | référence publiée ; haut de plage choisi, sensibilité 300 / 400 / 500 |
| Pois protéagineux et féveroles : 200–260 €/t | [CRIT Grand Est du 16 avril 2025, p. 3](https://draaf.grand-est.agriculture.gouv.fr/IMG/pdf/crit_16_avril_2025___annexe_2___referentiel_des_prix_crit_2025.pdf) | sourcé, référence de plan d'entreprise en Champagne-Ardenne, pas cotation actuelle |
| Variantes alimentaires : pois 280 €/t ; féverole 290 €/t | Guides pois 2025 et féverole 2024, p. 3 | scénarios documentés : prix indicatif publié pour le pois ; milieu de la plage alimentaire 260–320 €/t pour la féverole |
| Haricot conventionnel en Limagne : semences 340 €/ha, récolte 450 €/ha, contrats historiques blanc 830 €/t et rouge 990 €/t | [Pleinchamp, retour de filière de 2019](https://www.pleinchamp.com/actualite/grandes-cultures~comment-produire-du-haricot-sec-en-limagne) | sourcé, historique ; frais de récolte hors du paramètre d'intrants |
| Flageolet biologique : semences 500, irrigation 450, mécanisation 100, récolte 250 €/ha | [Bio Nouvelle-Aquitaine, fiche flageolet, p. 3](https://www.bionouvelleaquitaine.com/wp-content/uploads/2023/02/Flageolet.pdf) | sourcé, exemple bio ; total non transposé au conventionnel |
| Haricot sec irrigué : 400 semences + 150 fertilisation + 150 protection + 300 eau/énergie = 1 000 €/ha | Budget construit dans [REVUE_FILIERE_CULTURES.md](REVUE_FILIERE_CULTURES.md) | supposé, sensibilité 700 / 1 000 / 1 300 ; hors mécanisation, travail, fermage et tri aval |
| Haricot sec : repère de 1 188 €/t en conventionnel pour les pertes sécheresse 2025 | [Préfecture d'Indre-et-Loire, procédure d'indemnisation publiée en 2026](https://www.indre-et-loire.gouv.fr/Actions-de-l-Etat/Agriculture-foret-et-developpement-rural/Agriculture/Les-pertes-aides-de-crises-et-indemnisations/Secheresse-de-mai-a-aout-2025) | barème administratif ISN, pas cotation ni offre d'achat ; scénario choisi à 1 200 €/t, plage 900–1 500 |
| Éligibilité des légumineuses à graines et montant indicatif de 105 €/ha pour 2026 | [Notice Telepac 2026, p. 4](https://www.telepac.agriculture.gouv.fr/telepac/pdf/tas/2026/Dossier-PAC-2026_notice_aides-couplees.pdf) | sourcé, montant indicatif 2026 |

Les charges centrales sont des choix de scénario ancrés sur ces références, avec un périmètre commun hors mécanisation, travail, fermage, frais généraux et tri aval. Le haricot inclut ses consommations variables d'eau et d'énergie. Le bonus de rotation de 150 €/ha reste `suppose` pour les quatre cultures, y compris lorsque la source décrit un gain pouvant atteindre ce montant.

## Contexte

| Affirmation | Source | Étiquette |
|---|---|---|
| Contrats pluriannuels à prix minimum en légumes secs (Qualisol) | Réussir, La Dépêche | sourcé |
| Objectif Terres Univia : 1 million d'hectares de légumineuses en 2030 | Pleinchamp | sourcé |
| Filière légumineuses en Beauce, avec prime filière et assurance rendement | agriculture.gouv.fr | sourcé |
| Légumineuses : environ 4 % des terres agricoles, objectif de doublement en 2030 | guide participant Hack the Fork 2026 | sourcé |

## Concurrence et alternatives (recherche du 1er novembre 2026)

Utilisées dans [DOSSIER.md](DOSSIER.md) §10. Aucune n'entre dans un calcul.

| Affirmation | Source | Étiquette |
|---|---|---|
| Max Havelaar France « Origine France » : plancher lentille conventionnelle de 1 019 €/t et prime collective de 51 €/t pour la récolte 2025 (ex-Poitou-Charentes), calculé sur les coûts de production, 1,5 SMIC et le surcoût des pratiques ; contrats de 3 ans ; 175 ha et 6 agriculteurs pilotes en 2025 | [Réussir](https://www.reussir.fr/grandes-cultures/commerce-equitable-max-havelaar-garantit-des-prix-planchers-pour-des-bles-et-legumineuses-francais) ; [Réussir, 21/08/2026](https://www.reussir.fr/grandes-cultures/legumineuses-une-filiere-commerce-equitable-max-havelaar-se-structure-dans-le-sud-ouest) | sourcé |
| Euralis × Bonduelle : environ 1 000 ha, 115 agriculteurs dont 40 en lentilles, contrat de production (juin 2023) | [Euralis](https://www.euralis.fr/wp-content/uploads/2023/06/1er-anniversaire-partenariat-Bonduelle-legumes-secs-juin-2023.pdf) | sourcé |
| Cavac : surfaces de légumes secs toutes contractualisées, 350 producteurs, 3 200 ha (2018) | [Réussir, 18/10/2018](https://www.reussir.fr/lesmarches/la-cavac-investit-dans-sa-station-de-legumes-secs) | sourcé |
| Hari&Co : production achetée à un prix défini à l'avance, 10 agriculteurs, 60 ha bio (2022) | [Réussir, 17/05/2022](https://www.reussir.fr/lesmarches/une-filiere-et-des-plats-cuisines-pour-harico) | sourcé |
| Sabarot, lentille verte du Puy (AOP) : contrats annuels d'environ 2 300 à 2 400 €/t (2022) | [Pleinchamp, 18/07/2022](https://www.pleinchamp.com/actualite/lentille-verte-du-puy-aop-les-raisons-d-esperer-en-2022) | sourcé |
| Assurance récolte : subvention jusqu'à 70 %, franchise de 20 %, solidarité nationale au-delà de 50 % de pertes en grandes cultures, régime 2026–2028 | [DRAAF Grand Est, novembre 2025](https://draaf.grand-est.agriculture.gouv.fr/IMG/pdf/2511_assurancerecoltes_bro-1.pdf) | sourcé |
| AXA Climate et Bessé : assurance paramétrique de la germination du colza, près de 80 000 ha en France (2023) | [GrECo, 9/05/2023](https://greco.services/parametric-insurance-rapeseed-besse-and-greco-sign-an-exclusive-distribution-partnership-agreement/) | sourcé |
| Descartes Underwriting : assurance paramétrique agricole (sécheresse, gel, chaleur) | [Descartes](https://descartesunderwriting.com/products/agriculture) | sourcé |
| USDA RMA : Revenue Protection ouverte à la lentille (pois secs, 2023) | [RMA PM-23-015](https://www.rma.usda.gov/policy-procedure/bulletins-memos/product-management-bulletin/2023/pm-23-015-2023-crop-year-cy-dry) | sourcé |
| Saskatchewan Crop Insurance : Contract Price Option ouverte à toutes les cultures (2022) ; AgriStability : 80 % de la baisse de marge au-delà de 30 % | [Farms.com, 23/02/2022](https://www.farms.com/news/saskatchewan-announces-2022-crop-insurance-program-176746.aspx) ; [AAC](https://agriculture.canada.ca/en/programs/agristability) | sourcé |
| FiLoLeG : marges des rotations avec légumineuses selon des scénarios de prix et de rendement | [Chambre d'agriculture des Hauts-de-France](https://www.hautsdefrance.chambres-agriculture.fr/fileadmin/user_upload/Hauts-de-France/171_Inst-Hauts-de-France/2-Nos-actions/DAS5-cultures-sources-proteines-vegetales/Flyer_Projet_FILOLEG.pdf) | sourcé |
| Terres Inovia, myVar : fiches de variétés de lentille et de pois chiche | [Réussir, 17/06/2021](https://www.reussir.fr/ladepeche/mieux-connaitre-les-varietes-de-lupin-lentille-et-pois-chiche-grace-myvar-de-terres-inovia) | sourcé |
| Argus Media a racheté Agritel | [Réussir](https://www.reussir.fr/argus-media-soffre-agritel) | sourcé |
| Plateformes de contrats de grains : Bushel, Grain Discovery (DTN), AgriDigital | [Bushel](https://www.bushelpowered.com/blog/investing-in-tech) ; [DTN](https://www.dtn.com/agriculture/grain-discovery/) ; [AgriDigital](https://agridigital.io/) | sourcé |
| Xarvio Field Manager : suivi des parcelles | [Xarvio](https://ag.xarvio.com/field-manager) | sourcé |
| Appel à projets de 10 M€ pour l'innovation variétale des légumineuses (juillet 2026) | [agriculture.gouv.fr](https://agriculture.gouv.fr/ouverture-dun-appel-a-projets-en-faveur-de-linnovation-varietale-des-legumineuses) | sourcé |
| Cap Protéines+ (2024–2027) : 7,5 M€ de subvention | [Terres Inovia, plaquette](https://www.terresinovia.fr/sites/default/files/document_library/20126/3146141/3332226/plaquette-cap-proteines-plus.pdf) | sourcé |
| Lentille verte du Puy : AOP ; lentille verte du Berry : IGP et Label Rouge | [INAO, Puy](https://extranet.inao.gouv.fr/fichier/PNODULentilleverteduPuy2016.pdf) ; [INAO, Berry](https://www.inao.gouv.fr/fichier/DUIGPLentilleVerteDuBerry.pdf) | sourcé |
| Aide couplée aux légumineuses à graines : montant définitif 2025 de 138,04 €/ha, selon un arrêté du 5 juin 2026 | [Le Mag Juridique](https://www.lemag-juridique.com/articles/rural-agriculture-fixation-montants-aides-couplees-pour-campagne-2025-11625.htm) | [à vérifier sur Légifrance] ; la sensibilité du modèle reste à 0 / 105 / 122 €/ha |

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
- https://www.telepac.agriculture.gouv.fr/telepac/pdf/tas/2026/Dossier-PAC-2026_notice_aides-couplees.pdf
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
- Les valeurs choisies par l'équipe sont marquées **supposé** et figurent dans `data/hypotheses.yaml` ou `data/cultures.yaml`, avec leur provenance et leurs sensibilités.
