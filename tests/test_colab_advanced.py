"""The notebook must archive exactly the RPG weather bytes it executes."""
import hashlib
import importlib.util
import json
from pathlib import Path
from zipfile import ZipFile


def test_notebook_rpg_alias_preserves_body_and_archived_source(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location('colab_advanced',
        Path(__file__).parents[1] / 'scripts/colab_advanced.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
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
