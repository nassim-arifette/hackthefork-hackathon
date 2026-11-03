"""Produce department-level research prices; leave app exports unchanged."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from benchmark_models import RollingCalibrated, read_data, representatives, WEATHER
from benchmark_contract import DirectPrice, make_examples
from calibrate_contract_prices import adjustment
from common import IDF_AGRI, VOISINS_LENTILLE, hypotheses
from model import hyp_values, sample_quantile


def minimum_price(required_prices, tau=.8):
    return float(np.quantile(required_prices, tau, method="inverted_cdf"))


def scenarios(pool, lentil, wheat, dep, h, seed, n=20000):
    rng = np.random.default_rng(seed)
    ix = rng.integers(len(pool), size=n)
    yL = sample_quantile(lentil.predict(pool)[ix], rng.random(n)) * lentil.levels[dep] / 10
    yW = sample_quantile(wheat.predict(pool)[ix], rng.random(n)) * wheat.levels[dep] / 10
    pW = pool.prix_ble.to_numpy()[ix]
    required = (pW * yW - h["charges_ble"] + h["charges_lentille"] - h["bonus"]) / yL
    ps = minimum_price(required, h["tau"])
    # Calculate this from margins, independently of the ratio expression.
    margin_w = pW * yW - h["charges_ble"]
    margin_l = ps * yL - h["charges_lentille"] + h["bonus"]
    return {"p_star_eur_t_depart_ferme": ps,
            "simulated_success": float(np.mean(margin_l + 1e-10 >= margin_w)),
            "yield_lentil_mean_tha": float(yL.mean()),
            "yield_lentil_p10_tha": float(np.quantile(yL, .1)),
            "p_star_by_reliability": {str(t): minimum_price(required, t) for t in [.5, .6, .7, .8, .9]}}


def main(args):
    raw, weather = read_data()
    raw, weather = raw[raw.annee < args.year], weather[weather.annee < args.year]
    h = hyp_values(hypotheses())
    L, W = raw[raw.culture == "lentille"], raw[raw.culture == "ble"]
    # Same neighbouring-region transfer assumption as production, with duplicate groups removed.
    reps = representatives(L)
    neighbours = [d for d in VOISINS_LENTILLE if d in reps]
    if not neighbours:
        raise ValueError("No observed neighbouring lentil series")
    proxy = L[L.dep.isin(neighbours)].groupby("annee").rendement_qha.mean()
    levelL = float(proxy.mean())
    wheat = RollingCalibrated("linear").fit(W)
    outputs = {}
    for kind in ("linear", "lightgbm", "qrf"):
        lentil = RollingCalibrated(kind).fit(L)
        outputs[kind] = {}
        for dep in IDF_AGRI:
            lentil.levels.loc[dep] = levelL
            wheat.levels.loc[dep] = W[W.dep == dep].rendement_qha.mean()
            local_weather = weather[weather.dep == dep]
            lentil.features.centres.loc[dep] = local_weather[WEATHER].mean()
            wheat.features.centres.loc[dep] = local_weather[WEATHER].mean()
            pool = local_weather.copy()
            pool["annee"] = args.year
            outputs[kind][dep] = scenarios(pool, lentil, wheat, dep, h, seed=int(dep))
    examples = make_examples(raw, weather, h, final_year=args.year)
    train = examples[(examples.year < args.year) & examples.dep.isin(reps) & examples.target.notna()]
    direct = DirectPrice("qrf").fit(train)
    # Reconstruct the same out-of-time log-price errors used in the direct benchmark.
    calibration = []
    for year in range(args.year - 3, args.year):
        past_reps = representatives(L[L.annee < year])
        tr = examples[(examples.year < year) & examples.dep.isin(past_reps) & examples.target.notna()]
        te = examples[(examples.year == year) & examples.dep.isin(past_reps) & examples.target.notna()]
        m = DirectPrice("qrf").fit(tr)
        pred = te.baseline.to_numpy() * np.exp(m.predict_logratio(te))
        calibration.extend({"year": year, "price": float(p), "realised_break_even": float(t)}
                           for p, t in zip(pred, te.target))
    factor = adjustment(pd.DataFrame(calibration))
    outputs["direct_qrf"] = {}
    for dep in IDF_AGRI:
        fake = W[W.dep == dep].copy()
        fake["culture"] = "lentille"
        fake["rendement_qha"] = fake.annee.map(proxy)
        # Proxies are used for inference features only, never as training labels.
        features = make_examples(pd.concat([W, fake], ignore_index=True), weather, h, final_year=args.year)
        feature = features[(features.dep == dep) & (features.year == args.year)]
        price = float(feature.baseline.iloc[0] * np.exp(direct.predict_logratio(feature)[0]))
        outputs["direct_qrf"][dep] = {"raw_price_eur_t": price, "calibrated_price_eur_t": price * factor}
    result = {"year": args.year, "n_scenarios": 20000, "tau": h["tau"], "hypotheses": h,
              "weather_price_years": sorted(int(y) for y in weather.annee.unique()),
              "lentil_transfer_neighbours": neighbours, "direct_calibration_factor": factor,
              "models": outputs, "price_basis": "department_depart_ferme_transport_excluded",
              "direct_model_note": "Alternative estimator of Q80(R); not the Monte Carlo price.",
              "yield_transfer": "Neighbouring measured lentil yields, not parcel yield predictions."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--output", type=Path, default=Path("experiments/forecast_2026.json"))
    main(parser.parse_args())
