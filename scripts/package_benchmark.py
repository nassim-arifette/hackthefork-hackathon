"""Build a minimal Colab input archive containing only code and public input data."""
from pathlib import Path
import zipfile

root = Path(__file__).resolve().parents[1]
paths = ["requirements-research.txt", "pipeline/benchmark_models.py", "pipeline/model.py",
         "pipeline/common.py", "pipeline/benchmark_checkpoint.py", "scripts/colab_benchmark.py", "pipeline/01_agreste.py", "pipeline/benchmark_contract.py",
         "pipeline/calibrate_contract_prices.py", "pipeline/forecast_research.py", "data/panel_rendements.csv",
         "data/meteo_dept.csv", "data/prix_ble.csv", "data/hypotheses.yaml"]
with zipfile.ZipFile(root / "benchmark-input.zip", "w", zipfile.ZIP_DEFLATED) as archive:
    for name in paths:
        # Stable archive hash: restoring identical sources must find the same Drive run.
        info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, (root / name).read_bytes())
print(root / "benchmark-input.zip")
