"""Run the prespecified Q80/Q90/Q95 follow-up, separately for two simulations."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

root = Path('/content/hackthefork-benchmark')
parent = Path('/content/drive/MyDrive/HackTheFork/deep_audit/2026-10-31')
source = root / 'pipeline/benchmark_contract_policies.py'
predictions = parent / 'protocol/predictions_with_warmup.csv'
assert predictions.exists()
env = os.environ.copy()
env.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
for label, protocol in [('policies_sensitivity', 'modern_raw_raw'),
                        ('policies_expanded', 'modern_expanded_expanded')]:
    out = parent / label
    out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, out / 'executed_script.py')
    command = [sys.executable, '-u', str(source), '--input', str(predictions),
               '--panel', str(root / 'data/panel_rendements.csv'), '--output', str(out),
               '--calibration-quantiles', '.8', '.9', '.95', '--base-protocol', protocol]
    with (out / 'run.log').open('w') as log:
        process = subprocess.Popen(command, cwd=root, env=env, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True)
    (out / 'execution.json').write_text(json.dumps({
        'environment': 'Google Colab existing notebook runtime', 'date': '2026-10-31',
        'command': command, 'pid': process.pid, 'device': 'CPU', 'thread_count': 1,
        'design': 'Follow-up sensitivity after the original Q80 policy run; Q90 and Q95 levels fixed before these runs.',
        'product_target': .8, 'parent_experiment': str(parent / 'policies')}, indent=2) + '\n')
    print('POLICY_SENSITIVITY_STARTED', label, process.pid)
