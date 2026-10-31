"""Publish lossless tables and compact policy decisions without duplicate inputs.

Every policy row joins the benchmark inputs on culture/contract/year/dep/model.
The detailed analysis still emits its standalone full observation table locally.
"""
import gzip
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def compress(path):
    with gzip.GzipFile(filename=str(path) + '.gz', mode='wb', mtime=0) as out:
        out.write(path.read_bytes())


def main():
    for name in ('multilegumes_pre_pr3', 'multilegumes_pr3_recalculation', 'multilegumes_benchmark'):
        compress(ROOT / 'experiments' / name / 'predictions.csv')
    output = ROOT / 'experiments/multilegumes_policies'
    for name in ('summary.csv', 'subgroup_comparisons.csv'):
        compress(output / name)
    policies = pd.read_csv(output / 'policy_predictions.csv.gz', dtype={'dep': str},
                           float_precision='round_trip', low_memory=False)
    columns = [
        'culture', 'contract', 'year', 'dep', 'model', 'policy',
        'coefficient', 'raw_coefficient', 'calibration', 'calibration_quantile',
        'calibration_correction', 'calibration_n', 'calibration_max_year',
        'product_eligible', 'selected_policy', 'selector_past_max_year',
        'held',
    ]
    columns = [column for column in columns if column in policies]
    compact = policies[columns]
    if compact.duplicated(['culture', 'contract', 'year', 'dep', 'policy']).any():
        raise ValueError('Policy observation keys are not unique')
    compact.to_csv(output / 'policy_decisions.csv.gz', index=False,
                   compression={'method': 'gzip', 'mtime': 0})
    # Normalize generated text formatting without changing plot paths or CSV values.
    for path in output.glob('*.svg'):
        path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines()) + '\n')
    site_csv = ROOT / 'experiments/sites/results.csv'
    site_csv.write_text(site_csv.read_text())
    print(f'{len(compact)} policy decisions, {len(columns)} columns')


if __name__ == '__main__':
    main()
