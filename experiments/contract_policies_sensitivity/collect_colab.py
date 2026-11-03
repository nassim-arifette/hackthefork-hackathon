"""Archive both finished Q80/Q90/Q95 follow-up runs."""
import json
from pathlib import Path
import shutil

parent = Path('/content/drive/MyDrive/HackTheFork/deep_audit/2026-10-31')
for label in ('policies_sensitivity', 'policies_expanded'):
    out = parent / label
    if not (out / 'results.json').exists():
        print((out / 'run.log').read_text()[-2500:])
        raise RuntimeError(label + ' is not complete')
    execution = json.loads((out / 'execution.json').read_text())
    execution['completed'] = True
    (out / 'execution.json').write_text(json.dumps(execution, indent=2) + '\n')
    archive = shutil.make_archive('/content/' + label + '-results', 'zip', out)
    print('POLICY_SENSITIVITY_COMPLETE', archive, Path(archive).stat().st_size)
