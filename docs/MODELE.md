# Modèle et protocole effectivement implémentés

Le système calcule un prix de lentille qui atteint une marge de référence blé dans une proportion choisie de scénarios. Il compare des méthodes sur une reconstitution économique rétrospective, sans promettre la marge d'une exploitation. Les chiffres recalculés figurent dans [RESULTATS.md](RESULTATS.md), les fondements dans [RECHERCHE.md](RECHERCHE.md) et les réserves dans [LIMITES.md](LIMITES.md).

## Données et périmètre

Les rendements départementaux Agreste SAA sont exprimés en q/ha. Chaque ligne retenue a une surface d'au moins 50 ha, un rendement positif et un statut qualité 1 ou 2. Le statut de la source est une information disponible dans l'extraction utilisée : cette étude ne reconstitue pas les versions de publication effectivement connues chaque année.

Le CSV météo livré couvre 43 départements, dont les 39 départements ayant des lignes lentille utilisables et les quatre départements agricoles franciliens. Le modèle blé est limité aux départements disposant de cette météo. Le script d'acquisition couvre tous les territoires lentille utilisables, sans lire les anciens drapeaux de regroupement. La météo NASA POWER provient d'un point représentatif du contour de chaque département, sans pondération des terres agricoles.

| Variable | Agrégation annuelle |
|---|---|
| `pluie_mj` | Pluie de mars à juillet |
| `pluie_avj` | Pluie d'avril à juin |
| `j30_jj` | Nombre de jours avec température maximale >30 °C, juin–juillet |
| `gel_tardif` | Nombre de jours avec température minimale <−2 °C, 1er avril–15 mai |
| `pluie_recolte` | Pluie du 15 juillet au 15 août |
| `tmax_mj` | Température maximale moyenne de mai à juillet |

Le prix du blé est un **prix de référence reconstruit à partir d'Eurostat et d'Agreste** : un indice est ancré à 178,8 €/t en 2019, référence rendu Rouen de campagne 2019–2020. Ce n'est pas le prix payé à chaque producteur. Les prix lentille 2012–2016 sont une **référence historique nominale, non représentative d'une cotation actuelle**.

## Frontières temporelles

Pour une décision à l'année `t`, toutes les lignes `annee >= t` sont écartées avant apprentissage. Parmi les années restantes :

1. Les trois plus récentes servent exclusivement à la calibration.
2. Les deux précédentes servent exclusivement à la sélection automatique.
3. Toutes les années plus anciennes servent à l'apprentissage propre.

Ce même découpage s'applique aux candidats fixes et à `auto`. Par exemple, pour le test 2019 : apprentissage 2010–2013, sélection 2014–2015, calibration 2016–2018. Pour l'export 2026 : apprentissage 2010–2020, sélection 2021–2022, calibration 2023–2025. Le premier test dispose donc de seulement quatre années d'apprentissage.

Tous les ajustements suivants utilisent l'apprentissage propre uniquement :

- Niveau départemental : moyenne du rendement des départements ayant au moins trois années d'apprentissage. La cible est `rendement / niveau` ; une colonne `rel` préparée par l'appelant est ignorée.
- Regroupement : les valeurs doivent être identiques à 0,01 q/ha près sur au moins quatre années communes, sans divergence sur les autres années communes. Chaque paire d'un groupe doit satisfaire cette règle. Le représentant est choisi par la surface moyenne d'apprentissage, avec départage déterministe.
- Météo : centre départemental et échelle des anomalies estimés sur l'apprentissage. Un département absent utilise le centre global d'apprentissage ; ce recours constitue une hypothèse de transfert.

Les représentants sont figés pour sélection, calibration et évaluation. Les niveaux de tous les départements d'apprentissage restent disponibles pour apparier les cultures. Les anciens champs `doublon` et `serie_groupe`, calculés sur toute la période, ne commandent plus l'apprentissage. Les séries conservées sont dites **retenues après regroupement**, jamais indépendantes.

## Candidats et calibration

Tous prédisent les quantiles 0,10, 0,50 et 0,90 du rendement normalisé :

| Méthode | Définition |
|---|---|
| M0 | Tendance linéaire commune et quantiles empiriques des résidus |
| M1 | Régression quantile sur tendance et anomalies météo, pénalité fixe 0,005 |
| M2 | LightGBM quantile, 150 arbres, profondeur 3, 7 feuilles, 20 observations minimum par feuille |
| M3 | Moyenne équipondérée des quantiles M0/M1/M2 |
| `auto` | Candidat minimisant la perte pinball, moyennée à poids égal sur les deux années de sélection |

L'export utilise la procédure `auto` pour chacune des deux cultures. Les paramètres et candidats sont fixés avant ce nouveau calcul, sans nouvelle recherche guidée par son classement final. Les valeurs sont ordonnées et bornées à 0,02 pour la simulation ; ce plancher est numérique, pas agronomique.

Sur les lignes de calibration, le score vaut `max(q10 − y, y − q90)`. Avec `n` scores et une cible de couverture de 80 %, le rang utilisé est `ceil((n+1) × 0,8)`. La correction est le score à ce rang, borné inférieurement à zéro. Le même prédicteur est ensuite conservé. Il n'y a aucun réentraînement sur les années de sélection ou de calibration.

`predict_quantiles()` produit les quantiles bruts pour la perte pinball et les simulations. `predict()` produit les bornes élargies avec une médiane : ces bornes ne sont pas traitées comme des quantiles de distribution. La borne basse d'intervalle est ramenée à zéro si nécessaire. La dépendance entre années et départements empêche d'affirmer ici la garantie conformelle échangeable ; la couverture est évaluée empiriquement.

## Prix, simulation et hypothèses

Pour chaque scénario, une année passée fournit conjointement la météo des deux cultures et le prix de référence du blé. La tendance est projetée sur la campagne cible. Les rendements sont tirés dans une interpolation des trois quantiles bruts, puis convertis en t/ha.

La simulation centrale utilise des queues linéaires et des tirages résiduels indépendants entre cultures, conditionnellement à l'année rejouée. Partager la météo ne conserve pas toute la dépendance des récoltes. Les scénarios de sensibilité modifient les queues (bornées ou baisse renforcée) et les rangs résiduels entre cultures (identiques ou opposés). Ils encadrent certaines hypothèses, sans constituer une validation exhaustive des mauvaises récoltes.

Avec `yL`, `yB` en t/ha, `pB` en €/t, charges et bonus en €/ha :

```text
marge_ble = pB × yB − charges_ble
marge_lentille(P) = P × yL − charges_lentille + bonus
R = (pB × yB − charges_ble + charges_lentille − bonus) / yL
P* = quantile_tau(R)
```

L'aide non confirmée vaut zéro dans le scénario principal. Le montant de 122 €/ha figure uniquement dans une sensibilité conditionnelle à l'éligibilité et à son applicabilité. Les charges constantes et les autres hypothèses viennent de `data/hypotheses.yaml`. Il s'agit de marges reconstituées sous ces hypothèses, pas de marges historiques observées dans des exploitations.

L'export final simule 20 000 tirages par département pour une seule campagne, 2026. Le niveau de lentille francilien est transféré des producteurs voisins disponibles dans l'apprentissage. Les 200 rééchantillonnages des années météo/prix gardent modèles et niveaux figés : leur plage 10–90 % mesure une sensibilité conditionnelle aux années rejouées, pas un intervalle de confiance complet du prix.

## Évaluation et décision acheteur

Le backtest glisse de 2019 à 2025. Chaque prix est calculé avec le passé, puis confronté aux rendements et à la référence blé de l'année test. La référence historique apparie les prix d'équilibre lentille/blé par département-année, sans distribution reconstruite. Elle et M0 sont comparées aux candidats météo.

La perte pinball porte sur les quantiles bruts, la couverture sur les intervalles corrigés. Ces diagnostics de rendement sont **conditionnels à la météo réalisée** ; ils ne mesurent pas une prévision disponible avant semis. L'erreur absolue médiane est affichée en rendement normalisé ou q/ha, jamais comme une bande « ±33 % ».

Les résultats économiques montrent taux de succès, prix médian, manque de marge moyen, gravité des échecs et coût d'achat. Une grille fixe de niveaux de protection permet de comparer le compromis prix/protection. Les intervalles descriptifs de taux rééchantillonnent des années entières en gardant ensemble leurs départements ; sept blocs ne permettent pas une conclusion précise sur la population future.

Le prix proposé dans l'application est rendu au site acheteur. Le prix départ ferme utilisé pour chaque parcelle est `prix_rendu − coût_transport × distance`. La sélection et le contrat partagent le même prix, le même objectif de volume et la campagne 2026. Les volumes restent attendus, sans engagement de rendement ni d'adoption.

Le plafond acheteur par tonne entrante vaut :

```text
prix_revente × (1 − pertes_tri)
− coût_tri − coût_transformation − autres_coûts − marge_minimale
```

Le transport ferme-site est déjà inclus dans le prix rendu. Une plage de négociation existe seulement si le plafond couvre le prix nécessaire pour mobiliser le volume attendu. Le verdict concerne les paramètres saisis, pas une rentabilité certifiée.

Les tests contrôlent les données réellement ajustées, l'absence de réentraînement après calibration et l'invariance des prix lorsque toutes les données futures sont perturbées. Cette discipline de code ne transforme pas une étude historique déjà examinée en validation prospective intacte.
