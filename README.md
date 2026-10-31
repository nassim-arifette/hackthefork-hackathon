# Le Contrat qui Tient

**Hack the Fork Paris 2026 · Track 3 — scénario de contrat lentille / blé**

L'outil cherche un prix de contrat compatible avec l'objectif du producteur **et** le plafond économique de l'acheteur. Il conserve les cinq étapes : **Le verrou → Le prix → L'épreuve → La preuve → Le contrat**.

Le prix calculé vise 80 % des scénarios simulés. Il ne garantit ni le rendement, ni la marge d'une exploitation, ni huit bonnes années dans une décennie réelle. Le backtest est une **reconstitution sous hypothèses économiques**, avec charges fixes et prix du blé reconstruit à partir d'Eurostat et d'Agreste.

## Version corrigée

- Apprentissage, sélection et calibration sur trois fenêtres temporelles disjointes ; prédicteur conservé après calibration.
- Normalisation des rendements, regroupement des séries et transformations météo ajustés sur l'apprentissage seul.
- Comparaison M0 (sans météo), M1 (régression quantile), M2 (LightGBM), M3 (moyenne de leurs quantiles), sélection automatique et quantile historique des prix d'équilibre appariés.
- Évaluation de la précision, de la couverture, du prix payé, du coût d'achat et des pertes résiduelles. Aucun modèle n'est déclaré supérieur à partir du seul taux de succès.
- Quantiles bruts pour la simulation, bornes calibrées pour les intervalles ; sensibilités explicites aux queues et à la dépendance résiduelle des cultures.
- Aide non confirmée : **0 €/ha** dans le scénario principal ; **122 €/ha** dans une variante conditionnelle.
- Lentille : **référence historique nominale 2012–2016, non représentative d'une cotation actuelle**. L'utilisateur saisit son offre hypothétique.
- Une seule campagne 2026, même prix rendu, même transport, mêmes parcelles et même volume attendu du replay au contrat.
- Plafond acheteur = revente × (1 − pertes au tri) − coûts − marge minimale. L'interface peut conclure « accord impossible ».

Résultats recalculés : [RESULTATS](docs/RESULTATS.md). Protocole et limites : [MODELE](docs/MODELE.md), [LIMITES](docs/LIMITES.md). Articles consultés et choix : [RECHERCHE](docs/RECHERCHE.md).

## Reproduire à partir des fichiers versionnés

Python 3.12+ et Node 22. Pour les seuls recalculs, les bibliothèques géographiques ne sont pas requises :

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-model.txt
make recalculate PY="$PWD/.venv/bin/python"
.venv/bin/python -m pytest -q tests
cd app
npm ci
npm run build
npm run build:single
npm run dev
```

`make recalculate` utilise les données traitées et les géométries RPG déjà versionnées. Il recalcule le backtest, les seuils, les parcelles, le volume et les métadonnées. Aucun accès AWS n'est nécessaire. Sans `BEDROCK_MODEL_ID`, la lettre facultative est vidée pour éviter de réutiliser un ancien scénario.

`app/dist-single/index.html` est la démonstration autonome. `make all` reconstruit aussi les données depuis les sources publiques ; installer pour cela `requirements.txt`. Les distances RPG mises en cache ne sont réutilisées que si le site et le facteur de détour sont inchangés.

## Ce que les preuves permettent d'affirmer

Les prix évalués pour une année utilisent seulement les données antérieures. Les tests perturbent les rendements, surfaces, prix et météo de l'année test et des années suivantes, puis vérifient que ces décisions restent identiques. D'autres tests contrôlent les appels effectifs d'apprentissage, l'absence de réentraînement après calibration et la cohérence des exports.

Les diagnostics de rendement conditionnels utilisent la météo de l'année évaluée observée rétrospectivement ; ils ne constituent pas une prévision météo avant semis. Les décisions de prix, elles, utilisent uniquement la météo passée.

Sept années d'évaluation et des rendements départementaux ne suffisent pas à établir une garantie individuelle. Ces historiques ont déjà été examinés lors du développement : l'étude reste rétrospective et exige une future validation indépendante. Le regroupement produit des **séries retenues**, pas une preuve d'indépendance statistique.

## Fichiers

- `pipeline/` : acquisition, modèles, évaluation et export.
- `data/` : données traitées et hypothèses traçables.
- `app/src/` : interface React et données JSON recalculées.
- `tests/` : invariance temporelle, calibration, économie et cohérence.
- `docs/` : méthode, résultats, références, limites et parcours de démonstration.

Les licences et sources des données sont listées dans [SOURCES](docs/SOURCES.md).
