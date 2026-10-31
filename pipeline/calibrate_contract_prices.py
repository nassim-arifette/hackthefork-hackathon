"""Calibrate the final business decision with earlier out-of-time price errors."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from benchmark_models import quantile_loss, summarize


def adjustment(past):
    """Q80 of log(required/offered), each year assigned equal total weight."""
    if past.empty or (past.price <= 0).any() or (past.realised_break_even <= 0).any():
        raise ValueError("Need positive, earlier out-of-time prices")
    errors = np.log(past.realised_break_even.to_numpy() / past.price.to_numpy())
    weight = 1 / past.groupby("year").year.transform("size").to_numpy()
    ix = np.argsort(errors)
    return float(np.exp(errors[ix][np.searchsorted(np.cumsum(weight[ix]) / weight.sum(), .8)]))


def calibrate(all_predictions):
    records, audit = [], []
    for kind, data in all_predictions.groupby("model"):
        if kind == "paired_history":
            continue
        for year in sorted(data.loc[data.year >= 2019, "year"].unique()):
            past = data[(data.year < year) & (data.year >= year - 3)]
            factor = adjustment(past)
            now = data[data.year == year].copy()
            # Recover observed lentil tonnes/ha from the stored shortfall when possible;
            # the caller supplies actual_lentil for rows that had no shortfall.
            now["price"] *= factor
            now["held"] = now.price >= now.realised_break_even
            now["contract_loss"] = quantile_loss(now.realised_break_even, now.price, .8)
            now["shortfall_eur_ha"] = np.maximum(0, now.realised_break_even - now.price) * now.actual_lentil
            now["model"] = kind + "_price_cal"
            records.append(now)
            audit.append({"model": kind, "year": int(year), "factor": factor,
                          "calibration_years": sorted(int(y) for y in past.year.unique())})
    return pd.concat(records, ignore_index=True), audit


if __name__ == "__main__":
    from common import DATA
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--warmup", type=Path, default=Path("experiments/price_calibration_warmup/predictions.csv"))
    p.add_argument("--predictions", type=Path, default=Path("experiments/model_benchmark_rolling/predictions.csv"))
    p.add_argument("--output", type=Path, default=Path("experiments/price_calibration"))
    args = p.parse_args()
    all_predictions = pd.concat([pd.read_csv(path, dtype={"dep": str}) for path in (args.warmup, args.predictions)])
    panel = pd.read_csv(DATA / "panel_rendements.csv", dtype={"dep": str})
    yields = panel[panel.culture == "lentille"][["dep", "annee", "rendement_qha"]]
    yields = yields.rename(columns={"annee": "year"}).assign(actual_lentil=lambda d: d.rendement_qha / 10)
    all_predictions = all_predictions.merge(yields[["dep", "year", "actual_lentil"]], on=["dep", "year"], validate="many_to_one")
    detail, audit = calibrate(all_predictions)
    args.output.mkdir(parents=True, exist_ok=True)
    detail.to_csv(args.output / "predictions.csv", index=False)
    result = {"summary": summarize(detail), "audit": audit,
              "method": "prequential_log_price_residual_q80_equal_year_weights_last_3_years"}
    (args.output / "results.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(pd.DataFrame(result["summary"]).to_string(index=False))
