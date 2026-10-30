"""Modèles de rendement, calibration conformal et calcul du prix plancher.

Le modèle prédit un rendement **relatif** (rendement / niveau moyen du département),
ce qui rend les départements comparables et permet de transférer le modèle à un
département peu renseigné (l'Île-de-France pour la lentille). Voir docs/MODELE.md.
"""
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.linear_model import QuantileRegressor

from common import CLIMATO_YEARS, DATA, IDF_AGRI

QUANTILES = (0.1, 0.5, 0.9)
WEATHER = ["pluie_mj", "pluie_avj", "j30_jj", "gel_tardif", "pluie_recolte", "tmax_mj"]
FEATURES = ["tendance"] + [f"{w}_anom" for w in WEATHER]
ALPHA_INTERVAL = 0.2  # intervalle à 80 %
N_CALIB_YEARS = 3


def load() -> pd.DataFrame:
    """Panel utilisable (sans doublons) fusionné avec les anomalies météo et le prix du blé."""
    panel = pd.read_csv(DATA / "panel_rendements.csv", dtype={"dep": str, "serie_groupe": str})
    meteo = pd.read_csv(DATA / "meteo_dept.csv", dtype={"dep": str})
    prix = pd.read_csv(DATA / "prix_ble.csv")[["annee", "prix_eur_t"]]
    meteo = meteo.merge(prix.rename(columns={"prix_eur_t": "prix_ble"}), on="annee", how="left")
    # Anomalies par rapport à la climatologie 2010-2018, figée avant toute année test.
    clim = meteo[meteo.annee.isin(CLIMATO_YEARS)].groupby("dep")[WEATHER].mean()
    anom = meteo.set_index("dep")[WEATHER] - clim.reindex(meteo.dep).values
    scale = anom[meteo.set_index("dep").annee.isin(CLIMATO_YEARS).values].std()
    for w in WEATHER:
        meteo[f"{w}_anom"] = (anom[w] / scale[w]).values
    meteo["tendance"] = (meteo.annee - 2010) / 10
    u = panel[panel.utilisable & ~panel.doublon]
    return u.merge(meteo, on=["dep", "annee"], how="inner"), meteo


def levels_lookup(culture: str) -> pd.Series:
    """Niveau moyen de rendement de chaque département, doublons compris (consultation seule)."""
    panel = pd.read_csv(DATA / "panel_rendements.csv", dtype={"dep": str, "serie_groupe": str})
    u = panel[panel.utilisable & (panel.culture == culture)]
    return u.groupby("dep").rendement_qha.mean()


def levels(train: pd.DataFrame) -> pd.Series:
    """Niveau moyen de rendement (q/ha) de chaque département sur les années d'entraînement."""
    return train.groupby("dep").rendement_qha.mean()


def with_rel(df: pd.DataFrame, lev: pd.Series) -> pd.DataFrame:
    df = df[df.dep.isin(lev.index)].copy()
    df["rel"] = df.rendement_qha / lev.reindex(df.dep).values
    return df


# ---------- modèles ----------

class Baseline:
    """M0 : tendance linéaire commune + quantiles empiriques des résidus."""
    name = "M0"

    def fit(self, X, y):
        A = np.c_[np.ones(len(X)), X["tendance"]]
        self.coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        res = y - A @ self.coef
        self.qres = {q: np.quantile(res, q) for q in QUANTILES}
        return self

    def predict(self, X):
        base = self.coef[0] + self.coef[1] * X["tendance"].to_numpy()
        return np.column_stack([base + self.qres[q] for q in QUANTILES])


class LinearQuantile:
    """M1 : régression quantile linéaire sur la tendance et les anomalies météo."""
    name = "M1"

    def fit(self, X, y):
        self.models = [QuantileRegressor(quantile=q, alpha=0.005, solver="highs")
                       .fit(X[FEATURES], y) for q in QUANTILES]
        return self

    def predict(self, X):
        return np.sort(np.column_stack([m.predict(X[FEATURES]) for m in self.models]), axis=1)

    def coefficients(self):
        return {f"q{int(q*100)}": dict(zip(FEATURES, np.round(m.coef_, 4).tolist()))
                | {"constante": round(float(m.intercept_), 4)}
                for q, m in zip(QUANTILES, self.models)}


class GBMQuantile:
    """M2 : LightGBM quantile, peu profond et régularisé (challenger)."""
    name = "M2"

    def fit(self, X, y):
        self.models = [lgb.LGBMRegressor(objective="quantile", alpha=q, n_estimators=150,
                                         learning_rate=0.05, num_leaves=7, max_depth=3,
                                         min_child_samples=20, verbose=-1)
                       .fit(X[FEATURES], y) for q in QUANTILES]
        return self

    def predict(self, X):
        return np.sort(np.column_stack([m.predict(X[FEATURES]) for m in self.models]), axis=1)


MODELS = {"M0": Baseline, "M1": LinearQuantile, "M2": GBMQuantile}


class Calibrated:
    """Conformalized quantile regression, en respectant l'ordre du temps.

    On entraîne sur les années antérieures aux N_CALIB_YEARS dernières, on mesure
    sur celles-ci l'élargissement nécessaire pour couvrir 80 %, puis on réentraîne
    sur toutes les années et on applique cet élargissement.

    `kind="auto"` choisit, parmi M0, M1 et M2, celui qui a la plus faible pinball
    loss sur ces mêmes années de calibration : le choix n'utilise jamais l'année test.
    """

    def __init__(self, kind: str):
        self.kind = kind

    def fit(self, df: pd.DataFrame):
        years = sorted(df.annee.unique())
        cal_years = years[-N_CALIB_YEARS:]
        proper, cal = df[~df.annee.isin(cal_years)], df[df.annee.isin(cal_years)]
        if self.kind == "auto":
            losses = {k: pinball(MODELS[k]().fit(proper, proper.rel.to_numpy()).predict(cal),
                                 cal.rel.to_numpy()) for k in MODELS}
            self.kind = min(losses, key=losses.get)
            self.selection = {k: round(v, 4) for k, v in losses.items()}
        m = MODELS[self.kind]().fit(proper, proper.rel.to_numpy())
        q = m.predict(cal)
        scores = np.maximum(q[:, 0] - cal.rel.to_numpy(), cal.rel.to_numpy() - q[:, 2])
        n = len(scores)
        level = min(1.0, (1 - ALPHA_INTERVAL) * (n + 1) / n)
        self.qhat = float(np.quantile(scores, level, method="higher"))
        self.model = MODELS[self.kind]().fit(df, df.rel.to_numpy())
        return self

    def predict(self, X):
        q = self.model.predict(X).copy()
        q[:, 0] -= self.qhat
        q[:, 2] += self.qhat
        return np.clip(q, 0.02, None)


def pinball(q: np.ndarray, y: np.ndarray) -> float:
    loss = 0.0
    for j, a in enumerate(QUANTILES):
        d = y - q[:, j]
        loss += np.mean(np.maximum(a * d, (a - 1) * d))
    return loss / len(QUANTILES)


# ---------- Monte-Carlo et prix plancher ----------

def sample_quantile(q: np.ndarray, u: np.ndarray) -> np.ndarray:
    """Tire dans la distribution définie par (q10, q50, q90), queues linéaires."""
    q10, q50, q90 = q[:, 0], q[:, 1], q[:, 2]
    lo = (q50 - q10) / 0.4
    hi = (q90 - q50) / 0.4
    out = np.where(u < 0.5, q50 - (0.5 - u) * lo, q50 + (u - 0.5) * hi)
    return np.clip(out, 0.02, None)


def break_even_prices(X_pool, mL, mW, levL, levW, h, n=6000, seed=0):
    """Prix d'équilibre lentille/blé (€/t) dans n scénarios d'années rejouées.

    Chaque scénario tire une année historique : sa météo (pour les deux cultures) et
    son prix du blé, ce qui conserve leurs liens réels. `h["prix_ble"]` remplace la
    série si on veut tester un prix fixe (analyse de sensibilité).
    """
    rng = np.random.default_rng(seed)
    qL, qW = mL.predict(X_pool), mW.predict(X_pool)
    s = rng.integers(0, len(X_pool), n)
    yL = sample_quantile(qL[s], rng.random(n)) * levL / 10  # t/ha
    yW = sample_quantile(qW[s], rng.random(n)) * levW / 10
    pB = np.full(n, h["prix_ble"]) if h.get("prix_ble") else X_pool["prix_ble"].to_numpy()[s]
    cW, cL, bonus = h["charges_ble"], h["charges_lentille"], h["bonus"]
    return (pB * yW - cW + cL - bonus) / yL, yL, yW


def p_star(R: np.ndarray, tau: float) -> float:
    return float(np.quantile(R, tau))


def hyp_values(h: dict) -> dict:
    """Valeurs numériques des hypothèses. `bonus` = aide couplée + bonus de rotation (€/ha)."""
    return {"prix_ble": None,
            "charges_ble": h["charges_ble_eur_ha"]["valeur"],
            "charges_lentille": h["charges_lentille_eur_ha"]["valeur"],
            "aide": h["aide_couplee_eur_ha"]["valeur"],
            "rotation": h["bonus_rotation_eur_ha"]["valeur"],
            "bonus": h["aide_couplee_eur_ha"]["valeur"] + h["bonus_rotation_eur_ha"]["valeur"],
            "tau": h["fiabilite_visee"]["valeur"]}


def pool_for(meteo: pd.DataFrame, dep: str, years, target_year: int) -> pd.DataFrame:
    """Années météo historiques d'un département, projetées à l'année cible (tendance)."""
    p = meteo[(meteo.dep == dep) & meteo.annee.isin(years)].copy()
    p["tendance"] = (target_year - 2010) / 10
    return p
