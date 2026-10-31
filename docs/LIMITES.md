# Limites et portée des résultats

Les résultats de [RESULTATS.md](RESULTATS.md) sont une reconstitution sous hypothèses. Ils ne garantissent ni le rendement d'une parcelle, ni la marge d'une exploitation, ni la livraison du volume attendu. Le protocole exact est décrit dans [MODELE.md](MODELE.md).

| Limite | Conséquence | Traitement actuel et prochaine validation utile |
|---|---|---|
| Peu d'années | Le premier test n'a que quatre années d'apprentissage ; deux années de sélection peuvent donner un classement instable. | Candidats et paramètres fixes, comparaison année par année ; recueillir davantage de campagnes. |
| Étude déjà examinée rétrospectivement | Le code évite les fuites temporelles, mais l'équipe a déjà vu les résultats de 2019–2025. | Ne pas qualifier ce jeu de validation prospective intacte ; figer un protocole avant une nouvelle campagne ou cohorte. |
| Dépendances temporelles et spatiales | Les observations département-année ne sont pas autant de répétitions indépendantes. | Bootstrap descriptif d'années entières ; ne pas annoncer de garantie conformelle théorique dans ce contexte. |
| Regroupement heuristique | Des rendements identiques suggèrent une estimation commune, sans prouver l'origine de chaque chiffre ou l'indépendance restante. | Regroupement et choix du représentant sur l'apprentissage seulement ; conserver la traçabilité et obtenir des données de terrain. |
| Rendements départementaux | Le risque individuel peut différer fortement de celui d'un département moyen. | Pas de garantie parcellaire ; valider sur rendements et charges d'exploitations. |
| Transfert de la lentille vers l'Île-de-France | Le niveau vient de voisins ; la météo d'un territoire absent peut être centrée sur la moyenne globale d'apprentissage. | Hypothèse de transfert explicite ; suivi d'un pilote francilien requis. |
| Météo à un point par département | L'exposition des parcelles et des zones réellement cultivées peut différer. | CSV couvrant 43 départements, dont tous les territoires lentille utilisables ; améliorer l'agrégation spatiale et les stades phénologiques. |
| Diagnostics conditionnels à la météo réalisée | Une bonne précision rétrospective du rendement ne prouve pas une bonne prévision avant semis. | Séparer ce diagnostic de la décision de prix, qui rejoue seulement le passé. |
| Trois quantiles ne définissent pas toute une distribution | Queues, plancher numérique 0,02 et dépendance résiduelle peuvent modifier sensiblement P*. | Quantiles bruts séparés des intervalles ; sensibilités aux queues et aux rangs entre cultures. Ni un stress choisi ni une bonne couverture ne prouvent la distribution complète. |
| Incertitude du prix incomplète | La plage 10–90 % du rééchantillonnage ne comprend pas l'incertitude d'estimation du modèle ou du transfert territorial. | Modèles figés, libellé descriptif ; ne pas la vendre comme un intervalle de confiance complet. |
| Référence blé reconstruite | L'ancrage rendu Rouen ne représente pas tous les prix départ ferme. | Libellé Eurostat/Agreste, analyse de sensibilité ; recueillir des références producteur cohérentes. |
| Référence lentille ancienne | Les prix nominaux 2012–2016 ne décrivent pas le marché actuel. | Prix acheteur saisi comme hypothèse ; référence historique datée uniquement. |
| Charges constantes et aide conditionnelle | Les marges calculées ne sont pas des marges comptables historiques. | Zéro aide non confirmée dans le scénario principal ; 122 €/ha seulement sous réserve d'éligibilité, sensibilités de charges affichées. |
| Source publiée aujourd'hui | La série peut comprendre révisions et valeurs provisoires inconnues à la date historique simulée. | Décrire une reconstitution avec la version actuelle ; un vrai backtest « tel que connu à l'époque » nécessite des archives de publication. |
| RPG et aptitude agronomique | Une parcelle déclarée en blé n'est pas automatiquement adaptée à la lentille ou disponible à la rotation. | Potentiel d'offre, pas prévision d'adoption ; intégrer sols, rotations et volonté de signature. |
| Volume attendu | Surface multipliée par rendement moyen n'assure ni la récolte ni la livraison contractuelle. | Une seule campagne cible ; tester risque de volume, adoption et pertes qualité dans un pilote. |
| Replays 2016/2020 | Le choc lentille national est appliqué au niveau simulé francilien actuel ; ce n'est pas un backtest local hors échantillon. | Présenter ces écrans comme scénarios de stress illustratifs. |
| Plafond acheteur hypothétique | Prix de revente, pertes au tri, coûts et marge minimale ne sont pas des données vérifiées de coopérative. | Paramètres modifiables, unités explicites et verdict conditionnel ; valider devis, qualité, financement et débouchés. |
| Un prix plancher n'est pas une assurance récolte | Une récolte quasi nulle peut empêcher d'atteindre la marge malgré un prix élevé. | Afficher les pertes résiduelles ; étudier séparément les mécanismes assurantiels ou de partage de risque. |

Une amélioration de couverture obtenue en augmentant le prix n'est pas à elle seule une preuve de valeur de l'IA. La comparaison utile porte sur le prix et les pertes résiduelles à protection observée comparable, avec les limites d'échantillon annoncées. Le modèle sélectionné dans une fenêtre ne doit pas être présenté comme le meilleur modèle agricole possible.
