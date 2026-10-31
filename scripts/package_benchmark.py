"""Build a minimal Colab input archive containing only code and public input data."""
from pathlib import Path
import zipfile

root = Path(__file__).resolve().parents[1]
paths = ["requirements-research.txt", "pipeline/benchmark_models.py", "pipeline/model.py",
         "pipeline/common.py", "pipeline/01_agreste.py", "pipeline/benchmark_contract.py",
         "pipeline/calibrate_contract_prices.py", "pipeline/forecast_research.py", "data/panel_rendements.csv",
         "data/meteo_dept.csv", "data/prix_ble.csv", "data/hypotheses.yaml"]
with zipfile.ZipFile(root / "benchmark-input.zip", "w", zipfile.ZIP_DEFLATED) as archive:
    for name in paths:
        archive.write(root / name, name)
print(root / "benchmark-input.zip")
