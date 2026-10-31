"""Attribute the legacy-to-research change, with common cases and random draws.

Legacy reproductions are diagnostics of the historical pipeline (including its
full-period grouping/weather preprocessing). Modern rolling forecasts use only
past observations. The four raw/expanded variants change interval use separately
for lentil and wheat; they are not four fitted model families.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd

from benchmark_checkpoint import atomic_json
from benchmark_models import (Predictor, RollingCalibrated, read_data,
                              representatives, quantile_loss)
from common import DATA, hypotheses
from model import (FEATURES, Calibrated, break_even_prices, hyp_values, levels,
                   load, p_star, pool_for, sample_quantile, with_rel)

ROOT = Path(__file__).resolve().parents[1]
KINDS = {'trend': 'M0', 'linear': 'M1', 'qrf': None}
FACTORS = ((False, False), (True, False), (False, True), (True, True))


def expand_quantiles(q, adjustment):
    q = np.array(q, copy=True)
    q[:, 0] -= adjustment
    q[:, 2] += adjustment
    return np.clip(q, .02, None)


def legacy_adjustment(scores):
    """Exactly the legacy signed, interpolated-level/higher order statistic."""
    scores = np.asarray(scores)
    return float(np.quantile(scores, min(1., .8 * (len(scores) + 1) / len(scores)),
                             method='higher'))


def simulate_arrays(qL, qW, prices, levelL, levelW, h, year, samples=20000):
    """Common RNG order matches the completed Colab benchmark."""
    rng = np.random.default_rng(42 + year * 100)
    ix = rng.integers(len(prices), size=samples)
    uL, uW = rng.random(samples), rng.random(samples)
    yL = sample_quantile(qL[ix], uL) * levelL / 10
    yW = sample_quantile(qW[ix], uW) * levelW / 10
    ratios = (prices[ix] * yW - h['charges_ble'] + h['charges_lentille'] - h['bonus']) / yL
    return float(np.quantile(ratios, h['tau'], method='inverted_cdf'))


def modern_preparation_legacy_calibration(base, history):
    """Hold final fit/normalization fixed and replace only calibration recipe.

    Like legacy Calibrated, the level and feature preprocessing includes the
    calibration years, while the provisional estimator excludes them. This is a
    diagnostic bridge, not a new recommended calibration protocol.
    """
    history = history[history.dep.isin(base.levels.index)]
    cal_years = sorted(history.annee.unique())[-3:]
    proper = history[~history.annee.isin(cal_years)]
    cal = history[history.annee.isin(cal_years)]
    y = proper.rendement_qha.to_numpy() / base.levels.reindex(proper.dep).to_numpy()
    provisional = Predictor(base.kind).fit(base.features.transform(proper), y)
    q = provisional.predict(base.features.transform(cal))
    yc = cal.rendement_qha.to_numpy() / base.levels.reindex(cal.dep).to_numpy()
    return legacy_adjustment(np.maximum(q[:, 0] - yc, yc - q[:, 2]))


def metrics(rows):
    results = []
    for (protocol, model), d in rows.groupby(['protocol', 'model']):
        for subset, s in [('all', d), ('old133', d[d.old_cohort])]:
            if s.empty:
                continue
            annual = s.groupby('year')[['contract_loss', 'held', 'shortfall_eur_ha']].mean()
            results.append({'protocol': protocol, 'model': model, 'cohort': subset,
                'n': len(s), 'years': int(s.year.nunique()), 'held': float(s.held.mean()),
                'held_year_mean': float(annual.held.mean()),
                'contract_loss': float(annual.contract_loss.mean()),
                'median_price': float(s.price.median()),
                'shortfall_eur_ha': float(annual.shortfall_eur_ha.mean())})
    return results


def run(args):
    args.output.mkdir(parents=True, exist_ok=True)
    files = [Path(__file__), ROOT/'pipeline/model.py', ROOT/'pipeline/benchmark_models.py',
             ROOT/'pipeline/common.py', ROOT/'pipeline/01_agreste.py', args.legacy_reference,
             args.modern_reference] + [DATA/n for n in
             ['panel_rendements.csv', 'meteo_dept.csv', 'prix_ble.csv', 'hypotheses.yaml']]
    spec = {'samples': args.samples, 'seed': 42,
        'files': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        'packages': {n: importlib.metadata.version(n) for n in
                     ['numpy', 'pandas', 'scipy', 'scikit-learn', 'quantile-forest']}}
    signature = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()
    manifest = args.output/'manifest.json'
    if manifest.exists() and json.loads(manifest.read_text())['signature'] != signature:
        raise ValueError('Code, data or options changed: choose a new output directory')
    atomic_json(manifest, {'signature': signature, 'spec': spec})
    original = pd.DataFrame(json.loads(args.legacy_reference.read_text())['detail'])
    old_keys = set(zip(original.annee, original.dep))
    reference = pd.read_csv(args.modern_reference, dtype={'dep': str})
    old_df, old_weather = load()
    raw, weather = read_data()
    L, W = raw[raw.culture == 'lentille'], raw[raw.culture == 'ble']
    oldL, oldW = old_df[old_df.culture == 'lentille'], old_df[old_df.culture == 'ble']
    # Same complete data with legacy fixed-climatology columns, for grouping bridge.
    old_features = old_weather[['dep', 'annee', *FEATURES]]
    legacy_weather_raw = raw.merge(old_features, on=['dep', 'annee'], validate='many_to_one')
    h = hyp_values(hypotheses())
    all_rows, audits, diagnostics = [], [], []
    started = time.monotonic()

    def row_for(year, dep, kind, protocol, price, observation, realW, qL, qW):
        yL, yW = observation.rendement_qha/10, realW.loc[dep, 'rendement_qha']/10
        realised = (observation.prix_ble*yW-h['charges_ble']+h['charges_lentille']-h['bonus'])/yL
        return {'year': int(year), 'dep': dep, 'model': kind, 'protocol': protocol,
            'price': float(price), 'realised_break_even': float(realised),
            'held': bool(price >= realised), 'contract_loss': float(quantile_loss(realised, price, .8)),
            'shortfall_eur_ha': float(max(0., realised-price)*yL),
            'actual_lentil': float(yL), 'actual_wheat': float(yW),
            'actual_wheat_price': float(observation.prix_ble),
            'qhat_lentil': float(qL), 'qhat_wheat': float(qW),
            'old_cohort': (int(year), dep) in old_keys}

    for year in range(2016, 2026):
        checkpoint = args.output/f'year-{year}.json'
        if checkpoint.exists():
            saved = json.loads(checkpoint.read_text())
            assert saved['signature'] == signature
            all_rows.extend(saved['rows']); audits.extend(saved['audit']); diagnostics.extend(saved['diagnostics'])
            print(f'Protocol {year}: resumed', flush=True)
            continue
        rows, yearly_audit, checks = [], [], []
        histL, histW = L[L.annee < year], W[W.annee < year]
        modernW = RollingCalibrated('linear').fit(histW)
        models = {kind: RollingCalibrated(kind).fit(histL) for kind in KINDS}
        common_deps = set(modernW.levels.index) & set(models['trend'].levels.index)
        test = L[(L.annee == year) & L.dep.isin(common_deps)].sort_values('dep')
        realW = W[W.annee == year].set_index('dep')
        test = test[test.dep.isin(realW.index)]
        if year >= 2019:
            assert set(test.dep) == set(reference.loc[reference.year == year, 'dep'])
        for kind, model in models.items():
            assert set(test.dep).issubset(model.levels.index)
            yearly_audit.append({'year': year, 'model': kind, 'training_max': int(histL.annee.max()),
                'n_train': model.n_proper, 'n_test': len(test),
                'calibration': model.calibration_audit, 'qhat_lentil': model.qhat,
                'qhat_wheat': modernW.qhat})
        # Factorial changes only simulation use of calibrated interval bounds.
        for _, obs in test.iterrows():
            pool = weather[(weather.dep == obs.dep) & (weather.annee < year)].copy()
            pool['annee'] = year
            rawW = modernW.predict_quantiles(pool)
            qWs = {False: rawW, True: expand_quantiles(rawW, modernW.qhat)}
            for kind, model in models.items():
                rawL = model.predict_quantiles(pool)
                qLs = {False: rawL, True: expand_quantiles(rawL, model.qhat)}
                for expandL, expandW in FACTORS:
                    protocol = f"modern_{'expanded' if expandL else 'raw'}_{'expanded' if expandW else 'raw'}"
                    price = simulate_arrays(qLs[expandL], qWs[expandW], pool.prix_ble.to_numpy(),
                        model.levels[obs.dep], modernW.levels[obs.dep], h, year, args.samples)
                    rows.append(row_for(year, obs.dep, kind, protocol, price, obs, realW,
                                        model.qhat if expandL else 0., modernW.qhat if expandW else 0.))

        if year >= 2019:
            # Bridge: modern preparation/final estimator, legacy calibration only.
            qhatW = modern_preparation_legacy_calibration(modernW, histW)
            qhatLs = {kind: modern_preparation_legacy_calibration(model, histL)
                      for kind, model in models.items()}
            for _, obs in test.iterrows():
                pool = weather[(weather.dep == obs.dep) & (weather.annee < year)].copy()
                pool['annee'] = year
                qW = expand_quantiles(modernW.predict_quantiles(pool), qhatW)
                for kind, model in models.items():
                    qL = expand_quantiles(model.predict_quantiles(pool), qhatLs[kind])
                    price = simulate_arrays(qL, qW, pool.prix_ble.to_numpy(), model.levels[obs.dep],
                                            modernW.levels[obs.dep], h, year, args.samples)
                    rows.append(row_for(year, obs.dep, kind, 'modern_prep_legacy_cal', price,
                                        obs, realW, qhatLs[kind], qhatW))

            # Bridge: replace global grouping with usable, past-only grouping;
            # retain legacy fixed weather features and calibration/refit recipe.
            group_history = legacy_weather_raw[legacy_weather_raw.annee < year]
            bridge_models, bridge_levels = {}, {}
            for culture, keys in [('ble', ['linear']), ('lentille', ['trend', 'linear'])]:
                train = group_history[group_history.culture == culture]
                train = train[train.dep.isin(representatives(train))]
                counts = train.groupby('dep').size()
                train = train[train.dep.isin(counts[counts >= 3].index)]
                lev = levels(train)
                for kind in keys:
                    bridge_models[culture, kind] = Calibrated(KINDS[kind]).fit(with_rel(train, lev))
                    bridge_levels[culture, kind] = lev
            for _, obs in test.iterrows():
                pool = pool_for(old_weather, obs.dep, range(2010, year), year)
                bW = bridge_models['ble', 'linear']
                for kind in ['trend', 'linear']:
                    bL = bridge_models['lentille', kind]
                    price = simulate_arrays(bL.predict(pool), bW.predict(pool), pool.prix_ble.to_numpy(),
                        bridge_levels['lentille', kind][obs.dep], bridge_levels['ble', 'linear'][obs.dep],
                        h, year, args.samples)
                    rows.append(row_for(year, obs.dep, kind, 'past_groups_legacy_weather_cal', price,
                                        obs, realW, bL.qhat, bW.qhat))

            # Exact historical pipeline: preserve the legacy test iteration order
            # because it contributes to its department-specific random seed.
            trL, trW = oldL[oldL.annee < year], oldW[oldW.annee < year]
            counts = trL.groupby('dep').size()
            levL = levels(trL[trL.dep.isin(counts[counts >= 3].index)])
            levW = levels(trW)
            trL, trW = with_rel(trL, levL), with_rel(trW, levW)
            old_models = {kind: Calibrated(KINDS[kind]).fit(trL) for kind in ['trend', 'linear']}
            old_wheat = Calibrated('M1').fit(trW)
            te = with_rel(oldL[oldL.annee == year], levL)
            te = te[te.dep.isin(levW.index)]
            old_realW = oldW[oldW.annee == year].set_index('dep')
            for i, (_, obs) in enumerate(te.iterrows()):
                if obs.dep not in old_realW.index:
                    continue
                pool = pool_for(old_weather, obs.dep, range(2010, year), year)
                for kind, model in old_models.items():
                    ratios, _, _ = break_even_prices(pool, model, old_wheat, levL[obs.dep], levW[obs.dep],
                                                    h, n=6000, seed=year*100+i)
                    exact = p_star(ratios, h['tau'])
                    rows.append(row_for(year, obs.dep, kind, 'legacy_exact', exact, obs, old_realW,
                                        model.qhat, old_wheat.qhat))
                    aligned = simulate_arrays(model.predict(pool), old_wheat.predict(pool),
                        pool.prix_ble.to_numpy(), levL[obs.dep], levW[obs.dep], h, year, args.samples)
                    rows.append(row_for(year, obs.dep, kind, 'legacy_mc_aligned', aligned, obs,
                                        old_realW, model.qhat, old_wheat.qhat))
                    prior = original[(original.annee == year) & (original.dep == obs.dep)].iloc[0]
                    price_col, held_col = ('p_star_M0', 'tenu_M0') if kind == 'trend' else ('p_star', 'tenu')
                    checks.append({'year': year, 'dep': obs.dep, 'model': kind,
                        'rounded_price_difference': int(round(exact)-prior[price_col]),
                        'held_matches_original': rows[-2]['held'] == bool(prior[held_col])})

        atomic_json(checkpoint, {'signature': signature, 'rows': rows,
                                'audit': yearly_audit, 'diagnostics': checks})
        all_rows.extend(rows); audits.extend(yearly_audit); diagnostics.extend(checks)
        pd.DataFrame(all_rows).to_csv(args.output/'predictions_partial.csv', index=False)
        atomic_json(args.output/'progress.json', {'completed': year-2015, 'total': 10,
                                                 'year': year, 'status': 'running'})
        print(f'Protocol {year}: {year-2015}/10 saved, {len(rows)} predictions', flush=True)

    all_detail = pd.DataFrame(all_rows)
    detail = all_detail[all_detail.year >= 2019]
    assert not all_detail.duplicated(['year', 'dep', 'model', 'protocol']).any()
    check = pd.DataFrame(diagnostics)
    assert len(check) == 266 and check.held_matches_original.all(), 'Legacy held reproduction failed'
    assert check.rounded_price_difference.abs().max() <= 1, 'Legacy price reproduction failed'
    modern = detail[detail.protocol == 'modern_raw_raw'].merge(
        reference[reference.model.isin(KINDS)], on=['year', 'dep', 'model'],
        suffixes=('_new', '_reference'), validate='one_to_one')
    assert len(modern) == 576
    max_delta = float((modern.price_new-modern.price_reference).abs().max())
    assert max_delta < 1e-7, f'Modern baseline differs: {max_delta}'
    all_detail.to_csv(args.output/'predictions_with_warmup.csv', index=False)
    detail.to_csv(args.output/'predictions.csv', index=False)
    detail.groupby(['protocol', 'model', 'year'])[['price', 'held', 'contract_loss', 'shortfall_eur_ha']].mean().reset_index().to_csv(args.output/'annual_metrics.csv', index=False)
    check.to_csv(args.output/'legacy_reproduction.csv', index=False)
    result = {'spec': spec, 'summary': metrics(detail), 'audit': audits,
        'legacy_max_rounded_price_difference': int(check.rounded_price_difference.abs().max()),
        'legacy_held_all_match': bool(check.held_matches_original.all()),
        'modern_raw_max_price_difference': max_delta,
        'seconds': time.monotonic()-started,
        'interpretation': 'Sequential attribution is path-dependent. The raw/expanded 2x2 factorial holds fitted models and random draws fixed. Legacy and bridge steps are diagnostics, not deployment candidates.'}
    atomic_json(args.output/'results.json', result)
    atomic_json(args.output/'progress.json', {'completed': 10, 'total': 10, 'status': 'complete'})
    print(pd.DataFrame(result['summary']).to_string(index=False), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--legacy-reference', type=Path, default=DATA/'backtest.json')
    p.add_argument('--modern-reference', type=Path,
                   default=ROOT/'experiments/colab_2026_10_31/colab_benchmark/predictions.csv')
    p.add_argument('--output', type=Path, default=ROOT/'experiments/protocol_attribution')
    p.add_argument('--samples', type=int, default=20000)
    run(p.parse_args())
