# Contenu du deck

À reporter dans le template fourni par l'organisation. Une idée par slide, un chiffre fort par slide, la source en bas de chaque slide. Les captures viennent de l'application.

| # | Titre de la slide | Contenu | Visuel | Source en pied |
|---|---|---|---|---|
| 1 | Le Contrat qui Tient | Le prix plancher qui fait semer la lentille. Équipe, Track 3. | carte de l'Île-de-France en ocre et vert | — |
| 2 | La France importe 39 000 t de lentilles par an | Le rendement de la lentille varie deux fois plus que celui du blé. Une mauvaise année efface la marge. | courbe des rendements 2010–2025, 2016 et 2020 annotés | Eurostat Comext 2025 ; Agreste SAA |
| 3 | Une décision, une utilisatrice | La responsable filière d'une coopérative : à quel prix garantir la lentille pour qu'elle rapporte autant que le blé 8 années sur 10 ? | portrait type, sans photo | — |
| 4 | Aux prix d'hier, la lentille gagne une année sur deux | 5 années sur 10 à 715 €/t, la référence 2012–2016 ; 8 sur 10 à 1 567 €/t départ ferme en Seine-et-Marne, sur les tonnes acceptées au tri. | capture de l'étape « Le prix » | Modèle ; Eurostat 2012–2016 |
| 5 | Démo | Le verrou, le prix, l'épreuve, la preuve, le contrat. | démo en direct | — |
| 6 | Sous le capot | Météo NASA POWER → modèle d'apprentissage quantile calibré par conformal → 20 000 années rejouées avec le prix du blé → P\* = quantile 80 % du prix d'équilibre. | schéma en quatre blocs | NASA POWER ; Agreste ; Eurostat |
| 7 | La preuve | Prix calculé sur les moyennes : 29 % de contrats tenus. Notre modèle : 78 % pour 80 % promis, sur 133 cas jamais vus, en protocole strict. LightGBM, plus précis, n'en tient que 76 %. | frise du backtest et tableau des quatre façons de fixer le prix | Backtest 2019–2025 |
| 8 | Le bon contrat protège autant pour moins cher | 900 €/t (Unéal, 2023) : 6 années sur 10. 1 567 €/t sur toutes les tonnes : 8 sur 10. Tranches à 1 635 / 750 / 650 €/t : 8 sur 10 pour 18 % de moins ; en backtest, 79 % de contrats tenus (prix unique : 78 %) pour 19 % de moins. | tableau « Trois façons de garantir 8 années sur 10 » | Modèle ; Unéal ; NatUp (Union Agricole) |
| 9 | Un moteur, cinq légumineuses | Lentille : barème par tranches, 78 à 79 % de contrats tenus. Pour les quatre autres cultures, le backtest favorise le plancher indexé sur le blé : 78 à 89 %, contre 65 à 70 % à prix fixe. | tableau « Le même moteur, quatre autres légumineuses » | Backtest 2019–2025 ; Agreste ; data/cultures.yaml ; REVUE_FILIERE_CULTURES.md |
| 10 | Vu du ciel, un an avant le RPG | Avec les parcelles d'un carré de 4 km sur cinq, le satellite retrouve 73 % des légumineuses des autres carrés en fin de saison, 90 % de signalements justes. Appris sur 2024 seulement : 8 %. | capture de l'étape « Vu du ciel » | Copernicus Sentinel-2 ; RPG 2024 et 2025, IGN |
| 11 | Ce que nous ne savons pas encore | Prix incertain (1 099 à 2 877 €/t), rendements départementaux, 24 séries indépendantes seulement, contrats qui cèdent en 2020–2021, charges et rotation supposées. | liste courte | RESULTATS.md, LIMITES.md |
| 12 | Impact | Pilote : 300 t sur 210 ha. Ambition : 5 000 t sur 3 506 ha, 13 % des importations, 1 250 t de protéines, 631 t d'azote minéral non apporté, 2 647 t CO₂e évitées. | carte du contrat, compteurs | Modèle ; Comext ; GIEC ; DRIAAF |
| 13 | Qui paie | Coopératives et conditionneurs, par campagne. Étude pilote, puis abonnement par bassin ; ensuite toutes les cultures sous contrat et les assureurs. | trois étapes | — |
| 14 | Architecture | Pipeline Python, modèles précalculés ; Bedrock pour la lettre (aucun chiffre produit) ; Amplify déployé depuis GitHub ; démo hors ligne en fichier unique. | schéma | ARCHITECTURE.md |
| 15 | Merci | Lien vers le code et la démo. | — | — |

## Règles

- Pas de chiffre sans source en pied de slide.
- Les chiffres sont copiés depuis [RESULTATS.md](RESULTATS.md), jamais retapés de mémoire.
- Les limites ont leur slide : le jury récompense ce qui est prouvé.
