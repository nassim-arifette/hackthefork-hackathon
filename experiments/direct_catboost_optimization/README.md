# Direct-Q80 CatBoost experiment

Four fixed candidates, trained directly against the Q80 price loss. The residual target subtracts the known pre-season baseline before fitting and adds it back at prediction. Each training year has equal total weight.

The deployable experimental policy selects using only the preceding three out-of-time years, starting with 2016–18 for the 2019 decision. No model is chosen using the complete 2019–25 evaluation. All reported models share the same 192 department-year rows.

| Model | Year-equal Q80 loss (€/t) | Held (rows) | Median price (€/t) |
|---|---:|---:|---:|
| qrf | 209.49 | 63.0% | 1158.57 |
| direct_cb_price_d2 | 230.75 | 67.7% | 1324.14 |
| direct_cb_price_d3 | 236.59 | 67.2% | 1278.27 |
| direct_cb_residual_d3 | 243.52 | 67.2% | 1332.48 |
| direct_cb_past_selected | 247.44 | 66.7% | 1364.39 |
| direct_cb_residual_d2 | 252.59 | 69.3% | 1393.09 |
| direct_qrf | 280.91 | 78.1% | 1510.61 |
| direct_qrf_cal | 316.49 | 82.3% | 1743.55 |

Loss penalizes a price below realised break-even four times as much as an equal overshoot. Lower price alone is not an improvement. Held means the proposed farmgate price meets realised break-even.

Only seven calendar years are evaluated, and departments are correlated. These are research results; production exports are unchanged.

Reproduce from repository root (CatBoost and existing benchmark dependencies installed):

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python -u pipeline/benchmark_direct_catboost.py
```

`results.json` records parameters, input/script hashes, package versions, training-year audits and every past-only selection score. `oof_predictions.csv` includes the warmup years; `predictions.csv` and `annual_metrics.csv` include the comparison cohort and original baselines.

Executed directly in the existing Google Colab notebook runtime on 2026-10-31, using CPU with one thread. Results were downloaded and checked against the executed script hash, all 40 training cutoffs, all seven selection decisions, and the fixed comparison cohort. Three selector/cohort unit tests pass.
