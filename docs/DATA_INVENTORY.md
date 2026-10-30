# Inventaire des données

Ce que contiennent réellement les données, vérifié en les ouvrant. Les éléments non encore inspectés sont marqués **à inspecter**.

---

## 1. Agreste SAA 2010–2025 (vérifié le 30/10/2026)

- **Source** : lien officiel `SAA-SeriesLongues-2010-2025_DonneesProvisoires-DepartementalesRegionales.zip` (7,1 Mo).
- **Contenu** : deux fichiers XLSX.
  - `SAA_2010-2025_provisoires_donnees_departementales.xlsx` (11,2 Mo) ;
  - `SAA_2010-2025_provisoires_donnees_regionales.xlsx` (3,6 Mo).
- **Données arrêtées au 30/03/2026**, 2025 provisoire.
- **Unités** : surfaces en ha, productions en quintaux, rendements en q/ha (indiqué en tête de feuille).

### Structure de la feuille `COP` (céréales, oléagineux, protéagineux)

- En-tête à la ligne 6 (lignes 1 à 5 : titre et notes).
- Colonnes : `LIB_REG2`, `LIB_DEP`, `LIB_SAA`, `STATUT_QUALITE`, puis `SURF_2010` … `SURF_2025`, `REND_2010` … `REND_2025`, `PROD_2010` … `PROD_2025`.
- 4 500 lignes, 52 colonnes : 100 départements × 45 libellés de culture.
- `STATUT_QUALITE` prend les valeurs 1, 2, 3 et `NC`. La note méthodologique d'Agreste définit ces statuts [à lire pour la définition exacte].

### Cultures présentes (légumineuses)

`37` légumes à cosse d'origine tropicale, `38` féveroles et fèves, `39` haricots secs, **`40` lentilles**, `41` pois protéagineux, `42` mélange de pois, `43` pois chiches, `44` lupin doux, `45` autres protéagineux, `46` total.

### Lentille : ce que disent les chiffres

| Indicateur | Valeur | Étiquette |
|---|---|---|
| Lignes par statut qualité | statut 1 : 25 ; statut 2 : 15 ; statut 3 : 60 | mesuré |
| Départements avec ≥ 10 années à ≥ 50 ha et rendement renseigné | 44 | mesuré |
| Surface nationale | 12 186 ha (2010) → 35 869 ha (2020) → 33 927 ha (2025) | mesuré |
| Production nationale | 535 766 q en 2024 ; 515 576 q en 2025 (provisoire) | mesuré |
| Coefficient de variation du rendement national 2010–2025 | lentille 0,20 ; blé tendre d'hiver 0,09 (écart-type d'échantillon) | calculé sur mesuré |
| Coefficient de variation dans les 15 premiers départements | 0,24 à 0,38 | calculé sur mesuré |
| Corrélation des rendements nationaux lentille / blé | −0,08 (16 années) | calculé sur mesuré |
| Part de la surface dans les 5 premiers départements | 47 % | calculé sur mesuré |

Principaux départements (surface moyenne 2010–2025) : Haute-Loire, Indre, Aube, Yonne, Gers, Marne, Cher, Vendée, Charente-Maritime, Deux-Sèvres, Charente, Côte-d'Or, Eure-et-Loir, Haute-Marne, Loiret.

### Rendements nationaux (moyenne pondérée par la surface, q/ha)

| Année | 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Blé tendre d'hiver | 72,5 | 68,1 | 73,1 | 74,0 | 74,9 | 79,5 | **53,8** | 73,7 | 69,8 | 79,1 | 68,5 | 71,1 | 71,8 | 73,8 | 60,9 | 74,3 |
| Lentille | 15,2 | 17,0 | 16,8 | 16,2 | 13,5 | 13,3 | 13,4 | 12,8 | 14,0 | 12,7 | **8,2** | **8,6** | 11,1 | 12,9 | 17,0 | 15,2 |

Chocs utilisés pour le replay (écart à la moyenne des 5 années précédentes) :

- **2016** : blé −27 %, lentille −13 % ;
- **2020** : blé −4 %, lentille −38 %.

### Île-de-France : une zone de faible culture de lentille

| Département | Lentille 2025 (ha) | Statut | Observation |
|---|---|---|---|
| 77 Seine-et-Marne | 226 | 3 | rendements variables |
| 78 Yvelines | 245 | 3 | 9,0 q/ha en 2013, 2016 et 2019 : valeur visiblement imputée |
| 91 Essonne | 207 | 3 | 2,5 à 5,4 q/ha : très bas |
| 95 Val-d'Oise | 49 | 3 | |

- Le pois chiche affiche des rendements **identiques** dans les quatre départements (32, 41, 17 q/ha certaines années) : estimation régionale.
- Le blé tendre d'hiver couvre 116 585 ha en Seine-et-Marne en 2025 (statut 1).

**Conséquence** : le modèle de rendement lentille est entraîné sur le **panel national** (statuts 1 et 2), puis appliqué à l'Île-de-France avec la météo locale. Les départements voisins bien renseignés (Aube, Marne, Yonne, Eure-et-Loir, Loiret) servent d'appui. C'est une limite annoncée dans [LIMITES.md](LIMITES.md).

### Séries identiques entre départements

Aube et Marne présentent des rendements lentille identiques sur plusieurs années (25 ; 25 ; 22 ; 16 ; 8 ; 22 q/ha en 2015, 2016, 2019, 2020, 2021, 2024). Ces séries sont regroupées avant l'entraînement pour ne pas compter deux fois la même information.

---

## 2. NASA POWER (vérifié le 30/10/2026)

- API `power.larc.nasa.gov/api/temporal/daily/point`, communauté `AG`, réponse JSON.
- Requête test réussie (Seine-et-Marne, mars 2016, `T2M_MAX` et `PRECTOTCORR`).
- Paramètres prévus : `T2M_MAX`, `T2M_MIN`, `PRECTOTCORR`, `EVPTRNS` ou évapotranspiration de référence [nom exact à vérifier].

---

## 3. RPG Île-de-France 2025 (vérifié le 30/10/2026)

- **Source** : IGN, `RPG_4-0__GPKG_LAMB93_R11_2025-01-01.7z` (94 Mo), sur data.geopf.fr.
- **Couches** : `RPG_Parcelles` (125 212 parcelles), `RPG_Ilots`, `RPG_SNA` (éléments non agricoles), `RPG_ZDH`. Projection Lambert-93 (EPSG:2154).
- **Colonnes de `RPG_Parcelles`** : `id_parcel`, `surf_parc` (ha), `cat_cult_p`, `code_cultu`, `code_group`, `precision`, `gcp`, `pp`, `bio`, `iae`. Aucun identifiant d'exploitant.
- **Blé tendre d'hiver** (`BTH`) : 22 915 parcelles, 189 636 ha.
- **Lentille** (`LEC`, libellé à vérifier dans la nomenclature) : 178 parcelles, 1 095 ha. Agreste donne environ 730 ha pour 77, 78, 91 et 95 : écart à expliquer (périmètre, définition).
- **Retenues pour la carte** : parcelles `BTH` et `LEC` d'au moins 1 ha dans 77, 78, 91 et 95, soit 20 922 parcelles, simplifiées à 8 m.

## 4. Prix et commerce (vérifié le 30/10/2026)

- **Prix du blé tendre** : l'indice Eurostat des prix à la production (France, nominal) existe pour 2010–2025 en trois bases (2010, 2015, 2020). Il est chaîné sur la base 2015 et calé sur le prix rendu Rouen d'Agreste (178,8 €/t en 2019-2020). Les prix absolus Eurostat pour la France s'arrêtent en 2016 et sont incohérents avec l'indice (+39 % de 2010 à 2015, contre +3 % pour l'indice) : écartés.
- **Prix de la lentille** : prix de vente Eurostat de 650 à 779 €/t sur 2012–2016. Les valeurs 2010 et 2011 (140 €/t) sont incohérentes avec la suite : écartées.
- **Commerce** : Comext, NC8 07134000, France. Importations : 29 101 t (2020), 42 188 t (2024), 39 371 t (2025). Exportations : environ 5 000 t par an.

## 5. Estimations régionales dans Agreste

En comparant les séries, plusieurs départements ont des rendements de lentille **strictement identiques** sur 8 années ou plus : ils sont estimés ensemble. Exemples : Ardennes, Aube, Marne et Haute-Marne ; Côte-d'Or, Nièvre, Saône-et-Loire et Yonne ; huit départements d'Auvergne-Rhône-Alpes autour de la Haute-Loire. Sur 39 départements mesurés, il reste **24 séries indépendantes**. Pour le blé, seuls les petits départements franciliens (93, 94) et la Corse sont concernés.

## 6. À inspecter

| Jeu | Questions à trancher |
|---|---|
| Douanes 0713 (Drive) | recoupement avec Comext ; importations par pays, en masse et en valeur |
| Registre des cantines | colonnes utiles pour l'extension « débouchés » |
| Ciqual | teneur en protéines de la lentille sèche (site indisponible le 30/10) |
