"""Chemins, téléchargements et hypothèses partagés par les scripts du pipeline."""
from pathlib import Path
import time

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data_raw"
DATA = ROOT / "data"
APP_DATA = ROOT / "app" / "src" / "data"

AGRESTE_URL = (
    "https://agreste.agriculture.gouv.fr/agreste-web/download/publication/publie/"
    "SAA-SeriesLongues/SAA-SeriesLongues-2010-2025_DonneesProvisoires-DepartementalesRegionales.zip"
)
RPG_URL = (
    "https://data.geopf.fr/telechargement/download/RPG/RPG_4-0__GPKG_LAMB93_R11_2025-01-01/"
    "RPG_4-0__GPKG_LAMB93_R11_2025-01-01.7z"
)
DEPTS_URL = (
    "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/"
    "departements-version-simplifiee.geojson"
)

IDF = ["75", "77", "78", "91", "92", "93", "94", "95"]
IDF_AGRI = ["77", "78", "91", "95"]
# Départements producteurs bien renseignés, voisins de l'Île-de-France : ils servent
# à estimer le niveau de rendement lentille francilien (voir docs/MODELE.md).
VOISINS_LENTILLE = ["10", "51", "89", "28", "45"]

YEARS = list(range(2010, 2026))
TEST_YEARS = list(range(2019, 2026))
CLIMATO_YEARS = list(range(2010, 2019))  # climatologie fixée avant toute année test


def download(url: str, dest: Path, timeout: int = 600) -> Path:
    """Télécharge `url` vers `dest` s'il n'existe pas déjà."""
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(4):
        try:
            with requests.get(url, stream=True, timeout=timeout) as r:
                r.raise_for_status()
                tmp = dest.with_suffix(dest.suffix + ".part")
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
                tmp.rename(dest)
            return dest
        except requests.RequestException:
            if attempt == 3:
                raise
            time.sleep(2 ** (attempt + 1))
    return dest


def hypotheses() -> dict:
    """Lit data/hypotheses.yaml. Toute valeur vide bloque le pipeline."""
    h = yaml.safe_load((DATA / "hypotheses.yaml").read_text(encoding="utf-8"))
    missing = [k for k, v in h.items() if isinstance(v, dict) and v.get("valeur") is None]
    if missing:
        raise SystemExit(f"Hypothèses sans valeur dans data/hypotheses.yaml : {missing}")
    return h


def val(h: dict, key: str) -> float:
    return h[key]["valeur"]
