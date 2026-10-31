"""Archive the finished policy experiment from its Drive output directory."""
import json
from pathlib import Path
import shutil

out = Path('/content/drive/MyDrive/HackTheFork/deep_audit/2026-10-31/policies')
if not (out / 'results.json').exists():
    print((out / 'run.log').read_text()[-2500:])
    raise RuntimeError('Policy run is not complete')
execution = json.loads((out / 'execution.json').read_text())
execution['completed'] = True
(out / 'execution.json').write_text(json.dumps(execution, indent=2) + '\n')
archive = shutil.make_archive('/content/contract-policy-results', 'zip', out)
print('POLICIES_COMPLETE', archive, Path(archive).stat().st_size)
