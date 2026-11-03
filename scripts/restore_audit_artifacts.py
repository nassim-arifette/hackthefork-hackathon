"""Restore the large, verbatim audit tables stored in the Colab ZIP archives."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = ('contract_policies', 'contract_policies_sensitivity', 'contract_policies_expanded')
FILES = ('predictions.csv', 'predictions_with_warmup.csv', 'results.json')


def restore(directory):
    folder = ROOT / 'experiments' / directory
    archive = folder / 'results-colab.zip'
    expected = json.loads((folder / 'execution.json').read_text())['archive_sha256']
    if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
        raise ValueError(f'Archive checksum differs: {directory}')
    with zipfile.ZipFile(archive) as saved:
        for name in FILES:
            content = saved.read(name)
            target = folder / name
            if target.exists():
                if target.read_bytes() != content:
                    raise ValueError(f'Existing local result differs; refusing to overwrite {target}')
            else:
                target.write_bytes(content)
    print(f'{directory}: three original tables restored or verified')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', action='append', choices=DIRECTORIES)
    args = parser.parse_args()
    for directory in args.directory or DIRECTORIES:
        restore(directory)
