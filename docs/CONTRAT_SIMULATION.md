# Contrat de simulation : barème public et scénario complet

**Recherche du 31 octobre 2026.** Ce document permet de simuler un contrat de lentille verte conventionnelle pour l'alimentation humaine. Il associe un **barème public historique** à une **fiche commerciale synthétique complète**. Aucune entreprise citée n'est engagée dans notre pilote et aucun contrat signé n'a été obtenu.

Les paramètres lisibles par machine sont dans [contrats.json](../data/pilote_300t/contrats.json). Les données et leurs conventions sont décrites dans le [README du jeu de simulation](../data/pilote_300t/README.md) ; la proposition de partenariat figure dans [PILOTE_300T.md](PILOTE_300T.md).

## 1. Trois contrats, trois usages

| Identifiant | Contenu | Statut |
|---|---|---|
| `public_natup_2023_2024` | Barème marginal 900 / 700 / 600 €/t | Reconstruction d'un barème public ; autres clauses de simulation à distinguer. |
| `synthetique_2027` | Barème 1 000 / 750 / 650 €/t, prime de service et règles ci-dessous | Proposition fictive, campagnes 2027–2029. |
| `uniforme_900` | Prix uniforme de 900 €/t nette et prime de service | Comparateur synthétique simple. |

Le comparateur applique aux trois barèmes les mêmes lots, coûts, qualité, assiette nette et prime de service synthétique. Ces conventions communes ne deviennent pas des clauses réelles de NatUp.

## 2. Le barème public NatUp 2023–2024

Un entretien d'*Union Agricole*, publié le **18 septembre 2023**, décrit la politique de rémunération annoncée pour la récolte 2023 et reconduite pour 2024 : 900 €/t sur les dix premiers quintaux par hectare, 700 €/t entre onze et vingt quintaux, puis un minimum de 600 €/t avec complément possible selon le marché. [S1]

Le texte indique un fonctionnement par tranche. Nous l'interprétons comme un **barème marginal continu** :

~~~text
B_public(y) =
    900 × min(y, 1)
  + 700 × min(max(y − 1, 0), 1)
  + 600 × max(y − 2, 0)
~~~

B est une recette en €/ha et y le rendement payé en t/ha. La dernière tranche du reportage n'est pas une clause contractuelle reproduite : cette interprétation est déclarée dans la simulation. Le complément de marché est fixé à zéro, faute de règle publiée.

**Informations non publiées dans cette source :** assiette brute ou nette exacte, primes complémentaires, critères d'agréage détaillés, facture de tri, acompte et traitement des refus. La simulation utilise ses propres conventions pour ces champs.

Le communiqué NatUp de septembre 2025 mentionne séparément **1 000 € pour la première tonne par hectare** et un engagement triennal. Il ne permet pas de reconstituer les autres paliers de cette campagne. Les deux publications restent donc deux références distinctes. [S2]

## 3. Fiche synthétique pour les campagnes 2027–2029

Les montants de simulation sont exprimés en euros hors taxes.

### Produit, engagement et rémunération

| Champ | Choix de simulation |
|---|---|
| Parties | Un collectif de producteurs et un acheteur fictifs. |
| Produit | Lentille verte conventionnelle française destinée à l'alimentation humaine. |
| Durée | Trois campagnes : 2027, 2028 et 2029. |
| Engagement | Surface annuelle identifiée et livraison de sa récolte ; aucun minimum de rendement imposé. |
| Premier palier | 1 000 €/t nette acceptée jusqu'à 1 t/ha. |
| Deuxième palier | 750 €/t nette acceptée entre 1 et 2 t/ha. |
| Troisième palier | 650 €/t nette acceptée au-delà de 2 t/ha. |
| Prime de service | 30 €/t nette acceptée pour un lot pré-nettoyé. |
| Prime par hectare | Zéro dans ce scénario de référence ; une variante peut être calculée par le moteur. |
| Assiette | Tonnes nettes alimentaires acceptées après tri et agréage. |

Les paliers s'appliquent au **rendement net payé de chaque engagement producteur–campagne**, agrégé sur ses livraisons et divisé par sa surface engagée. Diviser artificiellement les livraisons ne recrée pas un premier palier. Un fichier avec une ligne par producteur et campagne peut appliquer directement cette règle.

Le premier palier s'inspire du repère NatUp 2025. Les autres prix et la prime de 30 € sont nos hypothèses. L'existence de primes pour pré-triage ou conditionnement en big bag est décrite dans une rencontre avec ALIGERMA du **17 novembre 2025**, qui mentionne aussi un acompte et un ajustement des volumes après tri. Aucun montant de prime n'y est publié. [S3]

### Qualité et poids payé

| Moment | Règle du scénario |
|---|---|
| Réception | Pesée et analyse du lot. Le poids entrant est la masse brute reçue, après l'éventuel pré-nettoyage du producteur. |
| Tri | Retrait des matières étrangères et des fractions non retenues pour le débouché alimentaire ; suivi séparé des écarts. |
| Agréage final | Humidité ≤ 15 % ; défauts et impuretés résiduels ≤ 2 % ; aucun insecte vivant ni moisissure. |
| Lot conforme | Paiement sur sa masse nette alimentaire acceptée. |
| Lot refusé en alimentaire | Masse alimentaire payée nulle ; éventuelle autre valorisation enregistrée séparément, à zéro par défaut. |

Ces seuils sont **supposés**. Le diagnostic de Terres Univia donne, selon les acheteurs, des références de commercialisation de 14–16 % d'humidité, 0–3 % d'impuretés et zéro insecte vivant. Il inclut les graines cassées ou bruchées dans les défauts pris en compte. [S4]

Le taux de graines bruchées n'est pas une perte massique : défauts bruts, écarts de tri, masse nette et refus sont distincts. Un grain écarté n'est soustrait qu'une fois. La perte d'eau au séchage est séparée des écarts solides.

### Qui paie le tri et la collecte ?

Le producteur prend en charge le pré-nettoyage dans ses charges agricoles. L'acheteur paie le tri complet et la collecte :

~~~text
Coût_tri = 180 €/t brute entrante × masse_brute_entrante
Coût_collecte = (5 + 0,12 × distance_routière_km) × masse_brute_entrante
~~~

Le choix de 180 €/t est une **hypothèse de budget**, appuyée par une publication Bio Hauts-de-France qui indique 180 €/t pour une prestation optique et jusqu'à 500 €/t pour une prestation complète, dans un contexte bio et de tri à la ferme ou mobile. La facturation sur tonnes brutes est notre convention ; aucun tarif industriel NatUp n'est inféré. Tester 100 / 180 / 300 €/t. [S5]

Le partage des tâches est plausible : la FNAB décrit des circuits longs bio dans lesquels seul le pré-nettoyage incombe au producteur. Nous transposons cette organisation au scénario conventionnel. [S6]

La distance est routière aller simple ; le coefficient global représente la logistique retenue. Le forfait de 5 €/t suppose des lots agrégés. Si l'humidité dépasse 15 %, un séchage vers 14 % est facturé à l'acheteur : **3 €/t reçue/point d'humidité retiré**, hypothèse supplémentaire sans devis. Les opérations effectuées restent facturées en cas de refus ultérieur.

### Acompte et régularisation

L'acompte vaut **30 % de la recette alimentaire estimée à réception**, avec une estimation explicite du poids net futur. Il constitue une avance, pas un supplément de revenu.

~~~text
Solde = recette_finale_après_agréage − acompte_déjà_versé
~~~

Si le solde est négatif, le scénario enregistre un **trop-versé à régulariser**. En cas de refus total et de valeur de récupération nulle, la recette finale est zéro et tout acompte devient trop-versé. La marge du modèle utilise toujours la recette finale ; la trésorerie présente séparément l'avance et sa régularisation.

L'historique fourni enregistre les **règlements finaux** : il ne simule pas les dates de versement et de remboursement de l'acompte.

## 4. Formules à appliquer

Pour une surface A en hectares, une masse brute M_b et une masse alimentaire nette acceptée M_n en tonnes :

~~~text
y = M_n / A

B_synthétique(y) =
    1 000 × min(y, 1)
  +   750 × min(max(y − 1, 0), 1)
  +   650 × max(y − 2, 0)

Recette_producteur =
    A × B_synthétique(y)
  + 30 × M_n [si prestation de service remplie]

Budget_acheteur =
    recette_producteur
  + coût_tri + coût_collecte + coût_séchage
  − valeur_récupération_écarts

Marge_campagne_producteur =
    recette_producteur − charges_agricoles + aide_PAC

Marge_avec_rotation =
    marge_campagne_producteur + bénéfice_rotation
~~~

Prime contractuelle, aide PAC et bénéfice de rotation sont distincts. Le tri payé par l'acheteur n'est pas déduit à nouveau de la recette producteur. Le budget exclut stockage, conditionnement et frais généraux.

Les charges du jeu de données restent partielles : le résultat calculé n'est pas un revenu net d'exploitation.

## 5. Deux exemples vérifiables

Les exemples supposent une humidité ≤ 15 % sans séchage, un lot conforme pré-nettoyé, **10 ha**, **30 km routiers** et une récupération nulle. Les tonnes brutes sont les tonnes **reçues**.

| Calcul | Exemple A : 18 t brutes, 16 t nettes | Exemple B : 30 t brutes, 26 t nettes |
|---|---:|---:|
| Rendement net payé | 1,6 t/ha | 2,6 t/ha |
| Premier palier : 10 t × 1 000 € | 10 000 € | 10 000 € |
| Deuxième palier | 6 t × 750 = 4 500 € | 10 t × 750 = 7 500 € |
| Troisième palier | 0 € | 6 t × 650 = 3 900 € |
| Prime : tonnes nettes × 30 € | 480 € | 780 € |
| **Recette finale producteur** | **14 980 €** | **22 180 €** |
| Tri : tonnes brutes × 180 € | 3 240 € | 5 400 € |
| Collecte : tonnes brutes × 8,60 € | 154,80 € | 258 € |
| **Budget acheteur** | **18 374,80 €** | **27 838 €** |
| Budget par tonne nette acceptée | 1 148,43 €/t | 1 070,69 €/t |

Pour l'exemple A, si l'estimation à réception est exactement réalisée, l'acompte est de **4 494 €** et le solde de **10 486 €**. Si le lot est finalement entièrement refusé après traitement, la recette alimentaire devient zéro, le trop-versé est de 4 494 € et l'acheteur conserve **3 394,80 €** de frais de tri et de collecte. Le coût par tonne alimentaire devient non défini lorsque le volume accepté est nul.

Le seul barème public reconstruit donne **13 200 €** dans l'exemple A et **19 600 €** dans B, hors compléments inconnus. Le prix uniforme de 900 €/t donne **14 400 €** et **23 400 €**. Le comparateur ajoute à chacun la prime synthétique commune, soit **480 €** et **780 €** ; elle n'est pas documentée chez NatUp.

## 6. Protection face au blé, calculée par le moteur

Le moteur de l'application juge ces barèmes sur ses 20 000 années simulées pour la Seine-et-Marne et sur son backtest historique 2019–2025 (`pipeline/07_contrats.py`, `pipeline/03_backtest.py`). L'entraînement et la calibration glissent dans le temps, mais les regroupements Agreste de ce backtest utilisent toute la période 2010–2025. Les lots synthétiques n'y entrent pas : ils servent à exercer les paiements et les coûts, pas à mesurer une fréquence.

| Barème | Années où la lentille bat le blé | Coût moyen par tonne acceptée | Contrats tenus en backtest |
|---|---:|---:|---:|
| Public reconstitué 900 / 700 / 600 | 5,9 sur 10 | 818 €/t | 55 % |
| Proposition 1 000 / 750 / 650 + 30 €/t | 6,4 sur 10 | 928 €/t | 65 % |
| Uniforme 900 €/t, sans prime | 6,1 sur 10 | 900 €/t | 57 % |
| Tranches recalibrées pour 8 sur 10 : **1 635** / 750 / 650 | 8,0 sur 10 | 1 283 €/t | 87 % |

Pour atteindre 8 années sur 10 avec les deuxième et troisième tranches de la proposition, la première tonne doit être payée 1 635 €/t. Ce barème protège autant qu'un prix unique de 1 568 €/t pour un coût moyen inférieur de 18 %. Les coûts du moteur excluent collecte, tri et séchage, détaillés plus haut. Détail et lecture dans [RESULTATS.md](RESULTATS.md#7-comparer-les-contrats).

## 7. Provenance par champ

| Champ | Réellement publié | Choix ajouté pour simuler |
|---|---|---|
| Barème historique | NatUp 2023–2024 : 900 / 700 / minimum 600. [S1] | Interprétation marginale ; complément de marché nul. |
| Premier palier récent, durée | NatUp 2025 : première tonne à 1 000 €, triennal. [S2] | Campagnes 2027–2029 ; autres paliers 750 / 650. |
| Prime, acompte, poids après tri | Mécanismes décrits chez ALIGERMA. [S3] | Prime 30 €/t, acompte 30 %, régularisation explicite. |
| Qualité | Plages de filière variables selon l'acheteur. [S4] | Seuils 15 % / 2 % / zéro insecte vivant. |
| Tri | Repères de prestations en contexte bio. [S5] | 180 €/t brute, facture à l'acheteur. |
| Pré-nettoyage | Organisation de circuits longs bio décrite par la FNAB. [S6] | Transposition au scénario conventionnel. |
| Collecte | Hypothèses du projet. | 5 €/t + 0,12 €/t/km routier. |
| Séchage | Hypothèse du projet. | 3 €/t reçue/point retiré, acheteur ; déclenchement > 15 %, cible 14 %. |
| Refus et récupération | Aucun barème privé obtenu. | Paiement alimentaire nul, récupération nulle par défaut. |

### Sources

- [S1 — Union Agricole, 18 septembre 2023 : entretien sur les récoltes 2023–2024][S1].
- [S2 — NatUp, 18 septembre 2025 : communiqué filière lentille][S2].
- [S3 — Biocivam de l'Aude, rencontre du 17 novembre 2025, p. 5 ; mise en ligne mars 2026][S3].
- [S4 — Terres Univia, diagnostic 2021, publication 2022, p. 5][S4].
- [S5 — Bio Hauts-de-France : références et expérimentations 2020–2024 avec Biocer, rubrique triage][S5].
- [S6 — Produire Bio / FNAB, 30 avril 2020 : charges selon le circuit de vente][S6].

[S1]: https://www.union-agricole.fr/natup-souhaite-augmenter-les-surfaces-de-lentilles
[S2]: https://natup.coop/download/5775/
[S3]: https://docs.bio-occitanie.org/wp-content/uploads/2026/03/CR_17.11.pdf
[S4]: https://www.terresunivia.fr/fichiers/publications/filiere-lentille-2022.pdf
[S5]: https://www.bio-hautsdefrance.org/systeme_bio/cultures-innovantes-de-nouvelles-opportunites-pour-les-grandes-cultures-bio/
[S6]: https://www.produire-bio.fr/articles-pratiques/diversifier-la-rotation-la-lentille-une-legumineuse-qui-ne-manque-pas-dinterets/
