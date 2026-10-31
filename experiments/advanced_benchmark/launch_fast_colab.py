"""Resume archived, unchanged experiments on five CPU workers in Colab."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

root = Path('/content/hackthefork-advanced')
output = Path('/content/hackthefork-advanced-results')
if output.exists():
    raise RuntimeError('Restore into a fresh output directory only')
with zipfile.ZipFile('/content/advanced-resume.zip') as archive:
    archive.extractall(output)
execution = json.loads((output / 'execution.json').read_text())
previous = dict(execution)
command = [sys.executable, '-u', '/content/parallel_advanced_v2.py',
    '--root', str(root), '--output', str(output), '--workers', '5',
    '--batched-helper', '/content/batched_prediction.py']
environment = {**os.environ, 'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1'}
with (output / 'parallel-fast.log').open('a') as log:
    process = subprocess.Popen(command, cwd=root, env=environment, stdout=log,
        stderr=subprocess.STDOUT, start_new_session=True)
execution.update(partition_pid=process.pid, partition_command=command,
    previous_runtime_execution=previous,
    migration_archive_sha256=hashlib.sha256(Path('/content/advanced-resume.zip').read_bytes()).hexdigest(),
    partition_wrapper_sha256=hashlib.sha256(Path('/content/parallel_advanced_v2.py').read_bytes()).hexdigest(),
    batching_helper_sha256=hashlib.sha256(Path('/content/batched_prediction.py').read_bytes()).hexdigest())
(output / 'execution.json').write_text(json.dumps(execution, indent=2) + '\n')
print('FAST_PARALLEL_STARTED', process.pid)
