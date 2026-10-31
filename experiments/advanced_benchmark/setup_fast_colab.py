"""Prepare an additional Colab runtime from the same frozen input archive."""
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import zipfile

root = Path('/content/hackthefork-advanced')
root.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile('/content/advanced-input.zip') as archive:
    archive.extractall(root)
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '-r',
                str(root / 'requirements-research.txt')], check=True)
print(json.dumps({'python': platform.python_version(), 'cpus': os.cpu_count(),
                  'machine': platform.machine(), 'root': str(root)}))
