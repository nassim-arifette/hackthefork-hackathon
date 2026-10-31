"""Resume the same logical run on two CPU workers without losing checkpoints."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

output = Path('/content/hackthefork-advanced-results')
execution = json.loads((output / 'execution.json').read_text())
previous = execution.get('partition_pid')
active = False
if previous and (Path('/proc') / str(previous) / 'cmdline').exists():
    active = b'parallel_advanced.py' in (Path('/proc') / str(previous) / 'cmdline').read_bytes()
if active:
    print('PARALLEL_ALREADY_RUNNING', previous)
else:
    command = [sys.executable, '-u', '/content/parallel_advanced.py',
        '--root', '/content/hackthefork-advanced', '--output', str(output), '--workers', '2']
    original = Path('/proc') / str(execution['pid']) / 'cmdline'
    if original.exists() and b'benchmark_advanced.py' in original.read_bytes():
        command += ['--stop-pid', str(execution['pid'])]
    environment = os.environ.copy()
    environment.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    with (output / 'parallel.log').open('a') as log:
        process = subprocess.Popen(command, env=environment, stdout=log,
            stderr=subprocess.STDOUT, start_new_session=True)
    execution.update(partition_pid=process.pid, partition_command=command,
        partition_wrapper_sha256=hashlib.sha256(Path('/content/parallel_advanced.py').read_bytes()).hexdigest())
    (output / 'execution.json').write_text(json.dumps(execution, indent=2) + '\n')
    print('PARALLEL_STARTED', process.pid)
