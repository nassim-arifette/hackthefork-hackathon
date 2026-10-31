# Questions : réponses de mentor et décisions proposées

Recherche documentaire du **31 octobre 2026**, pour avancer pendant Hack the Fork. Le rendu visuel reste celui validé le 30/10.

**Mon avis : garder la lentille, le Track 3 et le moteur de prix. Faire du résultat élevé une décision de filière : quel bassin, quelle rémunération et quel partage du risque permettent de mobiliser des hectares ?** Le hackathon doit montrer ces arbitrages avec des hypothèses explicites.

L'équipe a adopté ce scénario le 31/10 ; il est calculé dans la version 4 de [RESULTATS.md](RESULTATS.md). Les chiffres cités plus bas sont ceux de cette version, variantes de contrat comprises (§3, [RESULTATS.md §7](RESULTATS.md#7-comparer-les-contrats)). Cette revue documentaire ne vaut pas validation par l'organisation.

Les prix courants intègrent l'arrondi contractuel au plafond. Les taux de production utilisent désormais des groupes de légumineuses d'entraînement reconstruits sur le passé ; la cohorte test historique est conservée. Le benchmark multicultures de recherche utilise des règles et cohortes communes distinctes.

**Complément disponible :** un [barème public NatUp et un contrat synthétique complet](CONTRAT_SIMULATION.md), un [dossier de pilote 300 t avec partenaires ciblés](PILOTE_300T.md) et un [historique synthétique reproductible de 140 lots](../data/pilote_300t/README.md). Le comparateur fourni avec ce jeu permet de chiffrer les paiements et les coûts ; il ne recalcule pas le P* ni le backtest Agreste de l'application.

**Revue des autres cultures accomplie le 31/10 :** conserver **500 €/ha pour le pois chiche et 400 pour la féverole**, retenir **450 pour le pois et 1 000 pour le haricot sec irrigué**. Les guides Terres Inovia ont été ouverts ; les références de prix et le budget du haricot sont maintenant explicités. La [revue filière détaillée](REVUE_FILIERE_CULTURES.md) distingue le prix payé du pois chiche, le scénario haricot et le référentiel pois/féverole. Les hypothèses sont dans [data/cultures.yaml](../data/cultures.yaml) ; leurs effets chiffrés proviennent des exports recalculés, sans être déduits de cette seule revue.

## 0. Décisions de l'équipe, 31 octobre

| Sujet | Décision | État |
|---|---|---|
| Assistant de code | Claude Code est autorisé. | Déclaré dans [DECLARATIONS.md](DECLARATIONS.md), avec ChatGPT pour cette recherche. |
| Track | Track 3, déclaré. | — |
| Modèle | **Garder M1** pour la démo. Le banc d'essai des modèles probabilistes en cours sera comparé sur le même protocole avant tout changement. | — |
| Hypothèses | Scénario central de §2 adopté : charges 700 / 500 €/ha, aide 105 €/ha, rotation 150 €/ha, forfait de collecte 5 €/t brute. | Calculé : P\* de 1 568 €/t en Seine-et-Marne, 78,2 % de contrats tenus dans le backtest de production corrigé. |
| Tonnes payées | **Tonnes acceptées au tri**, 10 % de refus en scénario central, 0 et 20 % en sensibilité. Raisons ci-dessous. | Appliqué au modèle, au backtest, à la carte, au contrat et à l'impact. |
| Volumes | Pilote de 300 t, ambition de 5 000 t. | Bascule entre les deux à l'étape « Le contrat ». |
| Impact | Protéines, azote non apporté, émissions directes évitées. | Affichés pour le volume choisi (§6). |
| Repères de prix | « Référence historique 2012–2016 » remplace « prix du marché ». Unéal et NatUp affichés pour comparer. | Fait. |
| RPG / Agreste | Audit fait. | Résultat au §5. |
| Contrats | Comparer le prix unique, les barèmes publiés, la proposition du dossier pilote, des tranches calibrées et une prime à l'hectare, sur les mêmes scénarios et en backtest. | Fait : à protection égale, les tranches coûtent 18 % de moins que le prix unique (19 % en backtest, 79 % de contrats tenus contre 78 %). |
| Lettre Bedrock | Régénérer avec les chiffres de la version 4. | Commande dans [AWS.md](AWS.md). |
| Présentateur | Décidé plus tard. | — |

### Pourquoi payer les tonnes acceptées au tri

C'est la règle des contrats de collecte : le prix convenu s'applique à la marchandise conforme, après réfactions (humidité, impuretés) ; un lot hors normes est déclassé ou refusé et ne touche pas le prix garanti. Payer la récolte brute reviendrait à faire porter tout le risque qualité à l'acheteur, ce qu'aucun conditionneur n'accepte pour des lentilles destinées à l'alimentation humaine.

Agreste mesure le rendement « au stade arrivée ferme » (méthodologie SAA, p. 3), avant le tri de la coopérative. Le modèle applique donc la part refusée **une seule fois**, au rendement Agreste : 10 % en scénario central, cohérent avec les 10 à 20 % de pertes possibles liées à la bruche. Les lots refusés gardent une valeur (alimentation animale) que le modèle ne compte pas : c'est un choix prudent pour l'agriculteur.

Effet sur le prix plancher de la Seine-et-Marne : 1 411 €/t sans refus, **1 568 €/t avec 10 %**, 1 764 €/t avec 20 %. Le contrat doit l'écrire noir sur blanc : normes de réception, barème de réfaction, et prix de repli pour les lots déclassés.

## 1. Réponse à chaque question ouverte

| Question du document initial | Réponse de mentor | Action pour le hackathon |
|---|---|---|
| Assistant de code externe, dont Claude Code | Déclarer les outils effectivement utilisés, y compris ChatGPT pour cette recherche. Aucune règle publique trouvée ne permet de confirmer l'autorisation propre à cette édition. | Faire confirmer ce seul point de règlement par l'organisation et compléter [DECLARATIONS.md](DECLARATIONS.md). |
| Déclaration du Track 3 | **Garder Track 3** : le contrat, la collecte et l'approvisionnement français répondent au sujet filière retenu dans le repo. | Vérifier que la déclaration a été faite ; son statut n'est pas vérifiable dans les fichiers. |
| Culture cible | **Garder la lentille alimentaire conventionnelle**, avec entraînement national. Les références agronomiques et contractuelles existent. | Consacrer le temps disponible à la démonstration et aux contrats. |
| Site acheteur | **Garder le site fictif de Seine-et-Marne**, coordonnées longitude/latitude 2,95 / 48,55. | Le nommer « site de collecte du scénario ». Ajouter ensuite le déplacement sur la carte. |
| Charges blé / lentille | **700 / 500 €/ha** comme scénario central d'intrants, appuyé sur les références Terres Inovia ; conserver 440 / 280 comme scénario historique. | Actualiser les deux cultures ensemble et recalculer. Voir §2. |
| Bonus de rotation | **150 €/ha**, sensibilité 0 / 100 / 200. L'effet précédent de la lentille est documenté ; le montant reste un pari de scénario. | Compter le bénéfice de la culture suivante une seule fois. Voir §2. |
| Aide couplée | **Lentille alimentaire éligible ; 105 €/ha indicatifs pour 2026.** Les 122 €/ha sont le montant de la campagne 2025. [S1] [S2] | Corriger le millésime et le statut du montant, puis recalculer. |
| Transport | **Conserver 0,12 €/t/km** et proposer **5 €/t de forfait de collecte** pour un lot agrégé de référence de 25 t. | Paramètres supposés, avec sensibilités ; distinguer collecte et tri. Voir §4. |
| Volume coopérative | **300 t nettes alimentaires pour le pilote, 5 000 t pour l'ambition de bassin.** | Afficher l'assiette des tonnes et les surfaces nécessaires. Le pilote synthétique est dimensionné à 220 ha ; voir §4. |
| P* autour de 1 600 €/t | Le résultat justifie de **comparer plusieurs contrats** et plusieurs bassins. Les exemples contractuels récents sont sensiblement plus bas. | Montrer la frontière prix/protection, puis une rémunération à paliers ou avec prime par hectare. Voir §3. |
| RPG 1 095 ha / Agreste environ 730 ha | **RPG pour les surfaces localisées ; Agreste pour les séries de rendement.** Les périmètres statistiques diffèrent. | Audit ciblé de l'écart ; aucune mise à l'échelle artificielle de la carte. Voir §5. |
| Lettre Bedrock | **Génération au build, mise en cache**, à partir des seules sorties calculées. | Essai d'invocation sur le compte de l'équipe, puis export. « 8 sur 10 » décrit la comparaison de marges. |
| Langue du pitch | **Français**, avec les termes techniques traduits à l'oral. | Garder une seule version à répéter. |
| Présentateur | **Une personne au récit et aux arbitrages, une personne à la démo et aux questions techniques.** | Choisir les noms dans l'équipe lors d'une répétition de quatre minutes. |

## 2. Hypothèses économiques et agronomiques à adopter

### Charges : 700 €/ha pour le blé, 500 €/ha pour la lentille

Le guide lentille Terres Inovia 2023 chiffre un itinéraire conventionnel à **518 €/ha de charges opérationnelles**. La projection Cerfrance Nord-Est Île-de-France publiée dans le guide pois 2025 conduit, par calcul, à **675 €/ha** pour un blé après colza : 8,5 t/ha × 200 €/t − 1 025 €/ha de marge brute. [S3] [S4]

**Je propose donc les arrondis 700 et 500 €/ha**, étiquetés « supposé, ancré sur références techniques ». Ce sont des repères cohérents pour comparer les intrants ; ils ne représentent pas le coût complet de chaque exploitation.

| Paramètre | Central proposé | Variantes de sensibilité |
|---|---:|---|
| Charges opérationnelles blé | 700 €/ha | 600 / 700 / 800 |
| Charges opérationnelles lentille | 500 €/ha | 400 / 500 / 600 |
| Aide lentille, campagne 2026 | 105 €/ha, indicatif | 0 / 105 / 122 |
| Bénéfice de rotation | 150 €/ha | 0 / 100 / 150 / 200 |
| Couple de charges historique | 440 / 280 €/ha | conserver pour reproduire la version 3 |

Le différentiel de charges compte dans le prix d'équilibre. Relever uniquement le coût de la lentille tout en conservant le blé de 2020 déformerait cette comparaison. Si l'on ajoute récolte ou mécanisation, comparer les deux cultures au même périmètre. Affecter tri, stockage et conditionnement à l'acteur qui les paie.

### Rotation : intégrer 150 €/ha dès le scénario central

L'étude FiloLeg / Agro-Transfert publiée en 2024 utilise un effet précédent propre à la lentille de **+7 q/ha de blé et −55 kg N/ha**. Ce sont des hypothèses de simulation publiées. Terres Inovia mentionne par ailleurs une restitution pouvant atteindre 30 unités d'azote à la culture suivante. [S5] [S6]

Mon scénario de 150 €/ha se construit ainsi :

~~~text
Gain de rendement du blé suivant : 0,6 t/ha × 200 €/t = 120 €/ha
Économie d'azote sur ce blé :       25 kg N/ha × 1,2 €/kg = 30 €/ha
Bénéfice de rotation retenu :                               150 €/ha
~~~

Ces coefficients sont un **choix d'équipe argumenté**, à faire varier. Le bénéfice arrive sur la culture suivante : le tableau doit distinguer marge de la campagne et marge avec bénéfice de rotation. L'absence d'engrais azoté sur la lentille est déjà comprise dans ses charges.

**Sélection des parcelles :** cibler des sols drainants et tenir compte d'un retour d'au moins cinq ans, ainsi que des autres légumineuses sensibles à Aphanomyces. La carte de blé fournit des candidates économiques ; l'historique de rotation affine leur aptitude. [S7]

### Aide : réponse tranchée sur l'éligibilité, millésime explicite

La notice Telepac 2026, p. 4, inclut les lentilles récoltées en graines après le stade de maturité laiteuse, dont celles destinées à l'alimentation humaine. Le montant annoncé est **105 €/ha à titre indicatif**, ajustable selon les surfaces éligibles. L'arrêté du 24 février 2026 fixe **122 €/ha pour 2025**. [S1] [S2]

Pour une projection des prochains semis en 2027, présenter 105 comme une **reconduction supposée du repère 2026**. L'application actuelle est étiquetée campagne 2026 : conserver ce cadre dans le replay ou changer explicitement le millésime lors du prochain export.

### Conséquence calculable sur P*

Avec les nouveaux paramètres, le terme du prix d'équilibre indépendant des rendements passe de −282 à −455 €/ha :

~~~text
Actuel :   −440 + 280 − 122 −   0 = −282 €/ha
Proposé :  −700 + 500 − 105 − 150 = −455 €/ha

R_nouveau,s = R_actuel,s − 173 / y_lentille,s
~~~

Avec y en t/ha, la baisse vaut 231 €/t pour un scénario à 0,75 t/ha et 115 €/t à 1,5 t/ha. **Recalcul fait** : 1 411 €/t avec ces seuls paramètres, puis 1 568 €/t une fois les 10 % de refus au tri appliqués (scénario retenu, §0).

## 3. Un P* élevé : quelle proposition commerciale ?

### Les repères à utiliser

| Source et date | Observation | Usage dans la démo |
|---|---|---|
| Eurostat 2012–2016, déjà exploité dans le repo | 650–779 €/t | Renommer « référence historique 2012–2016 ». |
| Unéal, décembre 2023 | Lentilles du partenariat avec Vivien Paille valorisées à 900 €/t. [S8] | Exemple de filière industrielle. |
| AFP, 23 février 2026, témoignage d'une productrice Unéal | 900 €/t en 2024, 800 en 2025, 650 annoncés pour 2026. [S9] | Exemple récent daté, avec son contexte. |
| NatUp, entretien de septembre 2023 sur les récoltes 2023–2024 | Trois tranches annoncées : 900 €/t jusqu'à 1 t/ha, 700 de 1 à 2, 600 au-delà avec un éventuel complément de marché. [S19] | Barème réel reconstitué ; clauses non publiées conservées comme inconnues. |
| NatUp, 18 septembre 2025 | Contrat triennal conventionnel rémunérant la première tonne par hectare 1 000 €. [S10] | Précédent concret pour une rémunération à paliers. |

**Ma réponse au jury :** le prix de 1 568 €/t chiffre le coût d'une protection forte face au blé francilien dans le modèle actuel. L'outil doit permettre de négocier cette protection, de modifier la rémunération et de choisir les hectares les plus intéressants. Dans le même modèle, 900 €/t protège 6,1 années sur 10 et 1 000 €/t, 6,5.

Les contrats existants intègrent déjà le risque. Notre valeur ajoutée est de **comparer leurs barèmes, mesurer leur protection et cibler les parcelles**. Le score de 29 % dans le repo est celui de la baseline calculée sur les moyennes ; il ne mesure pas la performance de l'ensemble des contrats des coopératives.

### Trois formes de contrat à comparer

| Forme | Proposition de démonstration | Mesure à afficher |
|---|---|---|
| Prix uniforme | Garder P* et le curseur de fiabilité. | Prix, fréquence de marges gagnantes et tonnes potentielles. |
| Indexation blé | Utiliser le multiplicateur déjà exporté, puis le recalculer avec les nouvelles hypothèses. | Coût acheteur selon plusieurs prix du blé. |
| Partage du risque | Tester un palier sur la première tonne, puis une variante prix + prime par hectare. | Coût moyen, protection, perte des mauvaises années. |

**Contrat à paliers, prototype directement compréhensible :**

~~~text
recette_bareme(y) = 1 000 × min(y, 1)
                  + 750 × min(max(y − 1, 0), 1)
                  + 650 × max(y − 2, 0)
~~~

y est le rendement net alimentaire payé en t/ha, agrégé par producteur et campagne avant d'appliquer les tranches. Ce **contrat synthétique 2027** retient 1 000 / 750 / 650 €/t, plus 30 €/t net de prime de pré-nettoyage lorsque le service a été effectué. Le premier palier s'inspire du communiqué NatUp de 2025 ; les deux suivants et le montant de la prime sont nos choix. Le barème public distinct de 2023–2024, 900 / 700 / 600, est aussi disponible. [S10] [S19]

Les clauses de qualité, la prise en charge du tri, les exemples et les limites de la reconstitution figurent dans [CONTRAT_SIMULATION.md](CONTRAT_SIMULATION.md). Les trois barèmes sont paramétrés dans [contrats.json](../data/pilote_300t/contrats.json) et comparés sur le même historique synthétique. **Protection calculée par le moteur** (Seine-et-Marne, face au blé) : 5,9 années sur 10 pour le barème NatUp 2023–2024, 6,4 pour la proposition 2027, 6,1 pour le prix uniforme de 900 €/t. Pour atteindre 8 sur 10 en gardant 750 et 650 €/t, la première tonne doit être payée 1 635 €/t : le coût moyen tombe alors à 1 283 €/t, contre 1 568 €/t pour le prix unique.

**Pari commercial complémentaire : prix de base de 900 €/t + prime fixe par hectare.** Cette prime rémunère l'engagement dans la filière et soutient aussi les scénarios de faible rendement. Sa valeur peut se calculer dans le moteur :

~~~text
a* = max(0, quantile_80%(
       prix_blé × y_blé − charges_blé + charges_lentille
       − aide − bonus_rotation − 900 × y_lentille
     ))
~~~

**Calculé :** a\* = 491 €/ha pour 8 années sur 10, soit un coût moyen de 1 243 €/t. C'est la forme la moins chère et celle qui réduit le plus la perte des années perdantes, mais l'acheteur paie la prime même sans récolte, et elle a mal résisté à la flambée du blé de 2022 : 79 % de contrats tenus en backtest, sous la cible. Reste à afficher séparément la protection avec bonus de rotation et celle de la trésorerie de campagne.

L'indexation retire une partie du décalage avec le prix du blé en transférant ce risque vers l'acheteur. Elle conserve le risque de rendement et le risque de base entre l'indice et le prix réellement payé. Avec le multiplicateur actuel de 7,44, un blé à 200 €/t donne 1 488 €/t de lentille ; **l'indexation seule ne rend donc pas le contrat beaucoup moins cher**. Les valeurs 3,44 et 7,44 sont celles de l'export de la version 4, respectivement médiane et cible 80 %.

### Où chercher la viabilité ?

Je ciblerais **un industriel ou une marque qui valorise une origine française traçable**, avec un collecteur partenaire, un besoin de volume défini et un contrat sur plusieurs campagnes. Montrer ensuite le coût matière à l'échelle d'un produit : entre 900 et 1 568 €/t, l'écart est de **3,3 centimes pour 50 g de lentilles sèches**, avant tri, transformation, distribution et taxes. C'est un argument d'achat à tester.

Ajouter au calcul acheteur le tri, le stockage, les pertes de qualité et le conditionnement. Pour la qualité alimentaire, tester une sensibilité **0 / 10 / 20 % de volume non valorisé**, en vérifiant ce que le rendement de départ contient déjà. La bruche et les refus qualité sont réels ; un taux unique de perte doit rester une hypothèse du scénario. [S3] *Fait : paiement sur les tonnes acceptées, 10 % en central (§0) ; le rendement Agreste est mesuré avant tri.*

Pour le modèle économique de l'outil, je proposerais une **étude pilote payante à 3 000 €**, puis un **abonnement à 10 000 € par campagne et par bassin**. Ce sont des prix à tester, choisis pour obtenir une première vente et mesurer la valeur. À titre de calcul, une décision améliorant de 20 €/t un programme de 5 000 t représente 100 000 € ; il faudra démontrer le gain chez le client.

## 4. Collecte, volumes et surfaces à mobiliser

### Un pilote à 300 t nettes alimentaires, une ambition à 5 000 t

À 1,43 t/ha acceptées au tri (1,59 t/ha récoltées, rendement moyen simulé en Seine-et-Marne), **300 t correspondent théoriquement à 210 ha**. Le scénario spatial de l'application prend toutefois des parcelles entières : au site initial et à 1 600 €/t rendu, il retient 28 parcelles, 216,42 ha et 309,7 t acceptées attendues. Pour le programme indépendant, retenir **220 ha, par exemple 20 fermes × 11 ha**, soit 314,82 t alimentaires attendues avant refus additionnels. Ces paramètres sont des hypothèses.

**Assiette vérifiée :** la méthodologie de la SAA définit le rendement comme « un rendement en récolte, c'est-à-dire au stade arrivée ferme » (p. 3), donc avant la réception et le tri de la coopérative. Retirer 10 % au rendement Agreste ne compte pas la perte deux fois. La SAA parle aussi d'une production « récoltée et commercialisable » : une partie des impuretés peut déjà en être exclue, d'où la sensibilité 0 / 10 / 20 %. [S12]

NatUp a publié une collecte de 558 t en 2025. [S10] **NatUp/Lunor est le premier candidat proposé**, pour commencer par une comparaison sur un sous-ensemble de collecte existante. Les contacts, les alternatives et le message préparé figurent dans [PILOTE_300T.md](PILOTE_300T.md). Aucun partenaire n'a encore accepté le pilote. L'historique synthétique laisse volontairement apparaître les années où 220 ha ne suffisent pas à livrer 300 t nettes.

Conserver le scénario de 5 000 t pour montrer l'ambition de bassin. Au site initial et à 1 600 €/t rendu, la sélection de 260 parcelles entières représente 3 501,83 ha et 5 011,6 t acceptées attendues. Le ratio cible 5 000 / 39 371 vaut 12,7 % : afficher **« volume équivalent à 13 % des importations 2025 »**. Le remplacement effectif d'importations dépendra des débouchés.

Séparer les tonnes économiquement candidates, les tonnes d'un scénario de mobilisation et les engagements signés. Pour tester la prospection, prendre **10 % de mobilisation**, sensibilité 5 / 10 / 20 %, explicitement supposés. Appliquer cette proportion aux surfaces candidates après les filtres disponibles, puis recalculer les hectares et distances nécessaires pour atteindre la cible.

### Un transport simple, avec un forfait

Je conserve 0,12 €/t/km. Le CNR distingue les coûts liés aux kilomètres, au temps et à l'immobilisation : cela justifie un forfait pour l'enlèvement, sans transformer ce coefficient en tarif officiel. [S11]

~~~text
distance_route = 1,3 × distance_vol_oiseau
collecte_€/t_reçue = 5 + 0,12 × distance_route
coût_collecte_total = collecte_€/t_reçue × tonnes_reçues
prix_rendu_€/t_nette = prix_producteur_€/t_nette
                      + coût_collecte_total / tonnes_acceptées
~~~

Les hypothèses sont : lot agrégé de 25 t reçues ; forfait 5 €/t reçue, soit 125 € par lot ; sensibilité du forfait 0 / 5 / 10 et du coefficient 0,06 / 0,12 / 0,20. La distance est l'aller simple ; le coefficient global retenu représente l'organisation du scénario, retours compris. Pour de petits lots, utiliser ensuite un forfait d'enlèvement divisé par leur tonnage. Le prix rendu ci-dessus comprend achat et collecte ; ajouter tri et séchage pour le budget du contrat. Si aucune tonne n'est acceptée, le coût total reste dû et son expression par tonne alimentaire est non définie.

100 km routiers supplémentaires ajoutent 12 €/t reçue, soit 12 × tonnes reçues / tonnes acceptées par tonne alimentaire. **L'extension cartographique aide à organiser la collecte ; les principaux leviers du prix restent le bassin, la rotation et le contrat.** L'optimum affiché doit être le meilleur parmi les emplacements candidats, selon les hypothèses testées.

## 5. Pourquoi RPG et Agreste divergent-ils ?

Les quatre surfaces Agreste du repo donnent précisément **727 ha** : 226 + 245 + 207 + 49. Face aux 1 095 ha RPG, l'écart est donc de 368 ha.

La méthodologie SAA rattache les terres au **département du siège de l'exploitation**. Le RPG permet de compter les parcelles à leur localisation et couvre les déclarants PAC. En outre, les valeurs SAA franciliennes du repo sont de statut 3 et l'année 2025 est provisoire. Ces différences rendent l'écart possible ; leur contribution exacte n'est pas encore mesurée. [S12] [S13]

**Décision : garder les usages distincts des deux sources.**

### Audit fait le 31/10

1. **Millésime** : RPG version 4.0 au 1er janvier 2025 pour la région 11, soit les déclarations de la campagne 2025 ; SAA 2025 provisoire. Même campagne.
2. **Parcelles** : 178 parcelles LEC, 178 identifiants uniques, **1 095,1 ha de surface déclarée** (`surf_parc`, pas une aire recalculée). 16 parcelles de moins d'1 ha (9,4 ha) et 2 parcelles hors des quatre départements après simplification ne sont pas sur la carte : 160 y figurent. Le filtre n'explique donc pas l'écart.
3. **Par département**, à la localisation de la parcelle pour le RPG, au siège de l'exploitation pour la SAA :

| Département | RPG 2025 | SAA 2025 | Écart |
|---|---:|---:|---:|
| Seine-et-Marne | 481,9 ha | 226 ha | +256 ha |
| Yvelines | 299,6 ha | 245 ha | +55 ha |
| Essonne | 280,9 ha | 207 ha | +74 ha |
| Val-d'Oise | 23,0 ha | 49 ha | −26 ha |
| Hors des quatre départements | 9,7 ha | — | — |
| **Total** | **1 095,1 ha** | **727 ha** | **+368 ha** |

**Lecture** : 70 % de l'écart vient de la Seine-et-Marne, qui touche l'Aube, la Marne, l'Yonne et le Loiret, de gros producteurs de lentilles. Des exploitations dont le siège est dans ces départements et qui cultivent des parcelles en Seine-et-Marne sont comptées chez elles par la SAA, mais en Seine-et-Marne par le RPG. C'est l'explication la plus probable, compatible avec le statut 3 et le caractère provisoire des chiffres SAA ; elle n'est pas démontrée.

La SAA inclut les types variétaux de lentille et compte une surface non récoltée avec rendement nul : ces deux éléments ne justifient pas à eux seuls l'écart. [S12]

**Question précise pour le SRISE** : quelle part des surfaces en lentille localisées en Seine-et-Marne relève d'exploitations dont le siège est hors d'Île-de-France ?

**Conséquence pour l'outil** : aucune. La carte utilise le RPG (où sont les parcelles), le modèle utilise les rendements SAA (combien elles produisent). Aucune surface n'est mise à l'échelle.

## 6. Impact : trois compteurs prêts à spécifier

### Paramètres et formules

| Indicateur | Paramètre proposé | Calcul |
|---|---|---|
| Protéines potentielles | 25 % de la masse de graines alimentaires | tonnes alimentaires × 0,25 |
| Azote minéral non apporté | 180 kg N/ha de blé remplacé ; 0 sur lentille | nouveaux hectares × 180 / 1 000, en t N |
| Émissions directes associées | EF1 = 0,010 ; PRG100 N₂O = 267 | nouveaux hectares × 180 × 0,010 × 44/28 × 267 / 1 000, en t CO₂e |

**Protéines.** La fiche qualité Terres Inovia / Terres Univia, récolte 2024, donne 28,4 % de protéines sur matière sèche et 12,6 % d'eau en moyenne. La conversion indicative 0,284 × (1 − 0,126) donne 24,8 %. **Retenir 25 % comme coefficient arrondi** permet d'avancer malgré l'indisponibilité de Ciqual. Appliquer ce taux aux tonnes alimentaires après tri, ou préciser « avant pertes de tri » si le modèle n'en dispose pas. [S14]

**Azote.** Le Mémento Île-de-France 2025, publié en janvier 2026, situe les apports du blé tendre autour de 175–180 kg N/ha dans l'enquête 2021, hors parcelles recevant de l'azote organique. **180 est notre scénario arrondi**, à faire varier entre 150 et 210. Les hectares déjà en lentille ne comptent pas comme nouvelle économie. [S15] [S3]

**Climat.** Le facteur agrégé du GIEC 2019 et le PRG100 corrigé dans l'errata AR6 du 7 octobre 2025 conduisent à **0,755 t CO₂e/ha**. L'indicateur porte sur les émissions directes liées aux apports d'azote minéral évités. Il exclut fabrication des engrais, émissions indirectes, résidus, autres opérations et déplacement de production : le bilan climatique net de la filière demande un calcul plus large. [S16] [S17]

**Exemple de scénario pour la démo :** 100 nouveaux hectares à 1,6 t/ha, avant pertes de tri, donnent **160 t de lentilles, 40 t de protéines potentielles, 18 t d'azote minéral non apporté et environ 76 t CO₂e d'émissions directes associées**. Afficher « scénario » et donner le périmètre en une infobulle suffit.

*Fait, sur les parcelles entières sélectionnées au site initial à 1 600 €/t rendu : la cible pilote donne 309,7 t attendues sur 216,42 ha, soit 77 t de protéines, 39 t d'azote non apporté et 163 t CO₂e directes évitées ; l'ambition donne 5 011,6 t sur 3 501,83 ha, soit 1 253 t de protéines, 630 t N et 2 644 t CO₂e. Ces potentiels ne sont pas des volumes engagés.*

## 7. Mon arbitrage sur la roadmap et le pitch

**Pendant le hackathon :** mettre à jour les hypothèses, comparer les contrats, ajouter les compteurs d'impact, puis rendre le site déplaçable. Ensuite, prototyper Sentinel sur 5 à 10 parcelles en replay d'une saison achevée. Le détail et les critères de sortie sont dans [ROADMAP.md](ROADMAP.md).

Je conserverais M1 pour la démo : les résultats existants permettent déjà de montrer la différence entre prévision moyenne et décision sous risque. Toute nouvelle méthode sera une version distincte, comparée sur le même protocole. Avec les hypothèses de la version 4.1 et les groupes d’entraînement corrigés, le modèle tient 78,2 % des contrats sur sept années ; les nouveaux barèmes de contrat doivent être évalués à leur tour.

La question « sans IA, que perd-on ? » doit montrer la comparaison **M0 / M1 / M2** déjà présente dans le repo. La valeur démontrée vient de la distribution et de sa calibration ; la météo peut modifier le coût de la protection, même lorsqu'elle améliore peu la précision moyenne. Éviter d'assimiler tous les calculs sans IA à une simple moyenne.

Pour Bedrock, un modèle visible dans le catalogue doit encore être effectivement invocable avec les permissions du compte. Faire un essai court, enregistrer la lettre, et garder le rendu hors ligne prévu. [S18]

### Les trois éléments demandés : disponibles pour avancer

| Besoin | Livrable disponible | Prochaine donnée terrain utile |
|---|---|---|
| Contrat réel à simuler | [Barème NatUp 2023–2024 reconstitué et contrat synthétique 2027 complet](CONTRAT_SIMULATION.md), prix, paliers, prime, qualité, tri et durée. | Un contrat ou décompte réel pour remplacer les clauses inconnues, notamment l'assiette payée et les retenues. |
| Partenaire pour 300 t | [NatUp/Lunor prioritaire, trois alternatives et proposition de pilote](PILOTE_300T.md), avec contacts publics. | Accord d'un responsable filière sur un périmètre de données et de collecte. |
| Petit historique coopératif | [140 lots fictifs sur 2019–2025](../data/pilote_300t/README.md), récolte brute/nette, prix, charges et refus, avec générateur et références publiques séparées. | 20 à 50 lots réels et anonymisés avec leur décompte et les règles qualité. |

La démonstration peut démarrer avec ces fichiers. Les lots portent le statut **synthétique** et servent à exercer les calculs ; ils ne sont pas ajoutés aux observations Agreste ni utilisés comme preuve de la protection « huit années sur dix ».

Le pari à défendre est clair : **un responsable filière peut choisir un contrat et des hectares avec une meilleure lecture du risque, puis faire grandir une filière de lentilles françaises.**

## Sources consultées le 31 octobre 2026

| Réf. | Document | Élément utilisé |
|---|---|---|
| [S1] | Telepac, notice aides couplées 2026, p. 4/26 | Éligibilité et montant indicatif. |
| [S2] | Arrêté du 24 février 2026, art. 1 | Montant définitif de la campagne 2025. |
| [S3] | Terres Inovia, guide lentille 2023, pages imprimées 1, 6 et 10 | Charges, fertilisation, qualité. |
| [S4] | Terres Inovia, guide pois 2025, p. 3 | Projection Cerfrance et coût du blé déduit par calcul. |
| [S5] | FiloLeg / Agro-Transfert, synthèse technico-économique, 2024, p. 1 | Hypothèses d'effet précédent de la lentille. |
| [S6] | Terres Inovia, Les atouts de la lentille | Bénéfice de rotation et azote sur le suivant. |
| [S7] | Terres Inovia, Comment assurer la bonne implantation de la lentille ? | Sols et délai de retour. |
| [S8] | Unéal, Unéal recherche 100 ha de lentilles, décembre 2023 | Débouché et prix contractuel. |
| [S9] | AFP / Agri Mutuel, 23 février 2026 | Témoignage daté sur les prix 2024–2026. |
| [S10] | NatUp, communiqué du 18 septembre 2025 | Première tonne, contrat triennal et collecte. |
| [S11] | CNR, enquête longue distance 2013, §7.1 | Structure de coût uniquement ; tarifs anciens non repris. |
| [S12] | Agreste, méthodologie SAA, p. 3–5 et 10 | Qualité, rattachement géographique et champ. |
| [S13] | IGN, présentation du RPG sur data.gouv.fr | Déclarations PAC, localisation, millésimes. |
| [S14] | Terres Inovia / Terres Univia, qualité des graines, récolte 2024 | Protéines et humidité. |
| [S15] | DRIAAF, Mémento Île-de-France 2025, janvier 2026, p. 26 | Apports minéraux du blé, enquête 2021. |
| [S16] | GIEC, raffinement 2019, vol. 4, chap. 11, tableau 11.1 | Facteur direct N₂O-N agrégé. |
| [S17] | GIEC AR6 WGI, errata du 7 octobre 2025, tableau 7.15 corrigé | PRG100 N₂O. |
| [S18] | AWS, Request access to models | Disponibilité et permissions Bedrock. |
| [S19] | Union Agricole, entretien NatUp, 18 septembre 2023 | Barème par tranches annoncé pour 2023 et reconduit en 2024. |

[S1]: https://www.telepac.agriculture.gouv.fr/telepac/pdf/tas/2026/Dossier-PAC-2026_notice_aides-couplees.pdf
[S2]: https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000053594055
[S3]: https://www.terresinovia.fr/sites/default/files/2025-06/guide-de-culture-lentille-2023.pdf
[S4]: https://www.terresinovia.fr/sites/default/files/2025-05/guide-de-culture-pois-conventionnel-2025.pdf
[S5]: https://filoleg.fr/wp-content/uploads/2024/12/Synthese-technico-economique-insertion-LAG.pdf
[S6]: https://www.terresinovia.fr/fr/informations-techniques/lentille/les-atouts-de-la-lentille
[S7]: https://www.terresinovia.fr/fr/actualites/comment-assurer-la-bonne-implantation-de-la-lentille-1
[S8]: https://uneal.com/cms_filiere-lentille-uneal
[S9]: https://www.agri-mutuel.com/cultures/poussee-par-le-climat-la-lentille-se-cherche-une-vocation-dans-le-nord/
[S10]: https://natup.coop/download/5775/
[S11]: https://www.cnr.fr/download/file/publications/ENQU%C3%8ATE%20LONGUE%20DISTANCE%202013.pdf
[S12]: https://agreste.agriculture.gouv.fr/agreste-web/download/methode/S-SAA/Methodologie_Statistique-Agricole-Annuelle.pdf
[S13]: https://www.data.gouv.fr/datasets/rpg
[S14]: https://www.terresinovia.fr/documents/20126/162983/fiche_Terres_Inovia_Terres_Univia_qual_graines_lentille-2024.pdf/35e91999-3cd8-a885-7ce7-2bf4de1c9e4c?t=1743435326312
[S15]: https://driaaf.ile-de-france.agriculture.gouv.fr/IMG/pdf/memento_agricole_idf_2025_v2.pdf
[S16]: https://www.ipcc-nggip.iges.or.jp/public/2019rf/pdf/4_Volume4/19R_V4_Ch11_Soils_N2O_CO2.pdf
[S17]: https://www.ipcc.ch/report/ar6/wg1/downloads/report/IPCC_AR6_WGI_Errata.pdf
[S18]: https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html
[S19]: https://www.union-agricole.fr/natup-souhaite-augmenter-les-surfaces-de-lentilles
