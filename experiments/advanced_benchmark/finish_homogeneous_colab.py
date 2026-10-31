"""Validate and analyze the completed homogeneous runs, in a separate checkout."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile

ROOT = Path('/content/hackthefork-final-analysis-code')
OUTPUT = Path('/content/advanced-final-artifacts')
PRIMARY = Path('/content/hackthefork-homogeneous-results')
RPG = Path('/content/hackthefork-rpg-homogeneous-results')
SOURCE = Path('/content/advanced-validation-final-code.zip')


def state(stage, **extra):
    record = {'stage': stage, **extra}
    temp = OUTPUT / 'status.json.tmp'
    temp.write_text(json.dumps(record, indent=2) + '\n')
    temp.replace(OUTPUT / 'status.json')
    print(json.dumps(record), flush=True)


def command(name, argv):
    state(name)
    with (OUTPUT / (name + '.log')).open('w') as log:
        result = subprocess.run(argv, cwd=ROOT, env=ENV, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f'{name} failed ({result.returncode}); inspect its log')


ENV = {**os.environ, 'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1',
       'NPY_DISABLE_CPU_FEATURES': 'AVX512F,AVX512CD,AVX512_SKX,AVX512_CLX,AVX512_CNL,AVX512_ICL'}
OUTPUT.mkdir(exist_ok=True)
try:
    state('preparing_analysis_checkout')
    shutil.copytree('/content/hackthefork-advanced', ROOT, dirs_exist_ok=True)
    with zipfile.ZipFile(SOURCE) as archive:
        archive.extractall(ROOT)
    shutil.copyfile(SOURCE, OUTPUT / 'executed-analysis-code.zip')
    command('tests', [sys.executable, '-m', 'pytest', '-q'])
    while True:
        progress = [json.loads((directory / 'progress.json').read_text()) for directory in (PRIMARY, RPG)]
        if all(record['status'] == 'completed' for record in progress):
            break
        if any(record['status'] == 'interrupted' for record in progress):
            raise RuntimeError('A homogeneous benchmark was interrupted')
        state('waiting_for_benchmarks', primary=progress[0], rpg=progress[1])
        time.sleep(5)
    combined, policies = OUTPUT / 'combined', OUTPUT / 'policies'
    command('merge', [sys.executable, str(ROOT / 'pipeline/merge_advanced_runs.py'),
        '--primary', str(PRIMARY), '--rpg', str(RPG), '--output', str(combined)])
    command('analysis', [sys.executable, str(ROOT / 'pipeline/analyze_advanced.py'),
        '--input', str(combined / 'predictions.csv'), '--output', str(policies),
        '--benchmark-manifest', str(combined / 'manifest.json')])
    provenance = {'analysis_code_archive_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'environment': ENV['NPY_DISABLE_CPU_FEATURES'],
        'source_files': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                         for path in (ROOT / 'pipeline/merge_advanced_runs.py', ROOT / 'pipeline/analyze_advanced.py')},
        'tests_log_sha256': hashlib.sha256((OUTPUT / 'tests.log').read_bytes()).hexdigest()}
    (OUTPUT / 'execution.json').write_text(json.dumps(provenance, indent=2) + '\n')
    state('completed')
    target = Path('/content/advanced-final-artifacts.zip')
    with zipfile.ZipFile(target.with_suffix('.tmp'), 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(OUTPUT.rglob('*')):
            if path.is_file() and not path.name.endswith('.tmp'):
                archive.write(path, path.relative_to(OUTPUT))
    target.with_suffix('.tmp').replace(target)
    print('FINAL_ANALYSIS_ARCHIVE', target.stat().st_size, flush=True)
except BaseException as error:
    state('failed', error_type=type(error).__name__, error=str(error))
    raise
