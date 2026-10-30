# Notes de pitch

## Le pitch en une phrase

« Le Contrat qui Tient calcule le prix plancher d'un contrat lentille qui rapporte à l'agriculteur au moins autant que le blé 8 années sur 10, et montre quelles parcelles basculent à ce prix. »

## Les trois messages à faire passer

1. **Le verrou est mesuré.** La lentille varie deux fois plus que le blé (Agreste). Au prix de marché, elle ne gagne qu'environ une année sur deux : c'est la peur de la mauvaise année qui bloque.
2. **Le prix est calibré sur le risque, et c'est prouvé.** Sur des années jamais vues, 86 % des contrats ont tenu pour 80 % promis.
3. **Il y a un client qui paie.** La coopérative, à chaque campagne ; le même moteur s'étend à toutes les cultures sous contrat et aux assureurs.

## Questions attendues

| Question | Réponse courte |
|---|---|
| Ça finit au bétail ? | Non : des lentilles pour l'alimentation humaine, achetées par un conditionneur de légumes secs. |
| Où est l'IA ? | Un modèle d'apprentissage probabiliste : il apprend sur 294 couples département × année comment la météo déplace la distribution du rendement. Deux modèles entraînés et comparés (régression quantile, LightGBM), calibrés par conformal prediction, validés sur des années jamais vues. |
| Vous avez pris en compte la météo ? | Oui : NASA POWER journalier 2010–2025, 43 départements, six variables agronomiques. Les variables météo pèsent 61 % de ce que LightGBM a appris, et chaque année simulée rejoue une vraie année météo. |
| Quelle marge d'erreur ? | Le rendement d'une année se prédit à ±33 % ; c'est pour ça qu'on calibre un prix sur le risque plutôt que sur une prévision. L'intervalle à 80 % couvre 79 % des récoltes réelles. |
| Que perdrait l'outil sans l'IA ? | Un prix fixé sur les moyennes, comme aujourd'hui, ne tient que 32 % des contrats sur des années jamais vues. Notre modèle calibré en tient 86 %. La distribution calibrée fait l'essentiel du gain ; la météo y ajoute quatre points. |
| Pourquoi pas le modèle le plus précis ? | LightGBM prédit mieux l'année moyenne, mais il sous-estime les mauvaises : ses contrats ne tiennent que 77 % du temps. Pour protéger un revenu, la calibration de la queue compte plus que la précision moyenne. Et nous avions choisi le modèle avant de voir les résultats. |
| 1 622 €/t, c'est plus du double du marché ! | Oui, et c'est le résultat : garantir 8 années sur 10 en Île-de-France coûte cher. L'outil montre les leviers (aide couplée, bonus de rotation, autres départements : 914 €/t dans les Pyrénées-Orientales, 1 222 dans l'Indre) et le prix de chaque niveau de sécurité. |
| Ce prix est-il fiable ? | Il est incertain, et nous l'affichons : de 1 132 à 3 007 €/t à 80 %. Seize ans ne suffisent pas pour cerner les mauvaises années ; c'est la première chose qu'un pilote avec des données de coopérative améliore. |
| Pourquoi l'Île-de-France, qui produit peu de lentilles ? | C'est le territoire à conquérir : 117 000 ha de blé en Seine-et-Marne. Le modèle apprend sur les départements producteurs, et le niveau de rendement vient des voisins (Aube, Yonne, Eure-et-Loir, Loiret). C'est une limite annoncée. |
| Et à l'échelle de la parcelle ? | Limite assumée : le modèle est départemental. Les données de coopérative ou le satellite sont l'étape suivante. |
| Et 2020, le contrat a cédé ? | En Île-de-France il tient, mais sur les départements producteurs il n'a tenu que dans 44 % des cas. C'est pour ça qu'on vise 80 % et pas 100 % : un prix plancher n'est pas une assurance récolte. Les deux se complètent. |
| Et si le prix du blé flambe ? | Le prix du blé réel de chaque année est rejoué dans la simulation, 2022 compris (338 €/t). En prix fixe, de 160 à 280 €/t, P\* va de 1 180 à 2 334 €/t. Un contrat indexé sur le blé est une piste. |
| Ça existe déjà ? | Les contrats à prix minimum, oui. Un outil qui calcule ce prix sur le risque et cible les parcelles, nous ne l'avons pas trouvé. |
| Qui paie, combien ? | Les coopératives et les conditionneurs, par campagne. Les montants sont des hypothèses à tester en pilote. |

## Choix de modèle à savoir expliquer

- **Pourquoi des quantiles** : on veut la mauvaise année, pas l'année moyenne.
- **Pourquoi le conformal** : garantir que l'intervalle à 80 % contient vraiment le réel 80 % du temps.
- **Pourquoi rejouer des années entières** : conserver les liens réels entre météo, rendements et prix du blé.
- **Pourquoi P\* est un quantile** : P\* est le quantile 80 % du prix d'équilibre simulé ; au-dessus, la lentille gagne dans 80 % des scénarios.
- **Pourquoi regrouper des départements** : Agreste estime souvent la lentille au niveau régional ; compter ces séries comme indépendantes gonflerait la confiance.
