"""Same frozen benchmark, replacing only agricultural weather weights by RPG2015."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

root = Path('/content/hackthefork-rpg')
output = Path('/content/hackthefork-rpg-results')
root.mkdir(exist_ok=True)
output.mkdir(exist_ok=True)
with zipfile.ZipFile('/content/advanced-rpg-input.zip') as archive:
    for item in archive.infolist():
        if not (root / item.filename).resolve().is_relative_to(root.resolve()):
            raise ValueError('Invalid source archive path')
    archive.extractall(root)
command = [sys.executable, '-u', str(root / 'pipeline/benchmark_advanced.py'),
    '--output', str(output), '--samples', '20000', '--threads', '1',
    '--models', 'qrf_agri_sparse', 'qrf_agri_dense']
environment = os.environ.copy()
environment.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
with (output / 'run.log').open('a') as log:
    process = subprocess.Popen(command, cwd=root, env=environment, stdout=log,
                               stderr=subprocess.STDOUT, start_new_session=True)
shutil.copy2('/content/advanced-rpg-input.zip', output / 'executed-inputs.zip')
(output / 'execution.json').write_text(json.dumps({
    'environment': 'Google Colab CPU runtime', 'date': '2026-10-31',
    'command': command, 'pid': process.pid, 'threads': 1,
    'change': 'Only SIM agricultural weather CSV and its explicit RPG alias manifest differ',
    'checkpoint_storage': 'Atomic Colab checkpoints, periodically exported by CLI to Drive',
}, indent=2) + '\n')
print('RPG_BENCHMARK_STARTED', process.pid, str(output))
