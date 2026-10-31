"""Reassemble the exact benchmark gzip files from versioned binary parts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    sha = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            sha.update(block)
    return sha.hexdigest()


def restore(root=ROOT, verify_only=False):
    root = Path(root).resolve()
    manifest = json.loads((root / 'experiments/advanced_benchmark/git_artifacts.json').read_text())
    for record in manifest['files']:
        target = root / record['path']
        parts = [(root / part['path'], part) for part in record['parts']]
        for path, part in parts:
            if path.stat().st_size != part['size'] or digest(path) != part['sha256']:
                raise ValueError(f'Invalid archive part: {path}')
        if target.exists() and target.stat().st_size == record['size'] and digest(target) == record['sha256']:
            print(f'Verified {record["path"]}')
            continue
        if verify_only:
            raise ValueError(f'Missing or invalid reconstructed file: {target}')
        temporary = target.with_name(target.name + '.restoring')
        try:
            with temporary.open('wb') as output:
                for path, _ in parts:
                    with path.open('rb') as source:
                        for block in iter(lambda: source.read(1024 * 1024), b''):
                            output.write(block)
            if temporary.stat().st_size != record['size'] or digest(temporary) != record['sha256']:
                raise ValueError(f'Invalid reconstructed archive: {target}')
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
        print(f'Restored {record["path"]}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    restore(args.root, args.verify_only)
