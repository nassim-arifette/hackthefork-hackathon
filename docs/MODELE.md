# Spécification du modèle

Ce document décrit le modèle de rendement, la simulation Monte-Carlo, le calcul du prix plancher et le protocole de backtest, tels qu'ils sont codés dans `pipeline/model.py`, `03_backtest.py` et `05_export.py`. Chaque membre de l'équipe doit pouvoir l'expliquer au jury.

Notations : `d` département, `t` année, `c` culture (`B` blé tendre d'hiver, `L` lentille), `y` rendement, `τ` fiabilité visée (0,8 par défaut), `r` part de la récolte refusée au tri (0,10).

---

## 1. Données d'entraînement

### Cible

`y[d, t, c]` : rendement départemental Agreste SAA, 2010–2025 (2025 provisoire), feuille `COP`, colonnes `REND_2010` à `REND_2025`.

- Libellés retenus :
  - `01 - Blé tendre d'hiver et épeautre`
  - `40 - Lentilles (y compris semences)`
- Filtres :
  - surface `SURF_t ≥ 50 ha`, pour éviter les rendements calculés sur quelques parcelles ;
  - `STATUT_QUALITE` ∈ {1, 2} : on exclut le statut 3, dont les rendements lentille sont visiblement imputés (valeurs identiques d'une année à l'autre ou entre départements, voir [DATA_INVENTORY.md](DATA_INVENTORY.md)).
- **Doublons d'estimation** : Agreste estime souvent le rendement de la lentille au niveau régional, et plusieurs départements partagent alors exactement les mêmes valeurs (par exemple l'Aube, la Marne, la Haute-Marne et les Ardennes). Deux séries identiques à 0,01 q/ha près sur au moins 8 années sont regroupées ; le département le plus cultivé représente le groupe. Les doublons sont écartés de l'entraînement mais restent consultables (niveaux de l'Île-de-France et des voisins).

Panel obtenu : 39 départements mesurés pour la lentille, mais **24 séries indépendantes**, soit 294 couples département × année. Pour le blé tendre d'hiver : 1 439 couples sur 90 séries.

Le modèle apprend un **rendement relatif** : `rel[d,t] = y[d,t] / niveau[d]`, où `niveau[d]` est le rendement moyen du département sur les années d'entraînement. Les départements deviennent comparables, et le modèle se transfère à un département peu renseigné. Pour la lentille en Île-de-France, le niveau est emprunté aux départements producteurs voisins (Aube, Marne, Yonne, Eure-et-Loir, Loiret) : 17,5 q/ha.

### Variables météo (NASA POWER, quotidien)

Un point par département, le centroïde de son contour (version 1). Les variables sont calculées pour chaque année :

| Variable | Définition | Raison agronomique |
|---|---|---|
| `pluie_mj` | cumul `PRECTOTCORR` de mars à juillet (mm) | alimentation hydrique du cycle |
| `pluie_avj` | cumul `PRECTOTCORR` d'avril à juin (mm) | eau disponible à la mise en place et à la floraison |
| `j30_jj` | nombre de jours avec `T2M_MAX` > 30 °C, juin–juillet | échaudage du blé, coulure de la lentille à la floraison |
| `gel_tardif` | nombre de jours avec `T2M_MIN` < −2 °C, 1er avril – 15 mai | dégâts sur jeunes plantes |
| `pluie_recolte` | cumul de pluie du 15 juillet au 15 août (mm) | pertes à la récolte et qualité (lentille) |
| `tmax_mj` | moyenne de `T2M_MAX`, mai–juillet (°C) | chaleur pendant le remplissage |

Chaque variable entre dans le modèle en **anomalie** : écart à la climatologie du département sur 2010–2018, divisé par l'écart-type de ces anomalies. Cette climatologie est figée avant la première année test. Une variable `tendance = (t − 2010) / 10` complète les six anomalies.

Les seuils (30 °C, −2 °C) sont des choix de l'équipe (**supposé**), à confronter aux références Arvalis et Terres Inovia. Une météo moyennée sur les surfaces cultivées du RPG reste à faire.

---

## 2. Modèles de rendement

Trois modèles sont comparés sur le même protocole. M1 a été choisi **avant** de voir le backtest ; les autres servent de références.

### M0 · Baseline sans météo

```
rel[d,t] = a + b · tendance + ε
```

Tendance linéaire commune, quantiles 10, 50 et 90 % pris dans les résidus empiriques. C'est la référence à battre : si le modèle météo ne la bat pas, on le dit.

### M1 · Régression quantile linéaire (modèle retenu)

Pour chaque quantile `q` ∈ {0,1 ; 0,5 ; 0,9} et chaque culture :

```
Q_q(rel[d,t]) = a(q) + b(q) · tendance + Σ_k β_k(q) · anomalie_k[d,t]
```

- estimation par minimisation de la pinball loss (`sklearn.linear_model.QuantileRegressor`, pénalité L1 `alpha = 0,005`, solveur HiGHS) ;
- sept coefficients par quantile, exportés dans `meta.json` et lisibles au jury : pour la lentille, au quantile 50 %, une chaleur de mai à juillet supérieure d'un écart-type réduit le rendement relatif de 0,078 ;
- les trois quantiles sont réordonnés s'ils se croisent.

### M2 · LightGBM quantile (challenger)

`objective="quantile"`, `alpha` ∈ {0,1 ; 0,5 ; 0,9}, profondeur faible (`max_depth` 3, `num_leaves` 7), 150 arbres, taux d'apprentissage 0,05, au moins 20 observations par feuille.

### Choix automatique (« auto »)

À chaque entraînement, M0, M1 et M2 sont comparés sur les trois dernières années d'entraînement (perte pinball) ; le meilleur est retenu. Ce choix n'utilise jamais l'année test.

### Résultat de la comparaison (backtest, scénario de la version 4)

| | M0 tendance | M1 retenu | M2 LightGBM | auto |
|---|---|---|---|---|
| Perte pinball | 0,1078 | 0,1103 | 0,1014 | 0,1024 |
| Couverture à 80 % | 74 % | 79 % | 84 % | 74 % |
| Contrats tenus (80 % visés) | 81 % | **87 %** | 77 % | 80 % |
| P\* Seine-et-Marne 2026 | 2 932 €/t | 1 567 €/t | 1 000 €/t | — |

Pour référence, un prix fixé sur les moyennes des années passées, sans modèle, ne tient que 29 % des contrats, avec un P\* 2026 de 742 €/t.

Le plus précis n'est pas le meilleur pour fixer un prix : LightGBM prédit mieux l'année moyenne, mais il sous-estime la queue basse du rendement de la lentille, et ses contrats tiennent moins souvent que promis. M1, choisi avant tout résultat, reste le modèle de l'application.

### Calibration conformal

Les intervalles quantiles bruts sont souvent trop étroits. On applique une **conformalized quantile regression** (CQR), en respectant le temps :

1. on entraîne sur les années d'entraînement sauf les `k` dernières (`k` = 3) ;
2. sur ces `k` années, on mesure de combien il faut élargir l'intervalle `[q0,1 ; q0,9]` pour couvrir 80 % des rendements observés : c'est `Q̂` ;
3. on réentraîne sur toutes les années d'entraînement ;
4. l'intervalle final est `[q0,1 − Q̂ ; q0,9 + Q̂]`, borné à 0,02.

Pour le modèle final de la lentille, `Q̂` vaut 0,08 en rendement relatif.

### Distribution complète

À partir des trois quantiles calibrés, on reconstruit une distribution linéaire par morceaux : interpolation entre q10, q50 et q90, queues prolongées avec la même pente, rendement borné à 0,02. On y tire ensuite les rendements.

---

## 3. Simulation Monte-Carlo

Objectif : obtenir la distribution conjointe des marges blé et lentille pour un département et la campagne 2026.

Pour chaque scénario `s` (N = 20 000) :

1. **Tirer une année historique** `t_s` parmi 2010–2025, avec la tendance projetée en 2026. On tire **la même année pour les deux cultures**, ce qui conserve leur corrélation réelle : quasi nulle au niveau national (−0,08, **mesuré**), mais variable selon les départements.
2. **Calculer les quantiles conditionnels** des deux cultures avec la météo de `t_s`, puis tirer `y_B` et `y_L` dans leurs distributions, et les multiplier par le niveau du département.
3. **Prendre le prix du blé de la même année** `t_s` dans la série mesurée (`data/prix_ble.csv` : indice Eurostat des prix à la production du blé tendre, chaîné et calé sur le prix rendu Rouen Agreste de la campagne 2019-2020). Le lien réel entre récolte et prix est conservé, et le risque de prix (2022 : 338 €/t) entre dans la simulation.
4. **Calculer les marges** (en €/ha, avec `y` en t/ha) :

```
marge_B    = p_B · y_B − charges_B
marge_L(P) = P · y_L · (1 − r) − charges_L + aide + rotation
```

Le prix garanti `P` est payé sur les **tonnes acceptées au tri**, `y_L · (1 − r)`. Agreste mesure la récolte à l'arrivée à la ferme, avant le tri de la coopérative : le refus n'est donc compté qu'une fois.

Valeurs du scénario central (`data/hypotheses.yaml`) : `charges_B` 700 €/ha et `charges_L` 500 €/ha (**supposé**, arrondis des références Cerfrance et Terres Inovia) ; `aide` 105 €/ha (**sourcé**, montant indicatif 2026 de l'aide couplée aux légumineuses) ; `rotation` 150 €/ha de bénéfice pour le blé suivant (**supposé**) ; `r` = 10 % (**supposé**).

---

## 4. Le prix plancher P\*

### Définition

P\* est le plus petit prix P tel que :

```
Pr( marge_L(P) ≥ marge_B ) ≥ τ
```

### Calcul direct

La condition `marge_L(P) ≥ marge_B` s'écrit :

```
P ≥ R_s = (p_B · y_B − charges_B + charges_L − aide − rotation) / (y_L · (1 − r))
```

`R_s` est le **prix d'équilibre** du scénario `s`. Donc :

```
P* = quantile_τ( R_s )
```

Le quantile est pris au sens strict (`method="inverted_cdf"`) : c'est le plus petit prix simulé pour lequel la lentille gagne dans au moins 80 % des scénarios, égalités comprises. C'est rapide, exact, et facile à expliquer : « dans 80 % des années simulées, ce prix suffit ».

Les scénarios où `y_L` est proche de zéro donnent un `R_s` très grand : ils se retrouvent dans les 20 % que le contrat n'assure pas. C'est la limite assumée d'un prix plancher, qui n'est pas une assurance récolte.

### Par parcelle

Le prix plancher s'entend **départ ferme**. Pour l'acheteur, le coût rendu à son site vaut :

```
coût_rendu[i] = P*_d(i) + forfait + κ · 1,3 · distance(i, site)
```

- `forfait` : 5 €/t pour l'enlèvement d'un lot agrégé de 25 t (**supposé**) ;
- `κ` : 0,12 €/t/km (**supposé**) ;
- `1,3` : passage de la distance à vol d'oiseau à la distance routière (**supposé**).

Pour un prix rendu `Q` proposé par l'acheteur, la parcelle `i` bascule si `Q − forfait − κ · 1,3 · distance(i) ≥ P*_d(i)`.

### Courbe d'offre

```
S(Q) = Σ_i surface_i · E[y_L, d(i)] · (1 − r) · 1{ parcelle i bascule à Q }
```

Les parcelles éligibles sont les parcelles RPG en blé tendre d'hiver. S(Q) est un **potentiel** en tonnes acceptées, et non une prévision d'adoption : tous les agriculteurs éligibles ne signeront pas. Le contrat de démonstration retient les parcelles éligibles les plus proches du site jusqu'au volume visé (300 t pour le pilote, 5 000 t pour l'ambition de bassin).

### Contrat indexé

Variante calculée à l'export : un plancher égal à `m × prix du blé de la récolte`. Le multiplicateur `m*` est le quantile τ de `R_s / p_B` : 7,44 pour 8 années sur 10 en Seine-et-Marne, 3,44 en médiane.

### Contrats à tranches et prime à l'hectare

`pipeline/contrats.py` et `07_contrats.py` jugent d'autres formes de contrat sur les mêmes scénarios. Avec `r = y_L · (1 − r_tri)` les tonnes acceptées par hectare :

```
versé(r) = p1 · min(r, 1) + p2 · min(max(r − 1, 0), 1) + p3 · max(r − 2, 0)   (tranches)
         ou P · r                                                          (prix unique)
         + prime_t · r + prime_ha
marge_L  = versé(r) − coût_producteur · y_L − charges_L + aide + rotation
```

- **Protection** : part des scénarios où `marge_L ≥ marge_B`.
- **Tranches calibrées** : `p2` et `p3` fixés (750 et 650 €/t, ceux du dossier pilote), `p1` est le plus petit prix entier qui atteint τ (recherche par dichotomie, la protection croît avec `p1`).
- **Prime à l'hectare calibrée** : à prix de base `P0` (900 €/t), `prime_ha* = quantile_τ( marge_B − marge_L(P0) )`, borné à 0 et arrondi à l'euro supérieur.
- **Coût moyen pour l'acheteur** : `E[versé] / E[r]`, en €/t acceptée, hors collecte et tri.

Dans le backtest, ces deux formes sont recalibrées pour chaque cas avec les scénarios des années `< t`, exactement comme P\*.

---

### Autres légumineuses

`pipeline/09_cultures.py` réutilise ce chapitre pour le pois chiche, le haricot sec, le pois protéagineux et la féverole. Chaque culture a son modèle M1, appris sur ses séries Agreste (statuts 1–2, doublons regroupés) et sur la météo NASA POWER de ses départements (`data/meteo_dept_cultures.csv`). Les anomalies météo y sont divisées par les écarts-types du modèle principal : le modèle du blé, inchangé, reçoit les mêmes variables. Le niveau de rendement francilien est celui du département quand Agreste le publie avec un statut 1 ou 2 (pois, féverole), sinon la moyenne des départements voisins du bassin parisien (pois chiche, haricot). Les tranches sont mises à l'échelle du rendement accepté moyen : bornes à 0,7 et 1,4 fois ce rendement (1 et 2 t/ha pour la lentille), prix des deuxième et troisième tranches dans les proportions de la proposition lentille.

## 5. Backtest

### Protocole glissant, sans fuite

Pour chaque année test `t` de 2019 à 2025 :

1. entraîner M0, M1 et M2 sur les années `< t` uniquement, niveaux et calibration conformal compris ;
2. calculer `P*[d, t]` pour chaque département, en rejouant la météo et le prix du blé des années `< t` ;
3. observer l'année `t` réelle : rendements Agreste, prix du blé réalisé ;
4. le contrat **a tenu** si `P*[d,t] · y_L_réel · (1 − r) − charges_L + aide + rotation ≥ p_B_réel · y_B_réel − charges_B`.

Les années test ne servent ni à l'entraînement, ni au choix des hyperparamètres, ni au choix du seuil. Le protocole est figé avant de regarder les résultats.

La référence « moyennes » fixe le prix d'équilibre avec les rendements moyens et le prix moyen du blé des années `< t`, sans distribution : c'est la façon naïve de fixer un prix.

Les contrats publiés (Unéal 900 €/t, barème NatUp 2023–2024, proposition du dossier pilote) sont jugés de la même façon, sans recalibrage : leur barème est fixe.

### Métriques

| Métrique | Ce qu'elle mesure | Cible |
|---|---|---|
| Taux de contrats tenus | fiabilité réelle du prix | proche de τ = 80 % |
| Couverture de l'intervalle 80 % | calibration du modèle de rendement | proche de 80 % |
| Pinball loss moyenne | précision des quantiles | inférieure à la baseline M0 |
| Largeur moyenne de l'intervalle | utilité (un intervalle trop large ne sert à rien) | la plus faible à couverture égale |

### Ce qu'il faut dire au jury

- **L'unité indépendante est l'année.** Les départements d'une même année partagent la même météo. Avec 7 années test, l'incertitude sur le taux de contrats tenus reste grande. On montre les résultats **année par année**.
- **2020 et 2021 sont dans la fenêtre de test.** Un modèle entraîné jusqu'en 2019 n'a jamais vu un effondrement de la lentille de cette ampleur. Les contrats cèdent ces années-là (50 % et 61 % tenus). On le montre et on l'explique.
- Si les résultats sont mauvais, ils sont affichés quand même. Le protocole n'est jamais modifié après coup pour améliorer le chiffre.

---

## 6. Incertitude sur P\*

P\* est lui-même estimé sur seize années. On le mesure par **bootstrap par blocs d'années** : 40 tirages avec remise des années 2010–2025, réentraînement des deux modèles et recalcul de P\*. Pour la Seine-et-Marne : intervalle à 80 % de 1 099 à 2 877 €/t, médiane 1 742 €/t, pour une estimation centrale de 1 567 €/t. Seize années ne suffisent pas à cerner les mauvaises années : c'est la première raison de récupérer les données de rendement des coopératives.

## 7. Sensibilités affichées

- P\* selon τ (de 50 % à 95 %) : « le prix de la sécurité ».
- P\* selon le prix du blé, fixé de 160 à 280 €/t.
- P\* selon la part refusée au tri (0, 10, 20 %), le bénéfice de rotation (0 à 200 €/ha), les charges du blé (600 à 800 €/ha) et de la lentille (400 à 600 €/ha), l'aide couplée (0, 105, 122 €/ha).
- P\* avec les hypothèses de la version 3, pour comparaison.

Ces courbes sont précalculées (`05_export.py`) et affichées à l'étape « Le contrat ». Valeurs : voir [RESULTATS.md](RESULTATS.md).
