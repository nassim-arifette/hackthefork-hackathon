# Notes de pitch

## Le pitch en une phrase

« Le Contrat qui Tient calcule le prix plancher d'un contrat lentille qui rapporte à l'agriculteur au moins autant que le blé 8 années sur 10, et montre quelles parcelles basculent à ce prix. »

## Les quatre messages à faire passer

1. **Le verrou est mesuré.** La lentille varie deux fois plus que le blé (Agreste). Aux prix de 2012–2016, elle ne gagne qu'une année sur deux face au blé francilien : c'est la peur de la mauvaise année qui bloque.
2. **Le prix est calibré sur le risque, et c'est vérifié.** Sur des années jamais vues, en protocole strict, 78 % des contrats ont tenu pour 80 % promis : la promesse est presque tenue, sans surprotection coûteuse.
3. **L'outil trouve le bon contrat.** À protection égale, un barème par tranches, qui paie cher la première tonne, coûte 18 % de moins qu'un prix unique (19 % en backtest).
4. **Il y a un client qui paie.** La coopérative, à chaque campagne : 142 coopératives agricoles et 28 unions font le commerce des grains en France (Sirene). Le même moteur s'étend aux autres légumineuses, aux autres départements et aux assureurs.

## Questions attendues

| Question | Réponse courte |
|---|---|
| Ça finit au bétail ? | Non : des lentilles pour l'alimentation humaine, achetées par un conditionneur de légumes secs. Le prix garanti ne s'applique qu'aux tonnes acceptées au tri. |
| Vous payez quelles tonnes ? | Les tonnes acceptées au tri, comme dans tout contrat de collecte : un lot refusé (bruche, impuretés, calibre) ne touche pas le prix garanti. Agreste mesure la récolte avant ce tri ; on retire 10 %, une seule fois. À 0 % de refus, le prix plancher serait de 1 411 €/t ; à 20 %, de 1 763 €/t. |
| Où est l'IA ? | Un modèle d'apprentissage probabiliste : il apprend sur 294 couples département × année comment la météo déplace la distribution du rendement. Deux modèles entraînés et comparés (régression quantile, LightGBM), calibrés par conformal prediction, validés sur des années jamais vues. |
| Vous avez pris en compte la météo ? | Oui : NASA POWER journalier 2010–2025, 43 départements, six variables agronomiques. Les variables météo pèsent 61 % de ce que LightGBM a appris, et chaque année simulée rejoue une vraie année météo. |
| Quelle marge d'erreur ? | Le rendement d'une année se prédit à ±33 % ; c'est pour ça qu'on calibre un prix sur le risque plutôt que sur une prévision. L'intervalle à 80 % couvre 79 % des récoltes réelles. |
| Que perdrait l'outil sans l'IA ? | Un prix calculé sur les moyennes, sans modèle, ne tient que 29 % des contrats sur des années jamais vues. Notre modèle calibré en tient 78 %, pour 80 % visés. La distribution calibrée fait l'essentiel du gain ; la météo apporte surtout un prix plus juste : 1 567 €/t contre 2 932 sans météo, pour un taux comparable. |
| Pourquoi pas le modèle le plus précis ? | LightGBM prédit mieux l'année moyenne, mais il sous-estime les mauvaises : ses contrats ne tiennent que 76 % du temps. Pour protéger un revenu, la calibration de la queue compte plus que la précision moyenne. Et nous avions choisi le modèle avant de voir les résultats. |
| 1 567 €/t, c'est plus du double des prix observés ! | Oui, et c'est le résultat : garantir 8 années sur 10 face au blé francilien coûte cher. L'outil montre le prix de chaque niveau de sécurité (900 €/t, le prix Unéal de 2023, protège 6 années sur 10) et les leviers : aide couplée, rotation, autres bassins (558 €/t dans les Pyrénées-Orientales, 1 115 dans l'Indre, à charges franciliennes). |
| Les contrats existants sont moins chers, ils ont tort ? | Non : ils partagent déjà le risque autrement (volumes, qualité, bassins). Face au blé francilien, le barème NatUp 2023–2024 protège 5,9 années sur 10, le prix Unéal 6,1. Le score de 29 % est celui d'un prix calculé sur des moyennes, pas celui des coopératives. |
| Alors quel contrat proposer ? | Un barème par tranches : 1 635 €/t la première tonne par hectare, puis 750 et 650. Même protection que 1 567 €/t sur toutes les tonnes, 18 % moins cher en moyenne, et en backtest 79 % de contrats tenus (78 % pour le prix unique) pour 19 % de moins. La première tonne est celle qui manque les mauvaises années. |
| Et une prime à l'hectare ? | La moins chère en moyenne (900 €/t + 491 €/ha), mais l'acheteur la paie même sans récolte, et elle a cédé lors de la flambée du blé de 2022 : 74 % de contrats tenus, sous la cible. |
| Ce prix est-il fiable ? | Il est incertain, et nous l'affichons : de 1 099 à 2 877 €/t à 80 %. Seize ans ne suffisent pas pour cerner les mauvaises années ; c'est la première chose qu'un pilote avec des données de coopérative améliore. |
| D'où viennent les charges ? | 700 €/ha pour le blé et 500 €/ha pour la lentille, arrondis des références Cerfrance et Terres Inovia ; aide couplée de 105 €/ha (montant indicatif 2026) ; 150 €/ha de bénéfice de rotation pour le blé suivant. Tout est dans un seul fichier, avec sa source et sa sensibilité. |
| Pourquoi l'Île-de-France, qui produit peu de lentilles ? | C'est le territoire à conquérir : 117 000 ha de blé en Seine-et-Marne. Le modèle apprend sur les départements producteurs, et le niveau de rendement vient des voisins (Aube, Marne, Yonne, Eure-et-Loir, Loiret). C'est une limite annoncée. |
| La SAA donne 727 ha de lentille en Île-de-France, la carte 1 095 ha ? | Les deux sont justes : la SAA rattache les terres au siège de l'exploitation, le RPG à la parcelle. 70 % de l'écart est en Seine-et-Marne, voisine des grands départements producteurs. La carte utilise le RPG, le modèle les rendements SAA. |
| Et à l'échelle de la parcelle ? | Limite assumée : le modèle est départemental. Les données de coopérative ou le satellite sont l'étape suivante. |
| Et 2020, le contrat a cédé ? | En Île-de-France il tient, mais sur les départements producteurs il n'a tenu que dans la moitié des cas. C'est pour ça qu'on vise 80 % et pas 100 % : un prix plancher n'est pas une assurance récolte. Les deux se complètent. |
| Et si le prix du blé flambe ? | Le prix du blé réel de chaque année est rejoué dans la simulation, 2022 compris (338 €/t). En prix fixe, de 160 à 280 €/t, P\* va de 1 070 à 2 348 €/t. Un contrat indexé (7,44 fois le prix du blé) déplace ce risque vers l'acheteur sans rendre le contrat moins cher. |
| Quel impact ? | Le pilote de 300 t mobilise 216 ha ; l'ambition de 5 000 t, 3 502 ha : 13 % des importations, 1 250 t de protéines, 630 t d'azote minéral non apporté et 2 644 t CO₂e d'émissions directes évitées. |
| Et pendant la saison ? | Prototype : on rejoue 2025 sur les 8 parcelles de lentille les plus proches du site, avec 148 images Sentinel-2. Six suivent le groupe, deux sont sous le groupe en mai : on sait où aller voir. Le NDVI ne prédit pas encore le rendement ; les données du pilote serviront à le caler. |
| Le satellite remplace-t-il le RPG ? | Pas seul. Avec les parcelles d'un carré de 4 km sur cinq comme exemples, il retrouve 73 % des légumineuses des autres carrés en fin de saison, avec 90 % de signalements justes, un an avant le RPG. Appris sur l'année précédente seulement, il n'en retrouve que 8 % : printemps 2024 trop nuageux, féveroles mûres plus d'un mois plus tôt en 2025. Nous montrons les deux résultats. |
| Où placer le site de collecte ? | On le déplace d'un clic : distances, parcelles et coût se recalculent. Le meilleur point gagne quelques dixièmes d'euro par tonne : avec ces coûts, le site se choisit pour la logistique, pas pour le prix. Et il existe déjà : 352 établissements du commerce de grains à moins de 15 km des parcelles franciliennes (Sirene), dont un à 1,0 km en moyenne des parcelles du pilote. Sirene ne dit pas si c'est un silo : capacité à vérifier avec le partenaire. |
| Et ailleurs en France ? | Le même calcul donne le prix de 24 départements producteurs : de 558 €/t (Pyrénées-Orientales) à 2 238 €/t (Haute-Loire), à charges franciliennes. C'est la carte de l'écran 6, touche `F`. |
| Et les assureurs ? | Même distribution de récolte : une assurance rendement à 70 % du rendement moyen coûterait 231 €/ha de prime pure en Seine-et-Marne, avec un sinistre 3 années sur 10. Le prix plancher couvre le risque de marge, l'assurance la récolte effondrée : les deux se complètent. |
| Et les autres légumineuses ? | Même moteur, cinq cultures. Pour la lentille, barème par tranches. Pour le pois chiche, le haricot, le pois et la féverole, le backtest favorise un plancher indexé sur le blé : 78 à 89 % des contrats tenus, contre 65 à 70 % à prix fixe. Budgets revus : 500, 1 000, 450 et 400 €/ha respectivement. Le pois et la féverole demandent 427 et 462 €/t pour battre le blé 8 années sur 10, contre 200 à 260 €/t dans le référentiel CRIT de plan d'entreprise. |
| Vous annonciez 87 %, c'est 78 % ? | Oui : un audit interne a trouvé que le regroupement des séries Agreste en double utilisait toute la période, y compris les années testées. Refait avec le seul passé, le taux passe de 87 à 78 %. Nous préférons le chiffre strict : il est proche de la promesse, et c'est le but. |
| Ça existe déjà ? | Les contrats à prix minimum, oui. Un outil qui calcule ce prix sur le risque et cible les parcelles, nous ne l'avons pas trouvé. |
| Qui paie, combien ? | Les coopératives et les conditionneurs, par campagne : 142 coopératives agricoles et 28 unions font le commerce des grains en France (Sirene, 31/10/2026) ; le secteur coopératif agricole pèse 2 100 entreprises et 118 Md€ de chiffre d'affaires (Coop FR, chiffres 2024). Hypothèses à tester : étude pilote à 3 000 €, puis 10 000 € par campagne et par bassin. |
| Combien coûte le pilote à l'acheteur ? | Pour 300 t avec le barème par tranches : 385 k€ d'achat en moyenne, 60 k€ de tri et 2 k€ de collecte, soit 447 k€ ou 1 489 €/t acceptée. Tri et collecte sont des hypothèses sans devis. |

## Choix de modèle à savoir expliquer

- **Pourquoi des quantiles** : on veut la mauvaise année, pas l'année moyenne.
- **Pourquoi le conformal** : garantir que l'intervalle à 80 % contient vraiment le réel 80 % du temps.
- **Pourquoi rejouer des années entières** : conserver les liens réels entre météo, rendements et prix du blé.
- **Pourquoi P\* est un quantile** : P\* est le quantile 80 % du prix d'équilibre simulé ; au-dessus, la lentille gagne dans 80 % des scénarios.
- **Pourquoi regrouper des départements** : Agreste estime souvent la lentille au niveau régional ; compter ces séries comme indépendantes gonflerait la confiance.
- **Pourquoi « 8 sur 10 » n'est pas la fiabilité de la coopérative** : c'est la part des années simulées où la marge en lentille égale ou dépasse celle du blé. Les deux autres années, l'agriculteur peut gagner moins qu'en blé.
