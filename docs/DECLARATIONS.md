# Déclaration des ressources préexistantes

Obligatoire au dépôt. Tout ce qui n'a pas été produit pendant l'événement (ouvert le vendredi 30 octobre 2026 à 17h30) est déclaré ici.

## Jeux de données

| Ressource | Usage | Licence | Remarque |
|---|---|---|---|
| Agreste SAA 2010–2025 | cible du modèle | voir [SOURCES.md](SOURCES.md) | téléchargé depuis le lien officiel |
| NASA POWER | variables météo | données publiques NASA | via API |
| RPG Île-de-France 2025 | parcelles | voir [SOURCES.md](SOURCES.md) | fourni sur le Drive de l'organisation |
| Douanes NC8 | importations | voir [SOURCES.md](SOURCES.md) | fourni sur le Drive de l'organisation |
| Registre national des cantines | extension | voir [SOURCES.md](SOURCES.md) | fourni sur le Drive de l'organisation |
| Contours des départements (gregoiredavid/france-geojson, dérivé d'IGN ADMIN EXPRESS) | centroïdes météo, contours de carte | [à vérifier] | téléchargé depuis GitHub |

Les archives du Drive de l'organisation ont été créées le 30/10/2026 à 17h36.

## Bibliothèques logicielles

Python : pandas, numpy, openpyxl, scikit-learn, scipy, lightgbm, geopandas, pyogrio, shapely, pyproj, py7zr, requests, pyyaml.
JavaScript : Vite, React, TypeScript, deck.gl, vite-plugin-singlefile.
Versions exactes : `requirements.txt` et `app/package.json`.

## Modèles pré-entraînés

Aucun modèle de prévision pré-entraîné. Le LLM utilisé pour rédiger les textes de contrat (Claude, via Amazon Bedrock) est un modèle pré-entraîné tiers : il ne produit aucun chiffre.

## Outils d'IA utilisés pendant le développement

| Outil | Usage |
|---|---|
| Claude Code (Anthropic) | aide à l'écriture du code et de la documentation |
| Amazon Bedrock (Claude) | génération des textes de contrat au build |

Autorisation de l'assistant de code externe par l'organisation : **[à confirmer]**.

## Travaux préparatoires

- Exploration des sources ouvertes et réflexion sur le sujet avant l'événement, autorisées par le règlement.
- Aucun code, modèle ou prototype propre au challenge n'a été produit avant l'ouverture.

## Dépôts tiers

- https://github.com/gregoiredavid/france-geojson : contours des départements simplifiés.
