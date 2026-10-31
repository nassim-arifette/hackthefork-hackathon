"""Atomically archive completed Colab checkpoints for download and Drive backup."""
from pathlib import Path
import zipfile

root = Path('/content/hackthefork-advanced-results')
target = Path('/content/advanced-results.zip')
temporary = target.with_suffix('.tmp')
with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(root.rglob('*')):
        if path.is_file() and not path.name.endswith('.tmp'):
            archive.write(path, path.relative_to(root))
temporary.replace(target)
print(target, target.stat().st_size)
print((root / 'progress.json').read_text() if (root / 'progress.json').exists() else 'Starting')
