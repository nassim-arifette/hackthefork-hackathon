# Pack de simulation : collecte de 300 tonnes nettes de lentilles

Ce pack permet de démontrer les paiements, le bilan matière, les refus et le budget d'un pilote. **Les 140 exploitations-campagnes sont entièrement synthétiques** : 20 fermes fictives, 7 récoltes de 2019 à 2025, 220 ha de lentilles chaque année. Il ne contient aucun relevé individuel de NatUp ou d'une autre coopérative. Les observations publiques sont isolées dans `references_publiques.csv`.

Le scénario proposé pour 2027–2029 paie 1 000 / 750 / 650 €/t par tranches marginales, avec une prime de pré-nettoyage de 30 €/t nette. Le pack le compare au barème public reconstitué de 900 / 700 / 600 €/t et à une offre uniforme de 900 €/t, sur les mêmes lots et avec les mêmes conditions de qualité, prime et frais. Les clauses sont détaillées dans [CONTRAT_SIMULATION.md](../../docs/CONTRAT_SIMULATION.md).

## Utilisation

Depuis la racine du dépôt, avec Python 3 et sa bibliothèque standard uniquement :

```bash
python3 tools/generer_pilote_300t.py --verifier-reproductibilite
```

Le générateur lit `config.json` et `contrats.json`, réécrit les quatre CSV et contrôle les bilans. L'option de reproductibilité génère une deuxième fois dans un répertoire temporaire, compare les quatre fichiers octet par octet et affiche leurs SHA-256. La graine par défaut est `20261031`. Aucune installation ni connexion réseau n'est nécessaire.

Pour conserver le jeu livré et essayer une autre configuration :

```bash
python3 tools/generer_pilote_300t.py --config chemin/config.json --sortie /tmp/pilote-variante --verifier-reproductibilite
```

Les CSV sont en UTF-8, séparateur virgule, point décimal. Ils s'importent dans Python, R, un tableur ou l'application. Les valeurs monétaires sont en euros HT. Les montants sont arrondis au centime par lot avant agrégation, avec `ROUND_HALF_UP` ; les masses sont conservées à six décimales. `synthetique` figure dans chaque ligne des trois CSV de simulation. Les lignes de références portent `reference_publique`.

| Fichier | Contenu |
|---|---|
| `config.json` | Graine, surfaces, chocs annuels, prix historiques supposés, coûts et cinq refus de scénario. |
| `contrats.json` | Barème documenté, inconnues laissées à `null`, proposition 2027–2029 et comparateur uniforme. |
| `historique_lots_synthetiques.csv` | 140 lignes ; une ligne par exploitation et campagne. |
| `resume_campagnes_synthetiques.csv` | 7 lignes ; sommes et moyennes pondérées par campagne. |
| `comparaison_baremes_synthetiques.csv` | 21 lignes annuelles plus 3 cumuls 2019–2025 ; rejeu des trois barèmes. |
| `references_publiques.csv` | 18 observations ou paramètres publics, avec périmètre, unité et URL. Une surface non publiée reste vide. |
| `../../tools/generer_pilote_300t.py` | Générateur, calculs et contrôles intégrés. |

## Ce que montre le jeu livré

Ces valeurs sont des résultats de scénario. Les récoltes brutes sont générées directement ; elles ne proviennent pas de rendements nets publics auxquels une seconde perte aurait été appliquée.

| Campagne | Récolte brute (t) | Net alimentaire payé (t) | Lots refusés | Prix moyen payé après prime (€/t nette) |
|---|---:|---:|---:|---:|
| 2019 | 374,722 | 335,786 | 0 | 662,00 |
| 2020 | 247,687 | 216,453 | 0 | 702,21 |
| 2021 | 172,681 | 118,325 | 2 | 785,55 |
| 2022 | 309,256 | 263,568 | 0 | 860,08 |
| 2023 | 439,973 | 381,562 | 0 | 915,16 |
| 2024 | 469,905 | 361,770 | 1 | 831,95 |
| 2025 | 372,462 | 237,537 | 2 | 892,63 |

Les 220 ha donnent davantage ou moins de 300 t suivant la campagne. Le volume n'est jamais corrigé pour atteindre l'objectif. Les sept récoltes cumulent 1 915,001796 t alimentaires acceptées. Les cinq refus totaux représentent 3,57 % des **lots**, un choix du scénario qui ne prétend pas mesurer une fréquence réelle.

### Comparaison des barèmes sur les sept campagnes

Les 1 540 ha ci-dessous sont des **hectares-campagnes** (220 × 7). La surface physique annuelle demeure 220 ha.

| Barème rejoué | Recette producteurs après prime (€) | Solde producteurs hors mécanisation (€/ha-campagne) | Budget achat, collecte, tri, séchage (€) | Budget par tonne nette acceptée (€/t) |
|---|---:|---:|---:|---:|
| Public reconstitué 900 / 700 / 600 | 1 650 619,71 | 582,25 | 2 091 859,16 | 1 092,35 |
| Proposition 1 000 / 750 / 650 | 1 814 978,04 | 688,98 | 2 256 217,49 | 1 178,18 |
| Uniforme 900 | 1 763 020,72 | 655,24 | 2 204 260,17 | 1 151,05 |

Dans ce jeu, la proposition augmente le paiement des producteurs de 51 957,32 € par rapport à l'uniforme, soit 33,74 €/ha-campagne, pour le même volume et les mêmes frais. Ce résultat décrit les lots générés. Il ne mesure ni une garantie de revenu, ni une probabilité de succès du pilote. La comparaison du **barème public** lui applique la prime, la qualité et les frais de la proposition synthétique ; elle ne reconstitue donc pas les conditions économiques complètes des contrats NatUp.

## Hypothèses et provenance

Les sources publiques servent à choisir des scénarios plausibles, sans reproduire une coopérative identifiée.

| Élément | Choix du générateur | Statut et justification |
|---|---|---|
| Exploitations et surfaces | 20 fermes de 6 à 16 ha de lentilles ; 220 ha/an ; six blocs de même surface par ferme | Hypothèse de dimensionnement. Le même bloc revient en lentille après six ans ; les autres cultures ne sont pas simulées. |
| Quantité | Centres bruts de 0,82 à 2,30 t/ha selon l'année ; facteur ferme et bruit annuel | Hypothèses directes, indépendantes des collectes publiques. Les années communes créent une corrélation entre fermes. 140 lignes ne sont pas 140 années indépendantes. |
| 2020 | Choc de quantité | Choix de stress, sans prétention à reconstruire une série locale observée. |
| 2021 | Choc de quantité et qualité, humidité et germination accrues | Inspiré du bilan Terres Inovia / Terres Univia du 21 octobre 2021 : rendements **nets** fortement réduits, germination et défauts après récolte humide. [Bilan 2021](https://www.terresinovia.fr/documents/20126/726505/2021_10_21_recoltelentillespoischiche2021.pdf/4c7402ec-1fcc-df4e-d5f0-99f4b0daba9d?t=1634804428742). |
| 2024 | Bon brut avec qualité variable | Choix régional de scénario. L'humidité centrale de 13,4 % est une hypothèse ; la moyenne publique de l'échantillon national est 12,6 %. |
| 2025 | Pression de bruches plus forte | Le centre de 24,4 % de grains bruchés reprend un repère public national sur 40 échantillons, sans imposer cette moyenne au jeu fictif. |
| Prix historiques | Bases supposées 650, 690, 770, 850, 900, 820 et 880 €/t | Aucun bordereau réel ; ajustement de qualité de −20, 0 ou +10 €/t accepté, prime historique fictive de 20 €/t nette pré-nettoyée. L'augmentation 2022→2023 est cohérente avec la synthèse publique OPPLAG, qui ne fournit pas ici de série individuelle. |
| Charges producteur | Intrants 350–600 €/ha, centres plus hauts en 2022–2023 ; pré-nettoyage 12 €/t récoltée | Hypothèses. Intrants : semences, fertilisation, protection et dépenses culturales directes. Mécanisation, travail, fermage et frais généraux exclus. |
| Pré-nettoyage | Retrait de 70 % des impuretés massiques initiales pour les fermes équipées | Coefficient de scénario ; ne retire pas automatiquement 70 % des grains bruchés. |
| Écarts de tri | Conversion explicite des comptages en masse, puis retrait de défauts pour atteindre un résidu de scénario | Union des défauts avec recouvrement supposé : `u = b + g − b×g` ; masse relative d'un grain atteint de 0,70 à 0,80, contre 1 pour un grain sain. Fraction massique atteinte `f = u×r / (1−u+u×r)`. La matière défectueuse retirée et restante est conservée exactement. Hypothèses de scénario, aucune efficacité industrielle mesurée. |
| Qualité finale | Humidité ≤15 %, défauts ≤2 %, aucun insecte vivant, aucune moisissure | Proposition synthétique. Une cible de défauts résiduels est tirée par lot ; la masse retirée est calculée pour l'atteindre. Cinq événements explicites provoquent des refus. |
| Tri acheteur | 180 €/t brute reçue, y compris les lots refusés après tri | Hypothèse inspirée d'un coût de tri optique bio publié par [Bio en Hauts-de-France](https://www.bio-hautsdefrance.org/systeme_bio/cultures-innovantes-de-nouvelles-opportunites-pour-les-grandes-cultures-bio/). Ce n'est pas un devis pour le pilote conventionnel. |
| Collecte acheteur | (5 + 0,12 × distance routière en km) €/t brute reçue | Hypothèse logistique ; distance fixe par ferme, de 8 à 75 km ; aucun calcul de tournées ou coût de camion complet. |
| Séchage acheteur | Si humidité >15 %, séchage à 14 % ; 3 €/t reçue par point retiré | Hypothèse explicite. À 15 % ou moins, pas de séchage et aucune réhumidification. |
| Refus | 5 lots intégralement refusés après traitement | Choix de stress : défauts résiduels, insecte vivant ou moisissure. Paiement alimentaire et valorisation des refus égaux à zéro ; le tri, la collecte et le séchage déjà effectués restent payés. |

Les observations publiques de collecte NatUp (89, 273, 558 t) et de surfaces (65 et 130 ha en 2023–2024) sont conservées comme telles. La source ne précise pas suffisamment leur assiette pour en déduire des pertes de tri. La surface 2025 reste manquante dans ce fichier. Les moyennes de qualité 2023–2025 concernent des échantillons français ; elles ne décrivent pas ces fermes fictives.

L'observatoire OPPLAG fournit des résultats agrégés : ses prix portent sur un tonnage aux normes après agréage. Les relevés individuels confidentiels ne sont pas publics. [Méthode OPPLAG 2024](https://actualites-agricoles.lacooperationagricole.coop/images/files/2024/AA-2024-04-26/Note%20me%CC%81thodo%20OPP%20LAG%20e%CC%81d%202024.pdf) ; [synthèse publique mai 2025](https://www.terresunivia.fr/fichiers/publications/PE%5B05-2025%5D_web.pdf).

## Bilans matière et argent

Pour chaque exploitation-campagne, les catégories sont exclusives :

```text
récolte brute = écarts de pré-nettoyage + brut reçu
brut reçu = eau retirée + écarts de tri + refus qualité + net alimentaire payé
écarts de tri = impuretés retirées au tri + défauts retirés au tri
```

Un pourcentage de grains bruchés est une mesure de **nombre de grains**. Les impuretés massiques, l'eau, les grains retirés par le scénario et un refus commercial entier sont quatre notions distinctes. Les pourcentages de bruches et de germination peuvent se recouvrir ; ils ne sont jamais simplement additionnés pour former une perte massique. Avec `b` et `g` en fractions de 0 à 1, le modèle suppose un recouvrement `b×g`, puis une union `u=b+g−b×g`. La masse d'un grain atteint représente entre 70 et 80 % de celle d'un grain sain. Cette hypothèse transforme explicitement le comptage en fraction massique `f` ; elle n'est pas une mesure observée.

Pour une masse `M` après retrait des impuretés et une cible résiduelle `c`, le modèle retire `R=(M×f−M×c)/(1−c)` de matière défectueuse, borné à zéro. La masse défectueuse finale vaut donc `M×f−R`, et le taux final est recalculé sur la masse restante. Il n'y a pas de retrait additionnel de grains sains dans cette version. Par exemple, 40 % de grains atteints avec une masse relative de 0,75 représentent 33,33 % de la masse : atteindre 1 % de résidu nécessite de retirer environ 32,66 % de la masse initiale des grains. Les pertes élevées des lots fortement bruchés deviennent ainsi visibles.

Le séchage conserve la matière sèche : `eau = brut_reçu × (humidité_entrée − humidité_sortie) / (100 − humidité_sortie)`. Le modèle suppose une humidité homogène du lot reçu. Les masses arrondies sont ensuite soustraites pour garantir le bilan exact ; un lot déjà sec ne gagne aucune masse fictive.

```text
paiement final = paiement avant prime + prime de service
solde producteur hors mécanisation = paiement final − intrants − pré-nettoyage
budget acheteur = paiement final + tri + collecte + séchage
```

Le solde présenté n'est pas un bénéfice net d'exploitation. Aucune aide PAC, valeur d'effet rotation, marge de blé, charge de mécanisation, rémunération du travail ou charge foncière ne s'y ajoute. Le budget acheteur n'inclut ni stockage, conditionnement final, frais généraux, investissement, ni TVA. La prime rémunère un service ; son coût réel pour l'agriculteur reste distinct dans le solde.

Le barème s'applique après agrégation **par exploitation et campagne**, sur les tonnes alimentaires acceptées : première tranche plafonnée à la surface en hectares, deuxième tranche à la même surface, puis surplus. Fractionner les livraisons ne recrée pas le droit à une première tranche. Pour 10 ha et 16 t nettes : `10 × 1 000 + 6 × 750 = 14 500 €` avant la prime éventuelle de `16 × 30 = 480 €`.

Les flux d'acompte ne sont pas simulés dans les CSV : seules les recettes finales le sont. `contrats.json` décrit une proposition d'acompte de 30 % de la recette estimée et de régularisation après agréage, avec remboursement d'un trop-versé éventuel.

## Dictionnaire : historique des lots

Les noms de champs sont en français, sans accents pour faciliter l'import. `*_pct` signifie 0 à 100, et non une proportion 0 à 1. Les champs monétaires par hectare ou par tonne sont des taux ; les champs monétaires sans dénominateur sont des totaux par exploitation-campagne.

| Champ(s) | Unité / définition |
|---|---|
| `statut_donnees` | Toujours `synthetique`. |
| `cooperative_id`, `ferme_id`, `lot_id` | Identifiants fictifs, préfixés `SYN_` ; `lot_id` est unique. |
| `campagne`, `scenario` | Année de récolte et choc commun défini dans la configuration. |
| `bloc_rotation_id` | Bloc de l'exploitation en lentille cette année ; six blocs alternent. |
| `surface_lentille_ha` | Surface de lentilles de la ferme cette année, en ha. |
| `surface_rotation_ha` | Six fois la surface annuelle ; surface de l'ensemble des six blocs de la ferme, à ne pas sommer entre années comme des hectares physiques uniques. |
| `rendement_brut_t_ha`, `recolte_brute_t` | Rendement à la récolte avant pré-nettoyage et masse récoltée. |
| `prenettoye` | `oui` ou `non` ; service réalisé à la ferme avant réception. |
| `impuretes_recolte_pct_masse` | Pourcentage massique d'impuretés dans la récolte brute. |
| `ecarts_prenettoyage_t`, `brut_recu_t` | Masse retirée à la ferme et masse réellement remise au collecteur. |
| `humidite_reception_pct` | Eau en pourcentage massique du lot reçu. |
| `impuretes_reception_pct_masse` | Impuretés massiques restant dans le lot reçu après l'éventuel pré-nettoyage. |
| `grains_bruches_reception_pct_nombre`, `grains_germes_reception_pct_nombre` | Pourcentages par nombre de grains, distincts des pertes massiques. |
| `grains_defectueux_union_pct_nombre` | Pourcentage par nombre de grains de l'union bruché ou germé, recouvrement supposé indépendant. |
| `ratio_masse_grain_defectueux_sain` | Ratio de masse individuelle atteint/sain, sans unité, de 0,70 à 0,80. |
| `defauts_avant_tri_pct_masse`, `masse_defauts_avant_tri_t` | Fraction massique défectueuse calculée et masse correspondante après séchage et retrait des impuretés. |
| `taux_perte_massique_defauts_scenario_pct` | Retrait effectif de matière défectueuse divisé par la masse après retrait de l'eau et des impuretés. |
| `eau_retiree_t` | Eau évaporée ; jamais négative. |
| `ecarts_impuretes_tri_t`, `ecarts_defauts_tri_t`, `ecarts_tri_t` | Deux catégories de matières sorties au tri et leur somme. Aucune recette de valorisation n'est supposée. |
| `net_apres_tri_avant_agreage_t` | Matière restant après séchage et tri, avant décision d'acceptation. |
| `humidite_apres_tri_pct` | Humidité finale, égale à 14 % si séchage, sinon à l'humidité reçue. |
| `masse_defauts_restants_apres_tri_t` | Masse défectueuse après retrait ; somme de cette masse et des écarts de défauts égale à la masse défectueuse initiale. |
| `defauts_apres_tri_pct` | Pourcentage massique résiduel recalculé à partir de la masse défectueuse restante et de la masse nette après tri ; la cible reste une hypothèse de scénario. |
| `insectes_vivants_apres_tri_nombre_echantillon` | Nombre dans l'échantillon de contrôle simulé ; zéro exigé. Aucune taille d'échantillon réglementaire n'est présumée. |
| `moisissure_detectee` | `oui` ou `non` ; entraîne le refus si `oui`. |
| `statut_lot`, `motif_refus` | `accepte` ou `refuse_total`, et raison ; `aucun` pour les acceptés. |
| `refus_qualite_t`, `net_alimentaire_paye_t` | Matière après tri refusée et matière alimentaire acceptée ; une seule des deux est positive par lot. |
| `prix_base_annuel_hypothese_eur_t` | Base de prix historique fictive, conservée même si le lot est refusé ; ce n'est alors pas un prix payé. |
| `ajustement_qualite_eur_t` | −20 €/t si défauts finaux >1,5 % ; +10 €/t si <0,7 % ; 0 sinon ou si refus. |
| `prix_paye_avant_prime_eur_t_nette` | Prix appliqué aux tonnes acceptées ; 0 en cas de refus. |
| `prime_service_eur_t_nette` | Prime historique fictive de 20 €/t nette si pré-nettoyé et accepté ; 0 sinon. La comparaison contractuelle utilise 30 €/t. |
| `prix_paye_apres_prime_eur_t_nette` | Prix avant prime + taux de prime ; 0 si refus. |
| `paiement_avant_prime_eur`, `prime_service_eur`, `paiement_final_producteur_eur` | Recette alimentaire hors prime, prime et leur somme. |
| `charges_intrants_hors_meca_eur_ha`, `charges_intrants_hors_meca_eur` | Coût direct supposé par ha et total ; payé même si refus. |
| `cout_prenettoyage_producteur_eur` | 12 €/t récoltée si le pré-nettoyage est effectué, payé même si refus. |
| `solde_producteur_hors_meca_eur`, `solde_producteur_hors_meca_eur_ha` | Recette finale moins intrants et pré-nettoyage, en total et par ha. |
| `distance_route_km` | Distance routière de scénario, constante par ferme. |
| `tri_effectue`, `payeur_tri` | Toujours `oui` et `acheteur` dans ce scénario. |
| `cout_tri_acheteur_eur` | 180 €/t brute reçue, même si refus après tri. |
| `cout_collecte_acheteur_eur` | Brut reçu × (5 + 0,12 × km routiers). |
| `cout_sechage_acheteur_eur` | Brut reçu × points d'humidité retirés × 3 €. |
| `budget_achat_collecte_tri_sechage_eur` | Paiement producteur + trois coûts acheteur. |

## Dictionnaire : fichiers agrégés et sources

Dans `resume_campagnes_synthetiques.csv`, les masses et montants sont les sommes des lots de la campagne. `nombre_lots_refuses` compte les refus totaux. `rendement_*_t_ha` divise la masse par la surface totale. Les `prix_moyen_*` divisent les paiements par les tonnes **acceptées**, pas par les tonnes refusées ni par la moyenne simple des prix par ferme. `recette_producteurs_eur_ha` et `solde_producteurs_hors_meca_eur_ha` sont pondérés par les surfaces. `ecart_objectif_t = net_alimentaire_paye_t − 300` ; il reste négatif lorsque le scénario manque de volume.

Dans `comparaison_baremes_synthetiques.csv`, `periode` est une campagne ou `2019-2025` pour le cumul. `bareme_id` renvoie à `contrats.json`, et `cadre_commun` rappelle l'application des mêmes conditions synthétiques. `nombre_exploitations_campagnes` compte 20 observations par année ou 140 au cumul. `surface_cumulee_ha_campagne` est le dénominateur des recettes et soldes par ha. `palier_1_t`, `palier_2_t`, `palier_3_t` sont les volumes obtenus **après** application des plafonds à chaque exploitation-campagne. `paiement_hors_prime_eur` utilise ces tranches ; `prime_service_eur` vaut 30 €/t nette pré-nettoyée acceptée ; leur somme est `paiement_producteurs_eur`. `budget_eur_t_nette_acceptee` divise le budget acheteur par le net accepté ; il inclut donc les coûts des lots finalement refusés. Les autres champs de volume, frais et solde conservent les définitions ci-dessus.

Dans `references_publiques.csv`, `reference_id` identifie l'observation, `campagne` sa période, `indicateur` sa mesure et `valeur` le chiffre publié. `unite`, `organisme`, `perimetre` et `precision` empêchent de confondre des tonnes collectées, des hectares, un taux par nombre de grains et un taux sur matière sèche. `provenance` nomme le document, et `url` permet sa consultation. Une cellule `valeur` vide signifie **non documenté**, jamais zéro.

## Contrôles intégrés

La génération échoue si un contrôle échoue : 140 IDs uniques et 20 fermes ; 220 ha/an ; retour sur un même bloc après au moins six ans ; égalité du bilan matière par lot et par année à six décimales ; conservation de la matière défectueuse et résidu compatible ; absence de masse ajoutée au séchage ; paiement et prime additionnés une seule fois ; frais de tri exclusivement chez l'acheteur ; intrants dans les bornes ; acceptation conforme aux seuils ; refus sans recette mais avec frais engagés ; plafonds par exploitation-campagne ; mêmes volumes, primes et frais pour les trois barèmes. Les bornes du deuxième et du troisième palier sont également vérifiées, ainsi que l'identité du coût, du seuil et de la cible de séchage entre configuration et contrat. L'option `--verifier-reproductibilite` ajoute le contrôle de double génération identique.

Le jeu peut servir à tester les écrans et calculs du hackathon. Une estimation de probabilité, de causalité ou de robustesse économique demanderait ensuite des observations de terrain ; aucun seuil de validation à 80 % n'est déduit de ces données générées.
