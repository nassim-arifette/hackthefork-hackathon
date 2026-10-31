"""Stop the registered first runtime and archive its resumable crop partitions."""
import json
from pathlib import Path
import subprocess
import sys
import zipfile

output = Path('/content/hackthefork-advanced-results')
execution = json.loads((output / 'execution.json').read_text())
subprocess.run([sys.executable, '/content/parallel_advanced_v2.py',
    '--root', '/content/hackthefork-advanced', '--output', str(output),
    '--stop-wrapper-pid', str(execution['partition_pid']), '--stop-only'], check=True)
target = Path('/content/advanced-results.zip')
temporary = target.with_suffix('.tmp')
with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(output.rglob('*')):
        if path.is_file() and not path.name.endswith('.tmp'):
            archive.write(path, path.relative_to(output))
temporary.replace(target)
print('MIGRATION_ARCHIVE', target.stat().st_size)
print((output / 'progress.json').read_text())
