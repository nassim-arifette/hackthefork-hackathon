# Données brutes

Téléchargées par le pipeline depuis les sources officielles (voir `docs/SOURCES.md`), versionnées ici pour que tout soit reproductible sans réseau.

| Dossier | Contenu | Script |
|---|---|---|
| `agreste/saa.zip` | Agreste, Statistique agricole annuelle 2010–2025 (départements et régions) | `01_agreste.py` |
| `nasa_power/` | réponses de l'API NASA POWER, météo journalière 2010–2025, un fichier par département | `02_weather.py` |
| `eurostat/` | prix du blé (indice), prix de la lentille, commerce Comext des lentilles | `00_prix_commerce.py` |
| `geo/departements.geojson` | contours simplifiés des départements (gregoiredavid/france-geojson) | `02_weather.py`, `04_parcels.py` |

Le RPG 2025 Île-de-France (94 Mo compressé, 358 Mo extrait) n'est pas versionné : il dépasse les limites de GitHub. `04_parcels.py` le retélécharge depuis l'IGN. Les parcelles déjà traitées sont dans `data/parcelles.json`.
