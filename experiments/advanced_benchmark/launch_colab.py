"""Launch the archived advanced benchmark on the authorized Colab CPU runtime."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

root = Path('/content/hackthefork-advanced')
output = Path('/content/hackthefork-advanced-results')
root.mkdir(exist_ok=True)
output.mkdir(exist_ok=True)
with zipfile.ZipFile('/content/advanced-input.zip') as archive:
    for item in archive.infolist():
        if not (root / item.filename).resolve().is_relative_to(root.resolve()):
            raise ValueError('Invalid source archive path')
    archive.extractall(root)

environment = os.environ.copy()
environment.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
test = subprocess.run([sys.executable, '-m', 'pytest', '-q', 'tests'],
                      cwd=root, env=environment, capture_output=True, text=True)
(output / 'tests.txt').write_text(test.stdout + test.stderr)
print(test.stdout[-4000:])
if test.returncode:
    raise RuntimeError('Colab tests failed; inspect tests.txt before launching.')

command = [sys.executable, '-u', str(root / 'pipeline/benchmark_advanced.py'),
           '--output', str(output), '--samples', '20000', '--threads', '1']
with (output / 'run.log').open('a') as log:
    process = subprocess.Popen(command, cwd=root, env=environment, stdout=log,
                               stderr=subprocess.STDOUT, start_new_session=True)
shutil.copy2('/content/advanced-input.zip', output / 'executed-inputs.zip')
(output / 'execution.json').write_text(json.dumps({
    'environment': 'Google Colab CPU runtime', 'date': '2026-10-31',
    'command': command, 'pid': process.pid, 'threads': 1,
    'checkpoint_storage': 'Atomic Colab checkpoints, periodically exported by CLI to Drive',
    'notebook_storage': 'When Drive is mounted, notebook writes every checkpoint directly to Drive',
}, indent=2) + '\n')
print('BENCHMARK_STARTED', process.pid, str(output))
