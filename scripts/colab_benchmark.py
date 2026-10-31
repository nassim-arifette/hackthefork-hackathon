"""Execute with `colab exec -s hackthefork -f scripts/colab_benchmark.py`.

Upload benchmark-input.zip to /content first. No git credentials are needed.
TABPFN_TOKEN must be configured privately in the Colab runtime or notebook secrets.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile


def main():
    archive = Path("/content/benchmark-input.zip")
    root = Path("/content/hackthefork-benchmark")
    if not archive.is_file():
        raise FileNotFoundError("Upload benchmark-input.zip to /content first")
    if not os.environ.get("TABPFN_TOKEN"):
        from google.colab import userdata
        os.environ["TABPFN_TOKEN"] = userdata.get("TABPFN_TOKEN")
    os.environ["TABPFN_NO_BROWSER"] = "1"
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    root.mkdir(exist_ok=True)
    # Extract only the explicitly packaged files and reject path traversal.
    with zipfile.ZipFile(archive) as z:
        for entry in z.infolist():
            target = (root / entry.filename).resolve()
            if not target.is_relative_to(root.resolve()):
                raise ValueError("Unsafe archive path")
        z.extractall(root)
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(root / "requirements-research.txt"),
                    "tabpfn==9.0.0"], check=True)
    subprocess.run([sys.executable, "pipeline/benchmark_models.py", "--models", "trend", "linear",
                    "lightgbm", "qrf", "catboost", "ensemble", "tabpfn", "--device", "cuda",
                    "--calibration", "rolling", "--output", "experiments/colab_benchmark"], cwd=root, check=True)
    subprocess.run([sys.executable, "pipeline/benchmark_contract.py", "--models", "pooled", "linear",
                    "lightgbm", "qrf", "tabpfn", "--device", "cuda", "--reference",
                    "experiments/colab_benchmark/predictions.csv", "--output",
                    "experiments/colab_contract"], cwd=root, check=True)
    shutil.make_archive("/content/benchmark-results", "zip", root / "experiments")
    print("Completed: /content/benchmark-results.zip")


main()
