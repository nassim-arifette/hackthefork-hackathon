# Spécification du modèle

Ce document décrit le modèle de rendement, la simulation Monte-Carlo, le calcul du prix plancher et le protocole de backtest. Chaque membre de l'équipe doit pouvoir l'expliquer au jury.

Notations : `d` département, `t` année, `c` culture (`B` blé tendre d'hiver, `L` lentille), `y` rendement en q/ha, `τ` fiabilité visée (0,8 par défaut).

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
- **Doublons d'estimation** : certains départements ont des séries identiques (par exemple Aube et Marne pour la lentille). Ils sont estimés ensemble par l'administration. On les regroupe en une seule série pour ne pas compter deux fois la même information.

Panel attendu : environ 40 départements pour la lentille sur 16 ans, soit de l'ordre de 500 à 600 couples département × année exploitables.

### Variables météo (NASA POWER, quotidien)

Calculées par département et par année, à partir de points de grille couvrant la surface agricole du département (centroïde en version 1, moyenne pondérée par la surface agricole RPG ensuite).

| Variable | Définition | Raison agronomique |
|---|---|---|
| `pluie_mj` | cumul `PRECTOTCORR` du 1er mars au 31 juillet (mm) | alimentation hydrique du cycle |
| `bilan_printemps` | pluie − évapotranspiration, avril–juin (mm) | stress hydrique à la mise en place |
| `j30_jj` | nombre de jours avec `T2M_MAX` > 30 °C, juin–juillet | échaudage du blé, coulure de la lentille à la floraison |
| `gel_tardif` | nombre de jours avec `T2M_MIN` < −2 °C, 1er avril – 15 mai | dégâts sur jeunes plantes |
| `pluie_recolte` | cumul de pluie 15 juillet – 15 août (mm) | pertes à la récolte et qualité (lentille) |

Les variables sont exprimées en **écart à la moyenne du département** (anomalies), ce qui rend le modèle transférable d'un département à l'autre.

Les seuils (30 °C, −2 °C) sont des choix de l'équipe (**supposé**), à confronter aux références Arvalis et Terres Inovia.

---

## 2. Modèles de rendement

On compare trois modèles sur le même protocole. Le plus simple qui gagne en backtest est retenu.

### M0 · Baseline naïve

```
y[d,t] = a_d + b · t + ε
```

Effet département plus tendance linéaire. L'incertitude vient des quantiles empiriques des résidus. C'est la référence à battre : si le modèle météo ne la bat pas, on le dit.

### M1 · Régression quantile linéaire (modèle principal)

Pour chaque quantile `q` ∈ {0,1 ; 0,5 ; 0,9} et chaque culture :

```
Q_q(y[d,t]) = a_d + b · t + Σ_k β_k(q) · météo_k[d,t]
```

- `a_d` : effet département (variables indicatrices) ;
- estimation par minimisation de la pinball loss (`sklearn.linear_model.QuantileRegressor` ou `statsmodels QuantReg`) ;
- avec 500 à 600 observations, un modèle linéaire à moins de 10 coefficients météo reste lisible et robuste. On explique chaque coefficient au jury.

### M2 · LightGBM quantile (challenger)

`objective="quantile"`, `alpha` ∈ {0,1 ; 0,5 ; 0,9}, profondeur faible (`max_depth` 3, `num_leaves` ≤ 8), forte régularisation. Il ne remplace M1 que s'il gagne nettement en backtest.

### Calibration conformal

Les intervalles quantiles bruts sont souvent trop étroits. On applique une **conformalized quantile regression** (CQR), en respectant le temps :

1. on entraîne sur les années `< t − k` ;
2. on calibre sur les `k` dernières années d'entraînement (`k` = 3) ;
3. on calcule l'élargissement `Q̂` qui garantit une couverture de 80 % sur ces années de calibration ;
4. l'intervalle final est `[q0,1 − Q̂ ; q0,9 + Q̂]`.

### Distribution complète

À partir des quantiles calibrés, on reconstruit une distribution par interpolation monotone de la fonction quantile, avec des queues linéaires bornées à 0. On peut ensuite y tirer des rendements.

---

## 3. Simulation Monte-Carlo

Objectif : obtenir la distribution conjointe des marges blé et lentille pour un département et une année future.

Pour chaque scénario `s` (N = 10 000) :

1. **Tirer une année météo historique** `t_s` parmi les années d'entraînement. On tire **la même année pour les deux cultures**, ce qui conserve leur corrélation réelle : quasi nulle au niveau national (−0,08, **mesuré**), mais variable selon les départements.
2. **Calculer les quantiles conditionnels** des deux cultures avec la météo de `t_s`, puis tirer `y_B` et `y_L` dans leurs distributions.
3. **Tirer un prix du blé** `p_B` dans la série historique (même année `t_s` si la série le permet, pour garder le lien entre récolte et prix).
4. **Calculer les marges** (en €/ha, avec `y` converti en t/ha) :

```
marge_B = p_B · y_B − charges_B
marge_L(P) = P · y_L − charges_L + bonus_rotation
```

`charges_B`, `charges_L` et `bonus_rotation` sont des paramètres **supposés** ou **sourcés**, exposés dans l'interface.

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
P ≥ R_s = (p_B · y_B − charges_B + charges_L − bonus_rotation) / y_L
```

`R_s` est le **prix d'équilibre** du scénario `s`. Donc :

```
P* = quantile_τ( R_s )
```

Le prix plancher est simplement le quantile 80 % des prix d'équilibre simulés. C'est rapide, exact, et facile à expliquer : « dans 80 % des années simulées, ce prix suffit ».

Les scénarios où `y_L` est proche de zéro donnent un `R_s` très grand : ils se retrouvent dans les 20 % que le contrat n'assure pas. C'est la limite assumée d'un prix plancher, qui n'est pas une assurance récolte.

### Par parcelle

Le prix est fixé « départ ferme ». Pour l'acheteur, le coût rendu à son site vaut :

```
coût_rendu[i] = P*_d(i) + κ · distance(i, site)
```

- `κ` : coût de transport en €/t/km (**supposé**, paramètre) ;
- `distance` : distance routière approchée par la distance à vol d'oiseau × 1,3 (**supposé**).

Pour un prix rendu `Q` proposé par l'acheteur, la parcelle `i` bascule si `Q − κ · distance(i) ≥ P*_d(i)`.

### Courbe d'offre

```
S(Q) = Σ_i surface_i · E[y_L, d(i)] · 1{ Q − κ · distance(i) ≥ P*_d(i) }
```

Les parcelles éligibles sont les parcelles RPG en blé tendre d'hiver. S(Q) est un **potentiel** et non une prévision d'adoption : tous les agriculteurs éligibles ne signeront pas. Un taux d'adoption `α` (**supposé**) peut être appliqué pour un scénario réaliste.

---

## 5. Backtest

### Protocole glissant, sans fuite

Pour chaque année test `t` de 2019 à 2025 :

1. entraîner M0, M1 et M2 sur les années `< t` uniquement, calibration conformal comprise ;
2. calculer `P*[d, t]` pour chaque département, avec les prix du blé connus avant `t` ;
3. observer l'année `t` réelle : rendements Agreste, prix du blé réalisé ;
4. le contrat **a tenu** si `P*[d,t] · y_L_réel − charges_L + bonus ≥ p_B_réel · y_B_réel − charges_B`.

Les années test ne servent ni à l'entraînement, ni au choix des hyperparamètres, ni au choix du seuil. Le protocole est figé avant de regarder les résultats.

### Métriques

| Métrique | Ce qu'elle mesure | Cible |
|---|---|---|
| Taux de contrats tenus | fiabilité réelle du prix | proche de τ = 80 % |
| Couverture de l'intervalle 80 % | calibration du modèle de rendement | proche de 80 % |
| Pinball loss moyenne | précision des quantiles | inférieure à la baseline M0 |
| Largeur moyenne de l'intervalle | utilité (un intervalle trop large ne sert à rien) | la plus faible à couverture égale |

### Ce qu'il faut dire au jury

- **L'unité indépendante est l'année.** Les départements d'une même année partagent la même météo. Avec 7 années test, l'incertitude sur le taux de contrats tenus reste grande. On montre les résultats **année par année**.
- **2020 et 2021 sont dans la fenêtre de test.** Un modèle entraîné jusqu'en 2019 n'a jamais vu un effondrement de la lentille de cette ampleur. Il est probable que le contrat n'ait pas tenu partout ces années-là. On le montre et on l'explique.
- Si les résultats sont mauvais, ils sont affichés quand même. Le protocole n'est jamais modifié après coup pour améliorer le chiffre.

---

## 6. Sensibilités à montrer

- P\* selon τ (de 50 % à 95 %) : « le prix de la sécurité ».
- P\* selon le prix du blé (bas, médian, haut).
- P\* selon les charges de la lentille (± 20 %).
- P\* avec et sans bonus de rotation.

Ces courbes sont précalculées et affichées dans l'onglet « Hypothèses ».
