# Notes de pitch

## Le pitch en une phrase

« Le Contrat qui Tient calcule le prix plancher d'un contrat lentille qui rapporte à l'agriculteur au moins autant que le blé 8 années sur 10, et montre quelles parcelles basculent à ce prix. »

## Les trois messages à faire passer

1. **Le verrou est mesuré** : la lentille varie deux fois plus que le blé (Agreste). C'est la peur de la mauvaise année qui bloque.
2. **Le prix est calibré sur le risque, et c'est prouvé** : backtest sur des années que le modèle n'a jamais vues.
3. **Il y a un client qui paie** : la coopérative, à chaque campagne, et le moteur s'étend à toutes les cultures sous contrat.

## Questions attendues

| Question | Réponse courte |
|---|---|
| Ça finit au bétail ? | Non : des lentilles pour l'alimentation humaine, achetées par un conditionneur de légumes secs. |
| Quelle marge d'erreur ? | Couverture de l'intervalle à 80 % et taux de contrats tenus sur des années jamais vues, plus la pinball loss face à une baseline naïve. |
| Que perdrait l'outil sans l'IA ? | Sans distribution du rendement conditionnée à la météo, pas de prix calibré sur le risque : seulement une moyenne. |
| Pourquoi l'Île-de-France, qui produit peu de lentilles ? | Justement : c'est le territoire à conquérir, avec 117 000 ha de blé en Seine-et-Marne. Le modèle apprend sur les départements producteurs voisins, comme l'Aube ou l'Yonne, et s'applique avec la météo locale. C'est une limite que nous annonçons. |
| Et à l'échelle de la parcelle ? | Limite assumée : le modèle est départemental. Les données de coopérative ou le satellite sont l'étape suivante. |
| Ça existe déjà ? | Les contrats à prix minimum, oui. Un outil qui calcule ce prix sur le risque et cible les parcelles, nous ne l'avons pas trouvé. |
| Qui paie, combien ? | Les coopératives et les conditionneurs, par campagne. Les montants sont des hypothèses à tester en pilote. |
| Et si le prix du blé flambe ? | C'est un paramètre de la simulation : on le montre en direct, P\* monte. |
| Et 2020, le contrat a cédé ? | [selon le résultat] C'est pour cela qu'on vise 80 % et pas 100 % : un prix plancher n'est pas une assurance récolte. Les deux se complètent. |
| Pourquoi une régression quantile et pas un réseau de neurones ? | Environ 600 observations : un modèle linéaire quantile est plus robuste et explicable. LightGBM a servi de challenger. |

## Choix de modèle à savoir expliquer

- **Pourquoi des quantiles** : on veut la mauvaise année, pas l'année moyenne.
- **Pourquoi le conformal** : garantir que l'intervalle à 80 % contient vraiment le réel 80 % du temps.
- **Pourquoi rejouer des années météo** : conserver la corrélation réelle entre les rendements du blé et de la lentille.
- **Pourquoi P\* est un quantile** : P\* est le quantile 80 % du prix d'équilibre simulé. Au-dessus, la lentille gagne dans 80 % des scénarios.
