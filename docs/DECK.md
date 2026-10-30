# Contenu du deck

À reporter dans le template fourni par l'organisation. Une idée par slide, un chiffre fort par slide, la source en bas de chaque slide. Les captures viennent de l'application.

| # | Titre de la slide | Contenu | Visuel | Source en pied |
|---|---|---|---|---|
| 1 | Le Contrat qui Tient | Le prix plancher qui fait semer la lentille. Équipe, Track 3. | carte de l'Île-de-France en ocre et vert | — |
| 2 | La France importe 39 000 t de lentilles par an | Le rendement de la lentille varie deux fois plus que celui du blé. Une mauvaise année efface la marge. | courbe des rendements 2010–2025, 2016 et 2020 annotés | Eurostat Comext 2025 ; Agreste SAA |
| 3 | Une décision, une utilisatrice | La responsable filière d'une coopérative : à quel prix garantir la lentille pour qu'elle rapporte autant que le blé 8 années sur 10 ? | portrait type, sans photo | — |
| 4 | Au prix du marché, la lentille gagne une année sur deux | 4,7 années sur 10 à 715 €/t ; 8 sur 10 à 1 622 €/t en Seine-et-Marne. | capture de l'étape « Le prix » | Modèle ; Eurostat 2012–2016 |
| 5 | Démo | Le verrou, le prix, l'épreuve, la preuve, le contrat. | démo en direct | — |
| 6 | Sous le capot | Météo NASA POWER → modèle d'apprentissage quantile calibré par conformal → 20 000 années rejouées avec le prix du blé → P\* = quantile 80 % du prix d'équilibre. | schéma en quatre blocs | NASA POWER ; Agreste ; Eurostat |
| 7 | La preuve | Prix fixé sur les moyennes : 32 % de contrats tenus. Notre modèle : 86 % pour 80 % promis, sur 133 cas jamais vus. LightGBM, plus précis, n'en tient que 77 %. | frise du backtest et tableau des quatre façons de fixer le prix | Backtest 2019–2025 |
| 8 | Ce que nous ne savons pas encore | Prix incertain (1 132 à 3 007 €/t), rendements départementaux, 24 séries indépendantes seulement, contrats qui cèdent en 2020–2021. | liste courte | RESULTATS.md, LIMITES.md |
| 9 | Impact | 5 000 t sur 236 parcelles proches du site = 13 % des importations. Moins d'azote sur la rotation, revenu protégé 8 années sur 10. | carte du contrat de 5 000 t | Modèle ; Comext |
| 10 | Qui paie | Coopératives et conditionneurs, par campagne. Pilote d'une campagne, puis toutes les cultures sous contrat et les assureurs. | trois étapes | — |
| 11 | Architecture | S3, SageMaker (CPU), Bedrock, Amplify ; démo hors ligne en fichier unique. | schéma AWS | ARCHITECTURE.md |
| 12 | Merci | Lien vers le code et la démo. | — | — |

## Règles

- Pas de chiffre sans source en pied de slide.
- Les chiffres sont copiés depuis [RESULTATS.md](RESULTATS.md), jamais retapés de mémoire.
- Les limites ont leur slide : le jury récompense ce qui est prouvé.
