"""Modèles de rendement, calibration conformal et calcul du prix plancher.

Le modèle prédit un rendement **relatif** (rendement / niveau moyen du département),
ce qui rend les départements comparables et permet de transférer le modèle à un
département peu renseigné (l'Île-de-France pour la lentille). Voir docs/MODELE.md.
"""
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.linear_model import QuantileRegressor

from common import DATA

QUANTILES = (0.1, 0.5, 0.9)
WEATHER = ["pluie_mj", "pluie_avj", "j30_jj", "gel_tardif", "pluie_recolte", "tmax_mj"]
FEATURES = ["tendance"] + [f"{w}_anom" for w in WEATHER]
ALPHA_INTERVAL = 0.2  # intervalle à 80 %
N_CALIB_YEARS = 3
N_SELECTION_YEARS = 2


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Lignes utilisables brutes ; aucun ajustement sur la période complète.

    Les anciens drapeaux ``doublon`` et ``serie_groupe`` sont conservés à titre
    documentaire seulement. Regroupement, niveaux et météo sont appris par fit().
    """
    panel = pd.read_csv(DATA / "panel_rendements.csv", dtype={"dep": str, "serie_groupe": str})
    meteo = pd.read_csv(DATA / "meteo_dept.csv", dtype={"dep": str})
    prix = pd.read_csv(DATA / "prix_ble.csv")[["annee", "prix_eur_t"]]
    meteo = meteo.merge(prix.rename(columns={"prix_eur_t": "prix_ble"}), on="annee", how="left")
    meteo["tendance"] = (meteo.annee - 2010) / 10
    u = panel[panel.utilisable]
    return u.merge(meteo, on=["dep", "annee"], how="inner"), meteo


def levels_lookup(culture: str, before: int | None = None) -> pd.Series:
    """Niveau moyen de rendement de chaque département, doublons compris (consultation seule)."""
    panel = pd.read_csv(DATA / "panel_rendements.csv", dtype={"dep": str, "serie_groupe": str})
    u = panel[panel.utilisable & (panel.culture == culture)]
    if before is not None:
        u = u[u.annee < before]
    return u.groupby("dep").rendement_qha.mean()


def levels(train: pd.DataFrame) -> pd.Series:
    """Niveau moyen de rendement (q/ha) de chaque département sur les années d'entraînement."""
    return train.groupby("dep").rendement_qha.mean()


def with_rel(df: pd.DataFrame, lev: pd.Series) -> pd.DataFrame:
    df = df[df.dep.isin(lev.index)].copy()
    df["rel"] = df.rendement_qha / lev.reindex(df.dep).values
    return df


def prepare_as_of(df: pd.DataFrame, target_year: int) -> pd.DataFrame:
    """Frontière temporelle commune, AVANT toute transformation apprise."""
    return df[df.annee < target_year].copy()


def chronological_split(df: pd.DataFrame):
    years = sorted(int(y) for y in df.annee.unique())
    if len(years) < N_CALIB_YEARS + N_SELECTION_YEARS + 3:
        raise ValueError("Au moins huit années sont nécessaires : trois apprentissage, deux sélection, trois calibration.")
    return (years[:-(N_CALIB_YEARS + N_SELECTION_YEARS)],
            years[-(N_CALIB_YEARS + N_SELECTION_YEARS):-N_CALIB_YEARS],
            years[-N_CALIB_YEARS:])


def group_representatives(proper: pd.DataFrame) -> dict[str, str]:
    """Heuristique figée sur l'apprentissage : égalité à 0,01 q/ha sur >=4
    années communes et aucune divergence. Un groupe exige l'accord de chaque
    paire ; son représentant a la plus grande surface moyenne passée.
    Cela ne démontre pas l'indépendance statistique des séries conservées.
    """
    if proper.culture.nunique() != 1:
        raise ValueError("Un modèle doit être ajusté séparément pour chaque culture.")
    wide = proper.pivot(index="dep", columns="annee", values="rendement_qha").round(2)
    area = proper.groupby("dep").surface_ha.mean() if "surface_ha" in proper else pd.Series(dtype=float)
    groups: list[list[str]] = []

    def same(a, b):
        both = wide.loc[a].notna() & wide.loc[b].notna()
        return int(both.sum()) >= 4 and bool((wide.loc[a, both] == wide.loc[b, both]).all())

    for dep in sorted(wide.index):
        for group in groups:
            if all(same(dep, other) for other in group):
                group.append(dep)
                break
        else:
            groups.append([dep])
    result = {}
    for group in groups:
        head = max(group, key=lambda d: (float(area.get(d, 0)), d))
        result.update({dep: head for dep in group})
    return result


def training_cohort(df: pd.DataFrame) -> list[str]:
    proper_years, _, _ = chronological_split(df)
    proper = df[df.annee.isin(proper_years)]
    counts = proper.groupby("dep").annee.nunique()
    proper = proper[proper.dep.isin(counts[counts >= 3].index)]
    return sorted(set(group_representatives(proper).values()))


class WeatherTransform:
    """Anomalies et échelles estimées exclusivement sur l'apprentissage.

    Un territoire absent utilise le centre météo global d'apprentissage ; ce
    transfert reste une hypothèse, pas une validation locale du modèle.
    """

    def fit(self, proper):
        self.centres = proper.groupby("dep")[WEATHER].mean()
        self.fallback = proper[WEATHER].mean().fillna(0)
        centred = proper[WEATHER].to_numpy() - self.centres.reindex(proper.dep).to_numpy()
        scale = np.nanstd(centred, axis=0)
        self.scale = np.where(np.isfinite(scale) & (scale > 1e-8), scale, 1.0)
        return self

    def transform(self, df):
        out = df.copy()
        centre = self.centres.reindex(df.dep).fillna(self.fallback).to_numpy()
        values = np.where(np.isfinite(df[WEATHER].to_numpy()), df[WEATHER].to_numpy(), centre)
        anomalies = (values - centre) / self.scale
        for i, w in enumerate(WEATHER):
            out[f"{w}_anom"] = anomalies[:, i]
        # pool_for can deliberately project a historical weather row to a future trend.
        if "tendance" not in out:
            out["tendance"] = (out.annee - 2010) / 10
        return out


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
                                         min_child_samples=20, verbose=-1, n_jobs=1,
                                         random_state=0, deterministic=True, force_col_wise=True)
                       .fit(X[FEATURES], y) for q in QUANTILES]
        return self

    def predict(self, X):
        return np.sort(np.column_stack([m.predict(X[FEATURES]) for m in self.models]), axis=1)


class QuantileEnsemble:
    """M3 : moyenne équipondérée des quantiles M0/M1/M2, poids non ajustés.

    Challenger inspiré des travaux sur l'agrégation de quantiles ; il ne s'agit
    pas d'un mélange des distributions ni d'une amélioration présumée acquise.
    """
    name = "M3"

    def fit(self, X, y):
        self.models = [cls().fit(X, y) for cls in (Baseline, LinearQuantile, GBMQuantile)]
        return self

    def predict(self, X):
        return np.mean([m.predict(X) for m in self.models], axis=0)


MODELS = {"M0": Baseline, "M1": LinearQuantile, "M2": GBMQuantile, "M3": QuantileEnsemble}


class Calibrated:
    """Conformalized quantile regression, en respectant l'ordre du temps.

    Apprentissage, sélection (deux années) et calibration (trois années) sont
    disjoints. Toutes les transformations apprises utilisent l'apprentissage.
    Le prédicteur sélectionné est conservé : aucun réentraînement après calibration.
    Le rang CQR est corrigé pour la taille finie ; les dépendances temporelles et
    spatiales empêchent cependant de revendiquer ici la garantie échangeable.
    """

    def __init__(self, kind: str):
        if kind not in (*MODELS, "auto"):
            raise ValueError(f"Modèle inconnu : {kind}")
        self.requested_kind = kind
        self.kind = kind

    def fit(self, df: pd.DataFrame):
        proper_years, selection_years, cal_years = chronological_split(df)
        proper_raw = df[df.annee.isin(proper_years)].copy()
        counts = proper_raw.groupby("dep").annee.nunique()
        proper_raw = proper_raw[proper_raw.dep.isin(counts[counts >= 3].index)]
        if proper_raw.empty:
            raise ValueError("Aucun département avec trois années d'apprentissage.")
        self.levels = levels(proper_raw)
        self.levels_all = self.levels.copy()
        self.groups = group_representatives(proper_raw)
        self.retained_deps = sorted(set(self.groups.values()))
        self.transformer = WeatherTransform().fit(proper_raw)

        def prepared(years):
            rows = df[df.annee.isin(years) & df.dep.isin(self.retained_deps)]
            return self.transformer.transform(with_rel(rows, self.levels))

        proper, selection, cal = (prepared(years) for years in (proper_years, selection_years, cal_years))
        if selection.empty or cal.empty:
            raise ValueError("Sélection ou calibration vide pour la cohorte figée.")
        self.selection = {}
        if self.requested_kind == "auto":
            candidates = {k: cls().fit(proper, proper.rel.to_numpy()) for k, cls in MODELS.items()}
            # Equal year weighting prevents a year with more departments dominating selection.
            losses = {k: float(np.mean([pinball(np.clip(np.sort(m.predict(part), axis=1), 0.02, None),
                                               part.rel.to_numpy())
                                       for _, part in selection.groupby("annee")]))
                      for k, m in candidates.items()}
            self.kind = min(losses, key=losses.get)
            self.selection = losses
            self.model = candidates[self.kind]
        else:
            self.kind = self.requested_kind
            self.model = MODELS[self.kind]().fit(proper, proper.rel.to_numpy())
        q = np.clip(np.sort(self.model.predict(cal), axis=1), 0.02, None)
        scores = np.maximum(q[:, 0] - cal.rel.to_numpy(), cal.rel.to_numpy() - q[:, 2])
        n = len(scores)
        rank = int(np.ceil((n + 1) * (1 - ALPHA_INTERVAL)))
        # Expanding only is conservative and avoids an inverted interval on small samples.
        self.qhat = max(0.0, float(np.sort(scores)[rank - 1])) if rank <= n else float("inf")
        self.audit = {"proper_years": proper_years, "selection_years": selection_years,
                      "calibration_years": cal_years, "fit_years": proper_years,
                      "n_proper": len(proper), "n_selection": len(selection), "n_calibration": n,
                      "calibration_rank": rank, "qhat": self.qhat,
                      "retained_departments": self.retained_deps,
                      "groups": self.groups, "levels": self.levels.to_dict(),
                      "selected_model": self.kind, "selection_pinball": self.selection,
                      "refit_after_calibration": False,
                      "coverage_guarantee": "Empirique uniquement : données temporelles et spatiales non échangeables."}
        return self

    def predict_quantiles(self, X):
        """Quantiles bruts pour pertes quantiles et simulation de distribution."""
        return np.clip(np.sort(self.model.predict(self.transformer.transform(X)), axis=1), 0.02, None)

    def predict(self, X):
        """Bornes d'intervalle calibrées et médiane, PAS trois quantiles calibrés."""
        q = self.predict_quantiles(X).copy()
        q[:, 0] -= self.qhat
        q[:, 2] += self.qhat
        # Zero is a physical lower bound; clipping at 0.02 would exclude crop failures.
        q[:, 0] = np.maximum(q[:, 0], 0.0)
        return q


def pinball(q: np.ndarray, y: np.ndarray) -> float:
    loss = 0.0
    for j, a in enumerate(QUANTILES):
        d = y - q[:, j]
        loss += np.mean(np.maximum(a * d, (a - 1) * d))
    return loss / len(QUANTILES)


# ---------- Monte-Carlo et prix plancher ----------

def sample_quantile(q: np.ndarray, u: np.ndarray, tail: str = "linear") -> np.ndarray:
    """Interpolation des quantiles BRUTS : hypothèse de distribution explicite.

    ``linear`` extrapole les queues ; ``bounded`` borne à q10/q90 ; ``stress``
    double la pente sous q10. Le plancher 0,02 est numérique, non agronomique.
    """
    if tail not in {"linear", "bounded", "stress"}:
        raise ValueError(f"Hypothèse de queue inconnue : {tail}")
    u = np.asarray(u)
    if tail == "bounded":
        u = np.clip(u, 0.1, 0.9)
    q10, q50, q90 = q[:, 0], q[:, 1], q[:, 2]
    lo = (q50 - q10) / 0.4
    hi = (q90 - q50) / 0.4
    out = np.where(u < 0.5, q50 - (0.5 - u) * lo, q50 + (u - 0.5) * hi)
    if tail == "stress":
        out = np.where(u < 0.1, q10 - 2 * (0.1 - u) * lo, out)
    return np.clip(out, 0.02, None)


def break_even_prices(X_pool, mL, mW, levL, levW, h, n=6000, seed=0,
                      tail="linear", dependence="independent"):
    """Prix d'équilibre lentille/blé (€/t) dans n scénarios d'années rejouées.

    Chaque scénario tire une année historique : sa météo (pour les deux cultures) et
    son prix du blé, ce qui conserve leurs liens réels. `h["prix_ble"]` remplace la
    série si on veut tester un prix fixe (analyse de sensibilité).
    """
    if len(X_pool) == 0:
        raise ValueError("Aucune année météo disponible pour la simulation.")
    if dependence not in {"independent", "positive", "negative"}:
        raise ValueError(f"Dépendance résiduelle inconnue : {dependence}")
    rng = np.random.default_rng(seed)
    qL, qW = mL.predict_quantiles(X_pool), mW.predict_quantiles(X_pool)
    s = rng.integers(0, len(X_pool), n)
    uL, uW = rng.random(n), rng.random(n)
    if dependence == "positive":
        uW = uL
    elif dependence == "negative":
        uW = 1 - uL
    yL = sample_quantile(qL[s], uL, tail=tail) * levL / 10  # t/ha
    yW = sample_quantile(qW[s], uW, tail=tail) * levW / 10
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
