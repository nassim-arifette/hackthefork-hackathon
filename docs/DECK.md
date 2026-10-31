# Contenu du deck

À reporter dans le template fourni par l'organisation. Une idée par slide, un chiffre fort par slide, la source en bas de chaque slide. Les captures viennent de l'application.

Les scores historiques ci-dessous utilisent l'entraînement glissant du moteur de l'application, avec regroupements Agreste établis sur 2010–2025. Cette limite doit figurer avec le score ; le benchmark multicultures strict est présenté séparément.

| # | Titre de la slide | Contenu | Visuel | Source en pied |
|---|---|---|---|---|
| 1 | Le Contrat qui Tient | Le prix plancher qui fait semer la lentille. Équipe, Track 3. | carte de l'Île-de-France en ocre et vert | — |
| 2 | La France importe 39 000 t de lentilles par an | Le rendement de la lentille varie deux fois plus que celui du blé. Une mauvaise année efface la marge. | courbe des rendements 2010–2025, 2016 et 2020 annotés | Eurostat Comext 2025 ; Agreste SAA |
| 3 | Une décision, une utilisatrice | La responsable filière d'une coopérative : à quel prix garantir la lentille pour qu'elle rapporte autant que le blé 8 années sur 10 ? | portrait type, sans photo | — |
| 4 | Aux prix d'hier, la lentille gagne une année sur deux | 5 années sur 10 à 715 €/t, la référence 2012–2016 ; 8 sur 10 à 1 568 €/t départ ferme en Seine-et-Marne, sur les tonnes acceptées au tri. | capture de l'étape « Le prix » | Modèle ; Eurostat 2012–2016 |
| 5 | Démo | Le verrou, le prix, l'épreuve, la preuve, le contrat. | démo en direct | — |
| 6 | Sous le capot | Météo NASA POWER → modèle d'apprentissage quantile calibré par conformal → 20 000 années rejouées avec le prix du blé → P\* = quantile 80 % du prix d'équilibre. | schéma en quatre blocs | NASA POWER ; Agreste ; Eurostat |
| 7 | L'évaluation historique | Prix calculé sur les moyennes : 29,3 % de contrats tenus. M1 : 87,2 % pour 80 % visés sur 133 cas ; M0 : 81,2 %, LightGBM : 76,7 %. Entraînement glissant, mais regroupements de séries sur période complète. | frise du backtest et tableau des quatre façons de fixer le prix | Backtest historique 2019–2025 |
| 8 | Le bon contrat protège autant pour moins cher | 900 €/t (Unéal, 2023) : 6 années sur 10. 1 568 €/t sur toutes les tonnes : 8 sur 10. Tranches à 1 635 / 750 / 650 €/t : 8 sur 10 pour 18 % de moins, et 87 % de contrats tenus en backtest pour 22 % de moins. | tableau « Trois façons de garantir 8 années sur 10 » | Modèle ; Unéal ; NatUp (Union Agricole) |
| 9 | Un moteur, cinq légumineuses | Lentille : 87,2 % des cas historiques tenus en prix fixe. Avec les budgets PR3 revus pour haricot et pois, les quatre autres cultures tiennent 65,5–71,8 % en fixe et 82,3–87,3 % en indexé. L'indexation transfère le risque de prix du blé vers l'acheteur ; les nouveaux budgets changent aussi les prix calibrés. | tableau « Le même moteur, quatre autres légumineuses » | Backtest historique 2019–2025 ; Agreste ; data/cultures.yaml ; REVUE_FILIERE_CULTURES.md |
| 10 | Ce que nous ne savons pas encore | Prix incertain (1 099 à 2 877 €/t), rendements départementaux, 24 séries indépendantes seulement, contrats qui cèdent en 2020–2021, charges et rotation supposées. | liste courte | RESULTATS.md, LIMITES.md |
| 11 | Potentiel au site initial | À 1 600 €/t rendu : cible pilote 300 t, sélection de 309,7 t attendues sur 216,42 ha. Ambition : 5 011,6 t sur 3 501,83 ha, environ 13 % des importations, 1 253 t de protéines, 630 t d'azote minéral non apporté, 2 644 t CO₂e directes évitées. Disponibilité et capacité non vérifiées. | carte de la sélection, compteurs | Scénario spatial ; Comext ; GIEC ; DRIAAF |
| 12 | Qui paie | Coopératives et conditionneurs, par campagne. Étude pilote, puis abonnement par bassin ; ensuite toutes les cultures sous contrat et les assureurs. | trois étapes | — |
| 13 | Architecture | Pipeline Python, modèles précalculés ; Bedrock pour la lettre (aucun chiffre produit) ; Amplify déployé depuis GitHub ; démo hors ligne en fichier unique. | schéma | ARCHITECTURE.md |
| 14 | Merci | Lien vers le code et la démo. | — | — |

## Règles

- Pas de chiffre sans source en pied de slide.
- Les chiffres sont copiés depuis [RESULTATS.md](RESULTATS.md), jamais retapés de mémoire.
- Les limites ont leur slide : le jury récompense ce qui est prouvé.
