"""Exploration, hors pipeline : régularisation de la régression quantile choisie en validation interne,
et ensemble de modèles. Résultat (backtest 2019-2025) : plus précis que la tendance seule, mais
moins bien calibré (couverture autour de 71 %), donc non retenu. Lancer depuis pipeline/ :
  python explore_regularisation.py
"""
import sys
sys.path.insert(0, ".")
import numpy as np
from sklearn.linear_model import QuantileRegressor
from common import TEST_YEARS
from model import (FEATURES, QUANTILES, MODELS, Baseline, GBMQuantile, levels, load, pinball, with_rel)

df, meteo = load()
L = df[df.culture == "lentille"]

def fit_lq(d, alpha):
    return [QuantileRegressor(quantile=q, alpha=alpha, solver="highs").fit(d[FEATURES], d.rel) for q in QUANTILES]
def pred_lq(ms, X):
    return np.sort(np.column_stack([m.predict(X[FEATURES]) for m in ms]), axis=1)

def calibrate(pred_fn, fit_fn, d):
    yrs = sorted(d.annee.unique()); cal = yrs[-3:]
    pr, ca = d[~d.annee.isin(cal)], d[d.annee.isin(cal)]
    m = fit_fn(pr); q = pred_fn(m, ca)
    sc = np.maximum(q[:, 0] - ca.rel, ca.rel - q[:, 2]); n = len(sc)
    qhat = float(np.quantile(sc, min(1, 0.8 * (n + 1) / n), method="higher"))
    mf = fit_fn(d)
    return lambda X: (lambda q: np.clip(q + np.array([-qhat, 0, qhat]), 0.02, None))(pred_fn(mf, X))

res = {k: [] for k in ["M0", "M1", "M1cv", "ens"]}
cov = {k: [] for k in res}
for t in TEST_YEARS:
    tr = L[L.annee < t]; ok = tr.groupby("dep").annee.count(); lev = levels(tr[tr.dep.isin(ok[ok >= 3].index)])
    tr = with_rel(tr, lev); te = with_rel(L[L.annee == t], lev)
    # alpha par validation interne (3 dernières années d'entraînement)
    yrs = sorted(tr.annee.unique()); inner_tr, inner_va = tr[~tr.annee.isin(yrs[-3:])], tr[tr.annee.isin(yrs[-3:])]
    best = min([0.001, 0.005, 0.02, 0.05, 0.1, 0.2], key=lambda a: pinball(pred_lq(fit_lq(inner_tr, a), inner_va), inner_va.rel.to_numpy()))
    preds = {
        "M0": calibrate(lambda m, X: m.predict(X), lambda d: Baseline().fit(d, d.rel.to_numpy()), tr),
        "M1": calibrate(pred_lq, lambda d: fit_lq(d, 0.005), tr),
        "M1cv": calibrate(pred_lq, lambda d: fit_lq(d, best), tr),
    }
    g = calibrate(lambda m, X: m.predict(X), lambda d: GBMQuantile().fit(d, d.rel.to_numpy()), tr)
    y = te.rel.to_numpy()
    for k, f in preds.items():
        q = f(te); res[k].append(pinball(q, y) * len(y)); cov[k].append(np.sum((y >= q[:, 0]) & (y <= q[:, 2])))
    qe = (preds["M0"](te) + preds["M1"](te) + g(te)) / 3
    res["ens"].append(pinball(qe, y) * len(y)); cov["ens"].append(np.sum((y >= qe[:, 0]) & (y <= qe[:, 2])))
    print(t, "alpha retenu", best)
n = sum(len(with_rel(L[L.annee == t], levels(L[L.annee < t]))) for t in TEST_YEARS)
for k in res: print(k, "pinball", round(sum(res[k]) / n, 4), "couverture", round(sum(cov[k]) / n, 3))
