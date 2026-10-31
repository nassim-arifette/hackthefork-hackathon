"""Advanced benchmark with progress and source/NumPy-profile Drive checkpoints."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from colab_multilegumes import run_visible

# quantile-forest samples one observation per leaf by default. NumPy's SIMD
# argsort can reorder tied leaf IDs across CPUs before this seeded sample.
# Apply the evaluated execution profile before launching fresh child processes.
NUMPY_DISABLED_FEATURES = 'AVX512F,AVX512CD,AVX512_SKX,AVX512_CLX,AVX512_CNL,AVX512_ICL'


def numerical_profile(runtime):
    """Keep numerical dispatcher identity separate from machine/core metadata."""
    required = ('numpy_version', 'numpy_dispatch_override', 'numpy_cpu_features',
                'numpy_cpu_baseline', 'numpy_cpu_dispatch')
    if not isinstance(runtime, dict) or any(key not in runtime for key in required):
        raise ValueError('Profil numérique NumPy incomplet : reprise impossible.')
    override = runtime['numpy_dispatch_override']
    flags = runtime['numpy_cpu_features']
    if (override is not None and not isinstance(override, str)) or (
            not isinstance(flags, dict) or not flags or
            any(not isinstance(key, str) or type(value) is not bool for key, value in flags.items())):
        raise ValueError('Profil numérique NumPy invalide : reprise impossible.')
    return {'numpy_version': runtime['numpy_version'],
            'numpy_dispatch_override': sorted(set(part.strip() for part in (override or '').split(',') if part.strip())),
            'numpy_cpu_features': dict(sorted(flags.items())),
            'numpy_cpu_baseline': sorted(set(runtime['numpy_cpu_baseline'])),
            'numpy_cpu_dispatch': sorted(set(runtime['numpy_cpu_dispatch']))}


def checkpoint_key(files, runtime):
    digest = hashlib.sha256()
    for path in sorted(files):
        digest.update(str(path.relative_to(ROOT)).encode())
        digest.update(path.read_bytes())
    digest.update(b'\0NUMPY_EXECUTION_PROFILE\0')
    digest.update(json.dumps(numerical_profile(runtime), sort_keys=True, separators=(',', ':')).encode())
    return digest.hexdigest()[:16]


def save_execution_environment(directory, metadata):
    """Validate existing evidence before resuming; retain its original metadata."""
    path = Path(directory) / 'execution_environment.json'
    current = numerical_profile(metadata['runtime'])
    if path.exists():
        previous = json.loads(path.read_text())
        if (numerical_profile(previous.get('runtime')) != current or
                previous.get('NPY_DISABLE_CPU_FEATURES') != metadata['NPY_DISABLE_CPU_FEATURES']):
            raise ValueError('Profil numérique différent des sauvegardes existantes : nouveau calcul requis.')
        return
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(metadata, indent=2) + '\n')
    temporary.replace(path)


def inputs():
    names = ('panel_rendements.csv', 'meteo_dept_cultures.csv',
             'meteo_saisonnier_cultures.csv', 'meteo_advanced_cultures.csv',
             'sim_features.csv', 'soil_features.csv', 'prix_ble.csv',
             'hypotheses.yaml', 'cultures.yaml')
    files = [*sorted((ROOT / 'pipeline').glob('*.py')),
             *[ROOT / 'data' / name for name in names],
             ROOT / 'requirements-research.txt', Path(__file__).resolve(),
             ROOT / 'scripts/colab_multilegumes.py', ROOT / 'scripts/parallel_advanced.py']
    optional = ('sim_agri_features.csv', 'soil_features_crop.csv',
                'meteo_advanced_manifest.json', 'sim_manifest.json',
                'sim_agri_manifest.json', 'soil_manifest.json',
                'sim_rpg_features.csv', 'sim_rpg_manifest.json')
    files += [ROOT / 'data' / name for name in optional if (ROOT / 'data' / name).exists()]
    return sorted(set(files))


def prepare_rpg_alias(primary_archive, alias_data, secondary_archive):
    """Change only the weather weighting; preserve every numeric CSV byte."""
    alias_data = Path(alias_data)
    alias_data.mkdir(parents=True, exist_ok=True)
    for path in (ROOT / 'data').iterdir():
        if path.is_file():
            shutil.copy2(path, alias_data / path.name)
    sha = lambda value: hashlib.sha256(value).hexdigest()
    source = (ROOT / 'data/sim_rpg_features.csv').read_bytes()
    header, body = source.split(b'\n', 1)
    aliased = header.replace(b'_sim_rpg_', b'_sim_agri_') + b'\n' + body
    source_manifest = (ROOT / 'data/sim_rpg_manifest.json').read_bytes()
    with zipfile.ZipFile(primary_archive) as original:
        metadata = {
            'kind': 'rpg_weather_alias_v1',
            'source_file': 'data/sim_rpg_features.csv', 'source_sha256': sha(source),
            'source_manifest_file': 'data/sim_rpg_manifest.json',
            'source_manifest_sha256': sha(source_manifest),
            'alias_file': 'data/sim_agri_features.csv', 'alias_sha256': sha(aliased),
            'parent_alias_sha256': sha(original.read('data/sim_agri_features.csv')),
            'parent_manifest_sha256': sha(original.read('data/sim_agri_manifest.json')),
            'column_replace': {'from': '_sim_rpg_', 'to': '_sim_agri_'},
        }
        manifest_bytes = (json.dumps(metadata, ensure_ascii=False, indent=2) + '\n').encode()
        (alias_data / 'sim_agri_features.csv').write_bytes(aliased)
        (alias_data / 'sim_agri_manifest.json').write_bytes(manifest_bytes)
        with zipfile.ZipFile(secondary_archive, 'w', zipfile.ZIP_DEFLATED) as archive:
            for name in original.namelist():
                payload = (aliased if name == 'data/sim_agri_features.csv' else
                           manifest_bytes if name == 'data/sim_agri_manifest.json' else
                           original.read(name))
                archive.writestr(name, payload)


def main():
    os.environ['NPY_DISABLE_CPU_FEATURES'] = NUMPY_DISABLED_FEATURES
    drive = Path('/content/drive/MyDrive')
    if not drive.is_dir():
        raise RuntimeError('Monter Google Drive avant de lancer cette cellule.')
    files = inputs()
    runtime = {'NPY_DISABLE_CPU_FEATURES': NUMPY_DISABLED_FEATURES,
               'reason': 'Match the evaluated QRF leaf-sampling execution profile'}
    probe = ('import json, sys; sys.path.insert(0, "scripts"); '
             'from parallel_advanced import runtime_metadata; '
             'print(json.dumps(runtime_metadata()))')
    runtime['runtime'] = json.loads(subprocess.check_output(
        [sys.executable, '-c', probe], cwd=ROOT, text=True))
    key = checkpoint_key(files, runtime['runtime'])
    destination = drive / 'HackTheFork' / 'advanced' / key
    destination.mkdir(parents=True, exist_ok=True)
    primary, rpg, combined = [destination / name for name in ('primary', 'rpg', 'combined')]
    primary.mkdir(exist_ok=True)
    rpg.mkdir(exist_ok=True)
    for directory in (primary, rpg):
        save_execution_environment(directory, runtime)
    with zipfile.ZipFile(primary / 'executed-inputs.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT))
    print(f'Sauvegarde automatique : {destination}', flush=True)
    run_visible([sys.executable, '-u', str(ROOT / 'pipeline/benchmark_advanced.py'),
                 '--output', str(primary), '--samples', '20000', '--threads', '1'],
                primary, total=1700)
    alias_data = Path('/content') / ('advanced-rpg-data-' + key)
    prepare_rpg_alias(primary / 'executed-inputs.zip', alias_data, rpg / 'executed-inputs.zip')
    print('Météo pondérée par le RPG historique : deux expériences supplémentaires.', flush=True)
    run_visible([sys.executable, '-u', str(ROOT / 'pipeline/benchmark_advanced.py'),
                 '--data-dir', str(alias_data), '--output', str(rpg), '--samples', '20000',
                 '--threads', '1', '--models', 'qrf_agri_sparse', 'qrf_agri_dense'],
                rpg, total=100)
    subprocess.check_call([sys.executable, str(ROOT / 'pipeline/merge_advanced_runs.py'),
        '--primary', str(primary), '--rpg', str(rpg), '--output', str(combined)], cwd=ROOT)
    raw = combined / 'predictions.csv'
    print('Sélection passée des réglages, comparaison M0/QRF et sous-groupes…', flush=True)
    subprocess.check_call([sys.executable, str(ROOT / 'pipeline/analyze_advanced.py'),
        '--input', str(raw), '--output', str(destination / 'policies'),
        '--benchmark-manifest', str(combined / 'manifest.json')], cwd=ROOT)
    print('Résultats :', destination)


if __name__ == '__main__':
    main()
