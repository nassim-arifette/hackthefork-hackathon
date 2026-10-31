# Prix à protection comparable : diagnostic EXPOST_ORACLE

Ce diagnostic ajuste un multiplicateur commun sur les résultats des années testées. Il permet de comparer le niveau de prix nécessaire pour atteindre une protection réalisée proche de 80 %, à qualité relative des prix départementaux inchangée. **Il utilise les réponses du test et ne constitue donc ni une politique déployable ni un nouveau backtest hors temps.**

Chaque année reçoit le même poids. Le facteur est le quantile pondéré des ratios prix d’équilibre réalisé / prix proposé. La couverture atteinte peut dépasser légèrement la cible lorsque le seuil tombe sur un cas ou sur des ex æquo.

| Cohorte | Modèle | Facteur oracle | Tenus, années | Prix moyen €/t | Écart de prix vs M0 |
|---|---|---:|---:|---:|---:|
| all_192 | M1 | 1.282 | 80.2% | 1885 | +127 €/t |
| all_192 | QRF | 1.297 | 80.1% | 1609 | -149 €/t |
| all_192 | QRF 101 quantiles | 1.271 | 80.0% | 1597 | -161 €/t |
| all_192 | M0 | 1.311 | 80.2% | 1758 | +0 €/t |
| original_133 | M1 | 1.316 | 80.4% | 1878 | +161 €/t |
| original_133 | QRF | 1.345 | 80.5% | 1622 | -95 €/t |
| original_133 | QRF 101 quantiles | 1.351 | 80.5% | 1650 | -67 €/t |
| original_133 | M0 | 1.324 | 80.4% | 1717 | +0 €/t |

## Sélections fondées seulement sur le passé

Ces points sont distincts de la frontière oracle : aucun multiplicateur n'est réajusté avec les réponses du test. La sensibilité élargit les quantiles de calibration candidats à 0,8 / 0,9 / 0,95, tout en conservant l'objectif de 80 % dans le sélecteur. Les politiques sont exécutées symétriquement pour M0 et QRF.

| Cohorte | Distribution de départ | Modèle sélectionné | Tenus, cas | Tenus, années | Prix moyen €/t |
|---|---|---|---:|---:|---:|
| all_192 | Brute | QRF | 82.3% | 83.5% | 1984 |
| original_133 | Brute | QRF | 81.2% | 80.0% | 1925 |
| all_192 | Brute | M0 | 81.2% | 82.5% | 2208 |
| original_133 | Brute | M0 | 79.7% | 78.4% | 2132 |
| all_192 | Élargie | QRF | 82.3% | 83.4% | 2072 |
| original_133 | Élargie | QRF | 82.0% | 80.8% | 2012 |
| all_192 | Élargie | M0 | 82.8% | 84.0% | 2636 |
| original_133 | Élargie | M0 | 80.5% | 79.1% | 2549 |

`frontier.csv` donne également les niveaux 60, 70, 75, 85 et 90 %, et les points bruts sans recalibration. Les graphiques distinguent les courbes oracle des carrés bruts hors temps et, lorsqu’elles sont disponibles, des politiques calibrées uniquement sur le passé.

Les points honnêtes sont calculés avec leurs prix déjà produits, sans réajustement sur le test. Ils permettent de voir quelle part de la marge de progression diagnostiquée est effectivement capturée avant l’année à prédire. Le CSV conserve toutes les politiques, identifiées par `policy_source` pour ne pas confondre les mêmes noms entre expériences. La figure montre les 26 points initiaux en petit, les deux sélections sur distributions brutes en étoiles et les deux sélections sur distributions élargies en losanges creux.

Cette frontière concerne des multiplicateurs globaux, pas le minimum théorique de toute politique possible. Un prix moyen plus faible à ce taux global ne garantit pas un gain dans chaque département. Le taux affiché est une moyenne de taux annuels, distinct du taux calculé sur tous les cas.

Reproduction : `python pipeline/analyze_price_frontier.py`. Aucun export de production n’est modifié.
