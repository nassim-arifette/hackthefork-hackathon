"""Temporal leave-one-region-out test of lentil transfer to an unmeasured area.

The held-out region supplies historical weather and wheat, but no lentil level or
lentil fitting rows. Four climate analogues supply the lentil level. Historical
held-out lentil labels are consulted only to block duplicated source series from
leaking across the region split, never as fitting rows or donor-selection inputs.
"""
import argparse
import hashlib
import importlib
import importlib.metadata
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd

from benchmark_checkpoint import atomic_json
from benchmark_models import RollingCalibrated, read_data, quantile_loss, summarize
from common import DATA, hypotheses
from model import WEATHER, hyp_values, sample_quantile

ROOT = Path(__file__).resolve().parents[1]
SEED = 42


def region_training(history, held_region, year):
    """Exclude the region and all past duplicate groups touching that region."""
    history = history[history.annee < year].copy()
    flagged = importlib.import_module('01_agreste').flag_duplicates(history)
    blocked_groups = set(flagged.loc[flagged.region == held_region, 'serie_groupe'])
    outside = flagged.region != held_region
    duplicate = outside & flagged.serie_groupe.isin(blocked_groups)
    excluded = sorted(flagged.loc[duplicate, 'dep'].unique())
    return flagged[outside & ~duplicate].copy(), excluded


def climate_analogues(weather, donor_levels, target_dep, year, k=4):
    """Choose donors using past climate alone; target lentil labels are absent."""
    past = weather[weather.annee < year]
    means = past.groupby('dep')[WEATHER].mean()
    candidates = sorted(set(donor_levels.index) & set(means.index) - {target_dep})
    if len(candidates) < k or target_dep not in means.index:
        raise ValueError('Insufficient climate analogues')
    climate = means.loc[candidates]
    scale = climate.std().replace(0., 1.).fillna(1.)
    distance = ((climate - means.loc[target_dep]) / scale).pow(2).mean(axis=1).pow(.5)
    ranked = distance.rename('distance').reset_index().sort_values(['distance', 'dep'])
    selected = ranked.iloc[:k]
    donors = selected.dep.tolist()
    level = float(donor_levels.loc[donors].mean())
    return level, donors, selected.distance.to_list(), means.loc[target_dep]


def simulate_transfer(pool, lentil, wheat, dep, level_lentil, h, year, samples):
    rng = np.random.default_rng(SEED + year * 100)
    indexes = rng.integers(len(pool), size=samples)
    u_lentil, u_wheat = rng.random(samples), rng.random(samples)
    y_lentil = sample_quantile(lentil.predict_quantiles(pool)[indexes], u_lentil) * level_lentil / 10
    y_wheat = sample_quantile(wheat.predict_quantiles(pool)[indexes], u_wheat) * wheat.levels[dep] / 10
    required = (pool.prix_ble.to_numpy()[indexes] * y_wheat - h['charges_ble'] +
                h['charges_lentille'] - h['bonus']) / y_lentil
    price = float(np.quantile(required, h['tau'], method='inverted_cdf'))
    return price, float(np.mean(price >= required))


def run(args):
    started = time.monotonic()
    args.output.mkdir(parents=True, exist_ok=True)
    files = [Path(__file__), ROOT/'pipeline/benchmark_models.py', ROOT/'pipeline/model.py',
             ROOT/'pipeline/01_agreste.py', ROOT/'pipeline/common.py', args.reference]
    files += [DATA/name for name in ('panel_rendements.csv', 'meteo_dept.csv', 'prix_ble.csv', 'hypotheses.yaml')]
    spec = {'year_start': 2019, 'year_end': 2025, 'models': ['trend', 'qrf'], 'samples': args.samples,
            'seed': SEED, 'analogue_count': 4, 'distribution': 'raw_3_quantiles',
            'files': {str(p.name): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
            'packages': {name: importlib.metadata.version(name) for name in
                         ('numpy', 'pandas', 'scikit-learn', 'quantile-forest')}}
    signature = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()
    manifest = args.output/'manifest.json'
    if manifest.exists() and json.loads(manifest.read_text())['signature'] != signature:
        raise ValueError('Changed source/data/options: use a new output directory')
    atomic_json(manifest, {'signature': signature, 'spec': spec})
    raw, weather = read_data()
    L, W = raw[raw.culture == 'lentille'], raw[raw.culture == 'ble']
    regions = sorted(L.region.unique())
    h = hyp_values(hypotheses())
    reference = pd.read_csv(args.reference, dtype={'dep': str})
    cohort = reference[reference.model == 'qrf'][['year', 'dep']].copy()
    assert len(cohort) == 192 and not cohort.duplicated().any()
    rows, audits = [], []
    total = len(regions) * 7
    completed = 0
    for year in range(2019, 2026):
        past_lentil = L[L.annee < year]
        wheat = RollingCalibrated('linear', SEED).fit_base(W[W.annee < year])
        wanted = set(cohort.loc[cohort.year == year, 'dep'])
        test = L[(L.annee == year) & L.dep.isin(wanted)].sort_values('dep')
        real_wheat = W[W.annee == year].set_index('dep')
        for region_number, region in enumerate(regions):
            checkpoint = args.output/f'year-{year}-region-{region_number}.json'
            if checkpoint.exists():
                saved = json.loads(checkpoint.read_text())
                assert saved['signature'] == signature
                rows.extend(saved['rows']); audits.append(saved['audit'])
                completed += 1
                continue
            training, cross_region_duplicates = region_training(past_lentil, region, year)
            fitted = {kind: RollingCalibrated(kind, SEED).fit_base(training) for kind in ('trend', 'qrf')}
            donor_levels = fitted['trend'].levels.copy()
            assert set(donor_levels.index) == set(fitted['qrf'].levels.index)
            target = test[test.region == region]
            local_rows, donors_audit = [], []
            for _, row in target.iterrows():
                level, donors, distances, climate_centre = climate_analogues(
                    weather, donor_levels, row.dep, year)
                assert not training[training.dep.isin(donors)].region.eq(region).any()
                pool = weather[(weather.dep == row.dep) & (weather.annee < year)].copy()
                pool['annee'] = year
                realised = (row.prix_ble * real_wheat.loc[row.dep, 'rendement_qha'] / 10 -
                            h['charges_ble'] + h['charges_lentille'] - h['bonus']) / (row.rendement_qha / 10)
                for kind, model in fitted.items():
                    model.features.centres.loc[row.dep] = climate_centre
                    price, simulated_held = simulate_transfer(pool, model, wheat, row.dep,
                                                              level, h, year, args.samples)
                    local_rows.append({'year': year, 'dep': row.dep, 'region': region,
                        'model': f'transfer_{kind}', 'price': price,
                        'realised_break_even': float(realised), 'held': bool(price >= realised),
                        'contract_loss': float(quantile_loss(realised, price, .8)),
                        'shortfall_eur_ha': float(max(0., realised-price)*row.rendement_qha/10),
                        'simulated_held': simulated_held, 'transferred_level_qha': level,
                        'donors': '|'.join(donors), 'pinball': None, 'coverage': None, 'width': None})
                donors_audit.append({'dep': row.dep, 'donors': donors, 'climate_distance': distances,
                                     'transferred_level_qha': level})
            audit = {'year': year, 'excluded_region': region, 'train_max': int(training.annee.max()),
                     'training_regions': sorted(training.region.unique()),
                     'n_train': fitted['trend'].n_proper, 'n_test': len(target),
                     'training_departments': sorted(donor_levels.index),
                     'cross_region_duplicate_departments_removed': cross_region_duplicates,
                     'donors': donors_audit}
            assert region not in audit['training_regions'] and audit['train_max'] < year
            rows.extend(local_rows); audits.append(audit)
            atomic_json(checkpoint, {'signature': signature, 'rows': local_rows, 'audit': audit})
            pd.DataFrame(rows).to_csv(args.output/'predictions_partial.csv', index=False)
            completed += 1
            atomic_json(args.output/'progress.json', {'completed': completed, 'total': total,
                                                      'year': year, 'region': region, 'status': 'running'})
            print(f'Transfer {completed}/{total}: {year} {region}, {len(target)} departments', flush=True)
    detail = pd.DataFrame(rows)
    for name, part in detail.groupby('model'):
        assert len(part) == 192 and set(zip(part.year, part.dep)) == set(zip(cohort.year, cohort.dep)), name
    baseline = reference[reference.model.isin(['trend', 'qrf'])].copy()
    baseline['model'] = 'local_history_' + baseline.model
    baseline['region'] = baseline.dep.map(L.drop_duplicates('dep').set_index('dep').region)
    detail = pd.concat([detail, baseline], ignore_index=True)
    assert np.allclose(detail.groupby(['year', 'dep']).realised_break_even.min(),
                       detail.groupby(['year', 'dep']).realised_break_even.max())
    detail.to_csv(args.output/'predictions.csv', index=False)
    detail.groupby(['model', 'year'])[['held', 'price', 'contract_loss', 'shortfall_eur_ha']].mean().reset_index().to_csv(
        args.output/'annual_metrics.csv', index=False)
    regional = []
    for region, part in detail.groupby('region'):
        regional.extend(dict(region=region, **r) for r in summarize(part))
    pd.DataFrame(regional).to_csv(args.output/'regional_metrics.csv', index=False)
    result = {'spec': spec, 'summary': summarize(detail), 'regional_summary': regional, 'audit': audits,
              'seconds': time.monotonic()-started, 'cohort_size': 192,
              'purpose': 'Pseudo-unobserved region transfer stress test; not a validation in Ile-de-France itself.',
              'target_lentil_usage': 'No fitting rows, level, or analogue ranking. Past labels only exclude duplicated source series.',
              'selection': 'All seven observed production regions; no subgroup chosen using model scores.'}
    atomic_json(args.output/'results.json', result)
    atomic_json(args.output/'progress.json', {'completed': total, 'total': total, 'status': 'complete'})
    print(pd.DataFrame(result['summary']).to_string(index=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, default=ROOT/'experiments/colab_2026_10_31/colab_benchmark/predictions.csv')
    parser.add_argument('--output', type=Path, default=ROOT/'experiments/spatial_transfer')
    parser.add_argument('--samples', type=int, default=20000)
    run(parser.parse_args())
