"""Colab runner: visible progress, per-model/year Drive checkpoints, automatic resume."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
import zipfile


def run_visible(command, cwd, output, total):
    """Stream logs and poll completed work, including while a long fit is running."""
    from IPython.display import display
    from ipywidgets import HTML, IntProgress, VBox
    bar = IntProgress(value=0, max=total, description="Progression", bar_style="info")
    label = HTML(value="Démarrage…")
    display(VBox([bar, label]))
    output.mkdir(parents=True, exist_ok=True)
    token = os.environ.get("TABPFN_TOKEN", "")
    def redact(value):
        return value.replace(token, "[secret]") if token else value
    process = subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True, bufsize=1)
    def consume():
        with (output / "execution.log").open("a") as log:
            for line in process.stdout:
                line = redact(line)
                log.write(line)
                log.flush()
                print(line, end="", flush=True)
    reader = threading.Thread(target=consume, daemon=True)
    reader.start()
    started = time.monotonic()
    try:
        while True:
            state = {}
            try:
                state = json.loads((output / "progress.json").read_text())
            except (FileNotFoundError, json.JSONDecodeError):
                pass
            from html import escape
            bar.value = state.get("completed", 0)
            label.value = (f"<b>{bar.value}/{total}</b> · {escape(state.get('active', 'Initialisation'))}"
                           f" · {int(time.monotonic() - started)} s depuis la reprise"
                           " · sauvegarde Drive après chaque modèle–année")
            if process.poll() is not None:
                break
            time.sleep(1)
        reader.join()
        if process.returncode:
            bar.bar_style = "danger"
            raise RuntimeError(f"Benchmark interrompu (code {process.returncode}). Relancer la cellule pour reprendre.")
        bar.value, bar.bar_style = total, "success"
    except BaseException:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        reader.join(timeout=5)
        bar.bar_style = "danger"
        raise


def main():
    archive = Path("/content/benchmark-input.zip")
    root = Path("/content/hackthefork-benchmark")
    drive = Path("/content/drive/MyDrive")
    if not drive.is_dir():
        raise RuntimeError("Exécuter la cellule de connexion Drive du notebook avant le benchmark.")
    if not archive.is_file():
        raise FileNotFoundError("Exécuter la cellule de préparation du notebook ou téléverser benchmark-input.zip.")
    if not os.environ.get("TABPFN_TOKEN"):
        from google.colab import userdata
        os.environ["TABPFN_TOKEN"] = userdata.get("TABPFN_TOKEN")
    os.environ.update(TABPFN_NO_BROWSER="1", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
    root.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        for entry in z.infolist():
            if not (root / entry.filename).resolve().is_relative_to(root.resolve()):
                raise ValueError("Unsafe archive path")
        z.extractall(root)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    destination = drive / "HackTheFork" / "benchmarks" / digest[:16]
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(archive, destination / "benchmark-input.zip")
    sys.path.insert(0, str(root / "pipeline"))
    from benchmark_checkpoint import atomic_json
    atomic_json(destination / "run.json", {"archive_sha256": digest, "status": "installing"})
    print(f"Sauvegarde automatique : {destination}", flush=True)
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r",
                        str(root / "requirements-research.txt"), "tabpfn==9.0.0", "ipywidgets>=8,<9"], check=True)
        # Probe in a fresh process: notebook imports may predate pip's updates.
        subprocess.run([sys.executable, "-c", "import torch; assert torch.cuda.is_available(), 'Sélectionner un runtime GPU'; print(torch.cuda.get_device_name(0))"], check=True)
        atomic_json(destination / "run.json", {"archive_sha256": digest, "status": "running"})
        yields = destination / "colab_benchmark"
        direct = destination / "colab_contract"
        run_visible([sys.executable, "-u", "pipeline/benchmark_models.py", "--models", "trend", "linear",
                     "lightgbm", "qrf", "catboost", "ensemble", "tabpfn", "--device", "cuda",
                     "--calibration", "rolling", "--output", str(yields)], root, yields, 7 * 8)
        run_visible([sys.executable, "-u", "pipeline/benchmark_contract.py", "--models", "pooled", "linear",
                     "lightgbm", "qrf", "tabpfn", "--device", "cuda", "--reference",
                     str(yields / "predictions.csv"), "--output", str(direct)], root, direct, 10 * 5)
        with zipfile.ZipFile("/content/benchmark-results.zip", "w", zipfile.ZIP_DEFLATED) as z:
            for folder in (yields, direct):
                for path in sorted(folder.rglob("*")):
                    if path.is_file() and not path.name.endswith(".tmp"):
                        z.write(path, path.relative_to(destination))
        temporary = destination / "benchmark-results.zip.tmp"
        shutil.copy2("/content/benchmark-results.zip", temporary)
        temporary.replace(destination / "benchmark-results.zip")
        atomic_json(destination / "run.json", {"archive_sha256": digest, "status": "complete"})
        print(f"Terminé. Résultats : {destination / 'benchmark-results.zip'}")
    except BaseException as exc:
        atomic_json(destination / "run.json", {"archive_sha256": digest, "status": "interrupted",
                                               "error_type": type(exc).__name__})
        print("Les étapes terminées sont dans Drive. Relancer la dernière cellule reprend le calcul.")
        raise


if __name__ == "__main__":
    main()
