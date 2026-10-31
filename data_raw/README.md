# Données brutes

Téléchargées par le pipeline depuis les sources officielles (voir `docs/SOURCES.md`), versionnées ici pour que tout soit reproductible sans réseau.

| Dossier | Contenu | Script |
|---|---|---|
| `agreste/saa.zip` | Agreste, Statistique agricole annuelle 2010–2025 (départements et régions) | `01_agreste.py` |
| `nasa_power/` | réponses de l'API NASA POWER, météo journalière 2010–2025, un fichier par département | `02_weather.py` |
| `eurostat/` | prix du blé (indice), prix de la lentille, commerce Comext des lentilles | `00_prix_commerce.py` |
| `geo/departements.geojson` | contours simplifiés des départements (gregoiredavid/france-geojson) | `02_weather.py`, `04_parcels.py` |
| `sentinel/maillon_2024.csv.gz`, `sentinel/maillon_2025.csv.gz` | NDVI et NDMI médians par parcelle et par image Sentinel-2 L2A, 1er avril–31 juillet, zone de 24 km autour du site ; à supprimer pour relire les images | `10_maillon.py` |

Les RPG 2025 et 2024 Île-de-France (94 et 98 Mo compressés, environ 360 Mo extraits chacun) ne sont pas versionnés : ils dépassent les limites de GitHub. `04_parcels.py` et `10_maillon.py` les retéléchargent depuis l'IGN. Les parcelles déjà traitées sont dans `data/parcelles.json` et `app/src/data/maillon.json`.
