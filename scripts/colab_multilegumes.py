"""Visible Colab run, Drive checkpoints and exact-input automatic resume."""
import hashlib
from html import escape
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
INPUTS = [
    *sorted((ROOT / 'pipeline').glob('*.py')),
    *[ROOT / 'data' / name for name in (
        'panel_rendements.csv', 'meteo_dept_cultures.csv',
        'meteo_saisonnier_cultures.csv', 'prix_ble.csv',
        'hypotheses.yaml', 'cultures.yaml')],
    ROOT / 'requirements-research.txt',
]


def run_visible(command, output, total=300):
    from IPython.display import display
    from ipywidgets import HTML, IntProgress, VBox

    bar = IntProgress(value=0, max=total, description='Progression', bar_style='info')
    label = HTML(value='Préparation…')
    display(VBox([bar, label]))
    env = os.environ.copy()
    env.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True, bufsize=1)

    def consume():
        with (output / 'execution.log').open('a', encoding='utf-8') as stream:
            for line in process.stdout:
                stream.write(line)
                stream.flush()
                print(line, end='', flush=True)

    reader = threading.Thread(target=consume, daemon=True)
    reader.start()
    started = time.monotonic()
    try:
        while process.poll() is None:
            try:
                state = json.loads((output / 'progress.json').read_text())
            except (FileNotFoundError, json.JSONDecodeError):
                state = {}
            bar.max = state.get('total', total)
            bar.value = state.get('completed', 0)
            label.value = (f'<b>{bar.value}/{bar.max}</b> · '
                           f'{escape(str(state.get("active", "Préparation")))} · '
                           f'{int(time.monotonic() - started)} s depuis la reprise · '
                           'sauvegarde Drive après chaque culture–modèle–année')
            time.sleep(1)
        reader.join()
        if process.returncode:
            raise RuntimeError(f'Calcul interrompu (code {process.returncode}). '
                               'Les étapes terminées sont sur Drive ; relancer cette cellule.')
        bar.value, bar.bar_style = bar.max, 'success'
        label.value = 'Terminé — résultats et points de reprise enregistrés sur Drive.'
    except BaseException:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        reader.join(timeout=5)
        bar.bar_style = 'danger'
        raise


def main():
    drive = Path('/content/drive/MyDrive')
    if not drive.is_dir():
        raise RuntimeError('Monter Google Drive dans la cellule précédente avant de lancer le calcul.')
    digest = hashlib.sha256()
    for path in INPUTS:
        digest.update(str(path.relative_to(ROOT)).encode())
        digest.update(path.read_bytes())
    destination = drive / 'HackTheFork' / 'multilegumes' / digest.hexdigest()[:16]
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination / 'executed-inputs.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in INPUTS:
            archive.write(path, path.relative_to(ROOT))
    print(f'Sauvegarde automatique : {destination}', flush=True)
    run_visible([sys.executable, '-u', str(ROOT / 'pipeline/benchmark_multilegumes.py'),
                 '--seasonal-file', str(ROOT / 'data/meteo_saisonnier_cultures.csv'),
                 '--output', str(destination), '--samples', '20000'], destination)
    print('Calibration passée, comparaison M0 et sous-groupes…', flush=True)
    subprocess.check_call([sys.executable, str(ROOT / 'pipeline/analyze_multilegumes.py'),
                           '--input', str(destination / 'predictions.csv'),
                           '--output', str(destination / 'policies')], cwd=ROOT)
    print('Prédictions :', destination / 'predictions.csv')
    print('Synthèse :', destination / 'summary.csv')
    print('Conclusions :', destination / 'policies/REPORT.md')


if __name__ == '__main__':
    main()
