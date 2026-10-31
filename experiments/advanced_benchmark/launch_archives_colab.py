"""Package the two immutable runs as soon as both computations finish."""
from pathlib import Path
import subprocess
import sys

code = '''
import json, subprocess, sys, time
from pathlib import Path
roots = [Path('/content/hackthefork-homogeneous-results'), Path('/content/hackthefork-rpg-homogeneous-results')]
while True:
    states = [json.loads((root / 'progress.json').read_text())['status'] for root in roots]
    if all(state == 'completed' for state in states):
        break
    if 'interrupted' in states:
        raise RuntimeError('Cannot archive an interrupted benchmark')
    time.sleep(2)
subprocess.run([sys.executable, '/content/archive_homogeneous_colab.py'], check=True)
'''
with Path('/content/advanced-archive-job.log').open('w') as log:
    process = subprocess.Popen([sys.executable, '-u', '-c', code],
        stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
print('ARCHIVE_JOB_STARTED', process.pid)
