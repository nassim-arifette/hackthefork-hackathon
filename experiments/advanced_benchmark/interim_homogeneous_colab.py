"""Report completed crops only while other crop partitions continue running."""
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, '/content/hackthefork-final-analysis-code/pipeline')
import pandas as pd
from analyze_advanced import calibrate_compact, select_temporal, _summarize_many

primary = Path('/content/hackthefork-homogeneous-results')
rpg = Path('/content/hackthefork-rpg-homogeneous-results')
renames = {'qrf_agri_sparse': 'qrf_rpg_weather_sparse', 'qrf_agri_dense': 'qrf_rpg_weather_dense'}
tables, sources = [], {}
for crop in ('lentille', 'haricot', 'pois_chiche'):
    frames = []
    for base in (primary, rpg):
        directory = base / 'partitions' / crop
        if json.loads((directory / 'progress.json').read_text())['status'] != 'completed':
            raise RuntimeError(f'Crop is not complete: {directory}')
        path = directory / 'predictions.csv'
        frame = pd.read_csv(path, dtype={'dep': str}, float_precision='round_trip')
        if base == rpg:
            frame['model'] = frame.model.replace(renames)
        frames.append(frame)
        sources[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    raw = pd.concat(frames, ignore_index=True)
    policies = calibrate_compact(raw)
    selected, _, _ = select_temporal(policies)
    evaluated = pd.concat([policies[policies.year >= 2019], selected], ignore_index=True)
    tables.append(_summarize_many(evaluated, ['culture', 'contract', 'policy']))
summary = pd.concat(tables, ignore_index=True)
output = Path('/content/advanced-interim-homogeneous')
output.mkdir(exist_ok=True)
summary.to_csv(output / 'summary.csv', index=False)
(output / 'sources.json').write_text(json.dumps({'scope': 'three completed crops; full composition pending',
    'files_sha256': sources}, indent=2) + '\n')
for crop, group in summary[summary.contract == 'fixed'].groupby('culture'):
    print('\n', crop)
    columns = ['policy', 'n', 'held', 'realized_unit_cost', 'shortfall_eur_ha']
    print(group[group.held >= .8].sort_values('realized_unit_cost')[columns].head(7).to_string(index=False))
    print(group[group.policy.str.startswith('selector/') | group.policy.isin(['trend/cal95', 'qrf_seasonal/cal95'])][columns].to_string(index=False))
