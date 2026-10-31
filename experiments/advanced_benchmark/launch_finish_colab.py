"""Start final validation and analysis independently of the notebook connection."""
from pathlib import Path
import subprocess
import sys

with Path('/content/advanced-final-job.log').open('w') as log:
    process = subprocess.Popen([sys.executable, '-u', '/content/finish_homogeneous_colab.py'],
        stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
print('FINAL_JOB_STARTED', process.pid)
