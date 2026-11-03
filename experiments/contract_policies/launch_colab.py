"""Run the policy experiment after protocol attribution finishes in this Colab."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

root = Path('/content/hackthefork-benchmark')
out = Path('/content/drive/MyDrive/HackTheFork/deep_audit/2026-10-31/policies')
source = root / 'pipeline/benchmark_contract_policies.py'
predictions = out.parent / 'protocol/predictions_with_warmup.csv'
assert predictions.exists(), 'Finish the protocol-attribution run first'
out.mkdir(parents=True, exist_ok=True)
shutil.copy2(source, out / 'executed_script.py')
command = [sys.executable, '-u', str(source), '--input', str(predictions),
           '--panel', str(root / 'data/panel_rendements.csv'), '--output', str(out)]
env = os.environ.copy()
env.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
with (out / 'run.log').open('w') as log:
    process = subprocess.Popen(command, cwd=root, env=env, stdout=log,
                               stderr=subprocess.STDOUT, start_new_session=True)
(out / 'execution.json').write_text(json.dumps({
    'environment': 'Google Colab existing notebook runtime',
    'date': '2026-10-31', 'command': command, 'pid': process.pid,
    'device': 'CPU', 'thread_count': 1}, indent=2) + '\n')
print('POLICIES_STARTED', process.pid, str(out))
