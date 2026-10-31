# Notes de pitch

## Le pitch en une phrase

« Le Contrat qui Tient calcule le prix plancher d'un contrat lentille qui rapporte à l'agriculteur au moins autant que le blé 8 années sur 10, et montre quelles parcelles basculent à ce prix. »

## Les quatre messages à faire passer

Les taux ci-dessous proviennent du backtest historique de l'application : entraînement et calibration sur les années antérieures, mais regroupements Agreste établis sur 2010–2025. Ils ne remplacent pas le benchmark multicultures strict, qui reconstruit aussi les groupes dans le temps.

1. **Le verrou est mesuré.** La lentille varie deux fois plus que le blé (Agreste). Aux prix de 2012–2016, elle ne gagne qu'une année sur deux face au blé francilien : c'est la peur de la mauvaise année qui bloque.
2. **Le prix est calibré sur le risque.** Le backtest historique observe 87,2 % de contrats tenus sur 133 cas pour une cible de 80 %, avec la limite de regroupement indiquée ci-dessus.
3. **L'outil trouve le bon contrat.** À protection égale, un barème par tranches, qui paie cher la première tonne, coûte 18 % de moins qu'un prix unique (22 % en backtest).
4. **Il y a un client qui paie.** La coopérative, à chaque campagne ; le même moteur s'étend à toutes les cultures sous contrat et aux assureurs.

## Questions attendues

| Question | Réponse courte |
|---|---|
| Ça finit au bétail ? | Non : des lentilles pour l'alimentation humaine, achetées par un conditionneur de légumes secs. Le prix garanti ne s'applique qu'aux tonnes acceptées au tri. |
| Vous payez quelles tonnes ? | Les tonnes acceptées au tri, comme dans tout contrat de collecte : un lot refusé (bruche, impuretés, calibre) ne touche pas le prix garanti. Agreste mesure la récolte avant ce tri ; on retire 10 %, une seule fois. À 0 % de refus, le prix plancher serait de 1 411 €/t ; à 20 %, de 1 764 €/t. |
| Où est l'IA ? | Un modèle d'apprentissage probabiliste : il apprend sur 294 couples département × année comment la météo déplace la distribution du rendement. Régression quantile et LightGBM sont comparés à une tendance seule ; entraînement et calibration sont glissants, avec une limite historique sur le regroupement des séries. |
| Vous avez pris en compte la météo ? | Oui : NASA POWER journalier 2010–2025, 43 départements, six variables agronomiques. Les variables météo pèsent 61 % de ce que LightGBM a appris, et chaque année simulée rejoue une vraie année météo. |
| Quelle marge d'erreur ? | Le rendement d'une année se prédit à ±33 % ; c'est pour ça qu'on calibre un prix sur le risque plutôt que sur une prévision. L'intervalle à 80 % couvre 79 % des récoltes réelles. |
| Que perdrait l'outil sans l'IA ? | Dans le backtest historique, un prix calculé sur les moyennes tient 29,3 % des contrats ; la tendance probabiliste M0 en tient 81,2 % et M1 avec météo 87,2 %. Le gain de la distribution est distinct du gain additionnel de la météo ; la cohorte historique a la limite de regroupement annoncée. |
| Pourquoi pas le modèle le plus précis ? | LightGBM prédit mieux l'année moyenne, mais il sous-estime les mauvaises : ses contrats ne tiennent que 77 % du temps. Pour protéger un revenu, la calibration de la queue compte plus que la précision moyenne. Et nous avions choisi le modèle avant de voir les résultats. |
| 1 568 €/t, c'est plus du double des prix observés ! | Oui, et c'est le résultat : garantir 8 années sur 10 face au blé francilien coûte cher. L'outil montre le prix de chaque niveau de sécurité (900 €/t, le prix Unéal de 2023, protège 6 années sur 10) et les leviers : aide couplée, rotation, autres bassins (559 €/t dans les Pyrénées-Orientales, 1 115 dans l'Indre, à charges franciliennes). |
| Les contrats existants sont moins chers, ils ont tort ? | Non : ils partagent déjà le risque autrement (volumes, qualité, bassins). Face au blé francilien, le barème NatUp 2023–2024 protège 5,9 années sur 10, le prix Unéal 6,1. Le score de 29 % est celui d'un prix calculé sur des moyennes, pas celui des coopératives. |
| Alors quel contrat proposer ? | Un barème par tranches : 1 635 €/t la première tonne par hectare, puis 750 et 650. Même protection que 1 568 €/t sur toutes les tonnes, 18 % moins cher en moyenne, et en backtest les mêmes 87 % de contrats tenus pour 22 % de moins. La première tonne est celle qui manque les mauvaises années. |
| Et une prime à l'hectare ? | La moins chère en moyenne (900 €/t + 491 €/ha), mais l'acheteur la paie même sans récolte, et elle a cédé lors de la flambée du blé de 2022 : 79 % de contrats tenus, sous la cible. |
| Ce prix est-il fiable ? | Il est incertain, et nous l'affichons : de 1 099 à 2 877 €/t à 80 %. Seize ans ne suffisent pas pour cerner les mauvaises années ; c'est la première chose qu'un pilote avec des données de coopérative améliore. |
| D'où viennent les charges ? | 700 €/ha pour le blé et 500 €/ha pour la lentille, arrondis des références Cerfrance et Terres Inovia ; aide couplée de 105 €/ha (montant indicatif 2026) ; 150 €/ha de bénéfice de rotation pour le blé suivant. Tout est dans un seul fichier, avec sa source et sa sensibilité. |
| Pourquoi l'Île-de-France, qui produit peu de lentilles ? | C'est le territoire à conquérir : 117 000 ha de blé en Seine-et-Marne. Le modèle apprend sur les départements producteurs, et le niveau de rendement vient des voisins (Aube, Marne, Yonne, Eure-et-Loir, Loiret). C'est une limite annoncée. |
| La SAA donne 727 ha de lentille en Île-de-France, la carte 1 095 ha ? | Les deux sont justes : la SAA rattache les terres au siège de l'exploitation, le RPG à la parcelle. 70 % de l'écart est en Seine-et-Marne, voisine des grands départements producteurs. La carte utilise le RPG, le modèle les rendements SAA. |
| Et à l'échelle de la parcelle ? | Limite assumée : le modèle est départemental. Les données de coopérative ou le satellite sont l'étape suivante. |
| Et 2020, le contrat a cédé ? | En Île-de-France il tient, mais sur les départements producteurs il n'a tenu que dans la moitié des cas. C'est pour ça qu'on vise 80 % et pas 100 % : un prix plancher n'est pas une assurance récolte. Les deux se complètent. |
| Et si le prix du blé flambe ? | Le prix du blé réel de chaque année est rejoué dans la simulation, 2022 compris (338 €/t). En prix fixe, de 160 à 280 €/t, P\* va de 1 070 à 2 348 €/t. Un contrat indexé (7,44 fois le prix du blé) déplace ce risque vers l'acheteur sans rendre le contrat moins cher. |
| Quel impact ? | Au site initial à 1 600 €/t rendu, la cible de 300 t sélectionne 309,7 t attendues sur 216,42 ha. Celle de 5 000 t sélectionne 5 011,6 t sur 3 501,83 ha : environ 13 % des importations, 1 253 t de protéines, 630 t d'azote minéral non apporté et 2 644 t CO₂e directes évitées. Ces potentiels ne sont pas des livraisons garanties. |
| Et pendant la saison ? | Prototype : on rejoue 2025 sur les 8 parcelles de lentille les plus proches du site, avec 148 images Sentinel-2. Six suivent le groupe, deux sont sous le groupe en mai : on sait où aller voir. Le NDVI ne prédit pas encore le rendement ; les données du pilote serviront à le caler. |
| Où placer le site de collecte ? | Deux scénarios : réduire la collecte avec un prix rendu fixe, ou réduire le coût rendu avec des prix ferme départementaux. Le site courant reste candidat ; on montre le meilleur point testé, sans preuve d'optimum global ni capacité industrielle vérifiée. À prix rendu fixe, le gain de collecte augmente la part du producteur et ne réduit pas le prix acheteur fixé. |
| Et les autres légumineuses ? | Budgets revus : pois chiche 500, haricot irrigué 1 000, pois 450 et féverole 400 €/ha. Dans le backtest historique, le prix fixe tient de 65,5 à 71,8 % des cas pour ces quatre cultures ; l'indexation, de 82,3 à 87,3 %. Ce sont des produits et hypothèses économiques différents, pas la preuve d'un meilleur modèle. Les prix fixes du pois et de la féverole sont 427 et 462 €/t pour 80 % des simulations 2026, contre 200 à 260 €/t dans le référentiel CRIT de plan d'entreprise. |
| Ça existe déjà ? | Les contrats à prix minimum, oui. Un outil qui calcule ce prix sur le risque et cible les parcelles, nous ne l'avons pas trouvé. |
| Qui paie, combien ? | Les coopératives et les conditionneurs, par campagne. Hypothèses à tester : étude pilote à 3 000 €, puis 10 000 € par campagne et par bassin. |

## Choix de modèle à savoir expliquer

- **Pourquoi des quantiles** : on veut la mauvaise année, pas l'année moyenne.
- **Pourquoi le conformal** : viser une couverture de 80 % puis mesurer sa tenue hors période d'entraînement ; avec une série temporelle courte, ce n'est pas une garantie inconditionnelle.
- **Pourquoi rejouer des années entières** : conserver le lien météo–prix du blé et l'exposition des deux cultures à la même météo ; leur dépendance résiduelle n'est pas modélisée.
- **Pourquoi P\* est un quantile** : P\* est le quantile 80 % du prix d'équilibre simulé ; au-dessus, la lentille gagne dans 80 % des scénarios.
- **Pourquoi regrouper des départements** : Agreste estime souvent la lentille au niveau régional ; compter ces séries comme indépendantes gonflerait la confiance.
- **Pourquoi « 8 sur 10 » n'est pas la fiabilité de la coopérative** : c'est la part des années simulées où la marge en lentille égale ou dépasse celle du blé. Les deux autres années, l'agriculteur peut gagner moins qu'en blé.
