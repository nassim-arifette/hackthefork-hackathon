"""CLI launch used for the published multicrop run (CPU Colab)."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

root = Path('/content/hackthefork-multilegumes')
output = Path('/content/hackthefork-multilegumes-results')
root.mkdir(exist_ok=True)
output.mkdir(exist_ok=True)
with zipfile.ZipFile('/content/multilegumes-input.zip') as archive:
    for item in archive.infolist():
        if not (root / item.filename).resolve().is_relative_to(root.resolve()):
            raise ValueError('Invalid source archive path')
    archive.extractall(root)

# The local container restricts /proc, so check CatBoost on the actual runtime.
from catboost import CatBoostRegressor
import numpy as np
CatBoostRegressor(iterations=2, depth=2, verbose=False, allow_writing_files=False,
                  thread_count=1).fit(np.arange(30).reshape(10, 3), np.arange(10))
print('CATBOOST_RUNTIME_SMOKE_OK')

command = [sys.executable, '-u', str(root / 'pipeline/benchmark_multilegumes.py'),
           '--seasonal-file', str(root / 'data/meteo_saisonnier_cultures.csv'),
           '--output', str(output), '--samples', '20000', '--threads', '1']
env = os.environ.copy()
env.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
with (output / 'run.log').open('a') as log:
    process = subprocess.Popen(command, cwd=root, env=env, stdout=log,
                               stderr=subprocess.STDOUT, start_new_session=True)
shutil.copy2('/content/multilegumes-input.zip', output / 'executed-inputs.zip')
(output / 'execution.json').write_text(json.dumps({
    'environment': 'Google Colab CPU runtime', 'date': '2026-10-31',
    'command': command, 'pid': process.pid, 'threads': 1,
    'checkpoint_storage': 'Colab local; exported by CLI and backed up with Drive connector',
    'drive_note': 'Drive mount requires renewed Google consent; notebook supports per-model Drive writes.'
}, indent=2) + '\n')
print('BENCHMARK_STARTED', process.pid, str(output))
