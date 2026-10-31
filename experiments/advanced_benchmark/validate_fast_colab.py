"""Run the final tests in a separate checkout without modifying executed inputs."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

target = Path('/content/hackthefork-advanced-validation')
shutil.copytree('/content/hackthefork-advanced', target, dirs_exist_ok=True)
archive = Path('/content/advanced-validation-code.zip')
with zipfile.ZipFile(archive) as bundle:
    bundle.extractall(target)
out = Path('/content/advanced-validation')
out.mkdir(exist_ok=True)
with (out / 'pytest.log').open('w') as stream:
    result = subprocess.run([sys.executable, '-m', 'pytest', '-q'], cwd=target,
        stdout=stream, stderr=subprocess.STDOUT,
        env={**os.environ, 'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1'})
record = {'returncode': result.returncode,
    'code_archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
    'log_sha256': hashlib.sha256((out / 'pytest.log').read_bytes()).hexdigest()}
(out / 'validation.json').write_text(json.dumps(record, indent=2) + '\n')
print((out / 'pytest.log').read_text())
print(json.dumps(record))
if result.returncode:
    raise RuntimeError('Validation tests failed')
