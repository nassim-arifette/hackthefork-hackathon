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
| 7 | La preuve | Prix calculé sur les moyennes : 29 % de contrats tenus. Notre modèle : 87 % pour 80 % promis, sur 133 cas jamais vus. LightGBM, plus précis, n'en tient que 77 %. | frise du backtest et tableau des quatre façons de fixer le prix | Backtest 2019–2025 |
| 8 | Ce que coûte la sécurité | 900 €/t (Unéal, 2023) : 6 années sur 10. 1 567 €/t : 8 sur 10. 2 632 €/t : 9 sur 10. Le responsable filière choisit son compromis en connaissant son prix. | courbe « le prix de la sécurité » | Modèle ; communiqués Unéal et NatUp |
| 9 | Ce que nous ne savons pas encore | Prix incertain (1 099 à 2 877 €/t), rendements départementaux, 24 séries indépendantes seulement, contrats qui cèdent en 2020–2021, charges et rotation supposées. | liste courte | RESULTATS.md, LIMITES.md |
| 10 | Impact | Pilote : 300 t sur 210 ha. Ambition : 5 000 t sur 3 506 ha, 13 % des importations, 1 250 t de protéines, 631 t d'azote minéral non apporté, 2 647 t CO₂e évitées. | carte du contrat, compteurs | Modèle ; Comext ; GIEC ; DRIAAF |
| 11 | Qui paie | Coopératives et conditionneurs, par campagne. Étude pilote, puis abonnement par bassin ; ensuite toutes les cultures sous contrat et les assureurs. | trois étapes | — |
| 12 | Architecture | Pipeline Python, modèles précalculés ; Bedrock pour la lettre (aucun chiffre produit) ; Amplify déployé depuis GitHub ; démo hors ligne en fichier unique. | schéma | ARCHITECTURE.md |
| 13 | Merci | Lien vers le code et la démo. | — | — |

## Règles

- Pas de chiffre sans source en pied de slide.
- Les chiffres sont copiés depuis [RESULTATS.md](RESULTATS.md), jamais retapés de mémoire.
- Les limites ont leur slide : le jury récompense ce qui est prouvé.
