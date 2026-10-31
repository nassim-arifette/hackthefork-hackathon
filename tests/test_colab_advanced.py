"""The notebook must archive exactly the RPG weather bytes it executes."""
import hashlib
import importlib.util
import json
from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile

import pytest


def load_notebook_runner():
    spec = importlib.util.spec_from_file_location('colab_advanced',
        Path(__file__).parents[1] / 'scripts/colab_advanced.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def runtime_fixture():
    return {'numpy_version': '2.3.5', 'numpy_dispatch_override': 'AVX512F,AVX512_SKX',
        'numpy_cpu_features': {'SSE2': True, 'AVX2': True, 'AVX512F': False, 'AVX512_SKX': False},
        'numpy_cpu_baseline': ['SSE', 'SSE2'], 'numpy_cpu_dispatch': ['AVX2', 'AVX512_SKX'],
        'machine': 'x86_64', 'logical_cpus': 2, 'platform': 'Linux', 'python': '3.13.16'}


def test_checkpoint_key_ignores_core_count_and_cpu_brand(tmp_path, monkeypatch):
    module = load_notebook_runner()
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    source = tmp_path / 'frozen.py'
    source.write_text('unchanged source\n')
    before = runtime_fixture()
    after = deepcopy(before)
    after.update(logical_cpus=12, machine='different_cpu_brand')
    assert module.checkpoint_key([source], before) == module.checkpoint_key([source], after)


@pytest.mark.parametrize('field', ['numpy_cpu_features', 'numpy_dispatch_override', 'numpy_version'])
def test_checkpoint_key_changes_with_numerical_execution_profile(tmp_path, monkeypatch, field):
    module = load_notebook_runner()
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    source = tmp_path / 'frozen.py'
    source.write_text('unchanged source\n')
    before = runtime_fixture()
    after = deepcopy(before)
    if field == 'numpy_cpu_features':
        after[field]['AVX512F'] = True
    elif field == 'numpy_dispatch_override':
        after[field] = None
    else:
        after[field] = 'other_version'
    assert module.checkpoint_key([source], before) != module.checkpoint_key([source], after)


def test_existing_execution_evidence_is_preserved_and_mismatch_cannot_overwrite_it(tmp_path):
    module = load_notebook_runner()
    metadata = {'NPY_DISABLE_CPU_FEATURES': 'AVX512F,AVX512_SKX', 'runtime': runtime_fixture()}
    module.save_execution_environment(tmp_path, metadata)
    path = tmp_path / 'execution_environment.json'
    original = path.read_bytes()
    next_attempt = deepcopy(metadata)
    next_attempt['runtime']['logical_cpus'] = 12
    module.save_execution_environment(tmp_path, next_attempt)
    assert path.read_bytes() == original
    next_attempt['runtime']['numpy_cpu_features']['AVX512F'] = True
    with pytest.raises(ValueError, match='Profil numérique différent'):
        module.save_execution_environment(tmp_path, next_attempt)
    assert path.read_bytes() == original


def test_notebook_rpg_alias_preserves_body_and_archived_source(tmp_path, monkeypatch):
    module = load_notebook_runner()
    root = tmp_path / 'source'
    (root / 'data').mkdir(parents=True)
    rpg = b'dep,annee,lentille_sim_rpg_swi\n77,2019,0.12345678901234567\n'
    clc = b'dep,annee,lentille_sim_agri_swi\n77,2019,0.6\n'
    (root / 'data/sim_rpg_features.csv').write_bytes(rpg)
    (root / 'data/sim_rpg_manifest.json').write_text('{"source":"RPG2015"}\n')
    (root / 'data/sim_agri_features.csv').write_bytes(clc)
    (root / 'data/sim_agri_manifest.json').write_text('{"source":"CLC2012"}\n')
    monkeypatch.setattr(module, 'ROOT', root)
    original = tmp_path / 'primary.zip'
    with ZipFile(original, 'w') as z:
        for path in (root / 'data').iterdir():
            z.write(path, path.relative_to(root))
        z.writestr('pipeline/frozen.py', 'UNCHANGED\n')
    output = tmp_path / 'rpg.zip'
    module.prepare_rpg_alias(original, tmp_path / 'alias', output)
    with ZipFile(output) as z:
        alias = z.read('data/sim_agri_features.csv')
        manifest = json.loads(z.read('data/sim_agri_manifest.json'))
        assert alias.split(b'\n', 1)[1] == rpg.split(b'\n', 1)[1]
        assert alias == (tmp_path / 'alias/sim_agri_features.csv').read_bytes()
        assert z.read('data/sim_rpg_features.csv') == rpg
        assert z.read('pipeline/frozen.py') == b'UNCHANGED\n'
        assert manifest['alias_sha256'] == hashlib.sha256(alias).hexdigest()
        assert manifest['parent_alias_sha256'] == hashlib.sha256(clc).hexdigest()
