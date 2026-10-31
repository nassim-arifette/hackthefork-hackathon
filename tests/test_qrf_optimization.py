import numpy as np
import pandas as pd

from benchmark_qrf_optimization import GRID, choose_from_past, dense_sample


def test_dense_sampler_preserves_quantiles_and_observed_bounds():
    q = np.array([.2 + GRID ** 2, 2 + GRID])
    values = dense_sample(q, np.array([0, 0, 0, 1]), np.array([0., .1, 1., .5]))
    np.testing.assert_allclose(values, [.2, .21, 1.2, 2.5])


def test_model_selection_cannot_see_decision_year_or_future():
    rows = pd.DataFrame([
        {'year': y, 'model': m, 'contract_loss': loss}
        for y in range(2016, 2026) for m, loss in [('qrf_sparse', 100), ('qrf_dense', 90)]
    ])
    chosen = choose_from_past(rows, 2019)
    changed = rows.copy()
    changed.loc[(changed.year >= 2019) & (changed.model == 'qrf_dense'), 'contract_loss'] = 1e12
    assert choose_from_past(changed, 2019) == chosen == 'qrf_dense'


def test_selection_assigns_each_past_year_equal_weight():
    rows = pd.DataFrame([
        *[{'year':2017,'model':'qrf_sparse','contract_loss':0} for _ in range(100)],
        {'year':2018,'model':'qrf_sparse','contract_loss':100},
        {'year':2017,'model':'qrf_dense','contract_loss':40},
        {'year':2018,'model':'qrf_dense','contract_loss':40},
    ])
    assert choose_from_past(rows, 2019) == 'qrf_dense'
