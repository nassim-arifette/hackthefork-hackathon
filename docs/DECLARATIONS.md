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
| Sentinel-2 L2A (Copernicus), via le catalogue Earth Search d'Element 84 | suivi en saison, prototype | données Copernicus en accès libre, citation demandée | lues en ligne par `08_sentinel.py` |
| Contours des départements (gregoiredavid/france-geojson, dérivé d'IGN Admin Express COG 2018) | centroïdes météo, contours de carte | Licence Ouverte (Etalab), selon le dépôt | téléchargé depuis GitHub |
| RPG 2025 Île-de-France (IGN, data.geopf.fr) | parcelles de la carte | voir [SOURCES.md](SOURCES.md) | téléchargé depuis le site de l'IGN |
| Eurostat : prix agricoles et Comext | prix du blé et de la lentille, commerce extérieur | réutilisation autorisée avec citation | via l'API Eurostat |

Les archives du Drive de l'organisation ont été créées le 30/10/2026 à 17h36.

Les références documentaires des hypothèses (guides Terres Inovia, notice Telepac, synthèse FiloLeg, Mémento DRIAAF, GIEC) sont listées dans [SOURCES.md](SOURCES.md) et [QUESTIONS.md](QUESTIONS.md).

## Bibliothèques logicielles

Python : pandas, numpy, openpyxl, scikit-learn, scipy, lightgbm, geopandas, pyogrio, shapely, pyproj, py7zr, requests, pyyaml, rasterio, pystac-client.
JavaScript : Vite, React, TypeScript, deck.gl, vite-plugin-singlefile.
Polices : Archivo et Source Serif 4 (licence SIL Open Font License), via Fontsource.
Versions exactes : `requirements.txt` et `app/package.json`.

## Modèles pré-entraînés

Aucun modèle de prévision pré-entraîné. Le LLM utilisé pour rédiger les textes de contrat (Claude, via Amazon Bedrock) est un modèle pré-entraîné tiers : il ne produit aucun chiffre.

## Outils d'IA utilisés pendant le développement

| Outil | Usage |
|---|---|
| Claude Code (Anthropic) | aide à l'écriture du code et de la documentation |
| ChatGPT (OpenAI) | recherche documentaire des réponses de mentor ([QUESTIONS.md](QUESTIONS.md)) ; sources relues et chiffres recalculés par le pipeline |
| Amazon Bedrock (Claude) | lettre d'accompagnement au build, facultative ; aucun chiffre produit (garde-fou testé) |

Autorisation de l'assistant de code externe par l'organisation : **confirmée** (équipe, 31/10/2026).

## Travaux préparatoires

- Exploration des sources ouvertes et réflexion sur le sujet avant l'événement, autorisées par le règlement.
- Aucun code, modèle ou prototype propre au challenge n'a été produit avant l'ouverture.

## Dépôts tiers

- https://github.com/gregoiredavid/france-geojson : contours des départements simplifiés.
