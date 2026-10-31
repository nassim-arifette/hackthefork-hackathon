"""EXPOST_ORACLE: compare model prices after equal realised protection scaling.

This diagnostic uses evaluation outcomes to find each model's cheapest global
multiplier at a prescribed held rate. It is not a deployable calibration rule or
an out-of-time forecast. Honest policy points, when available, are shown apart.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KEYS = ["year", "dep"]
MODELS = ("trend", "linear", "qrf", "qrf_dense")
TARGETS = (.60, .70, .75, .80, .85, .90)
LABELS = {"trend": "M0", "linear": "M1", "qrf": "QRF", "qrf_dense": "QRF 101 quantiles"}


def weighted_quantile(values, weights, quantile):
    """Smallest observation with cumulative weight at least the target."""
    values, weights = np.asarray(values, float), np.asarray(weights, float)
    if not len(values) or len(values) != len(weights) or not 0 < quantile <= 1:
        raise ValueError("Invalid quantile inputs")
    if not np.isfinite(values).all() or not np.isfinite(weights).all() or (weights <= 0).any():
        raise ValueError("Quantile values/positive weights must be finite")
    order = np.argsort(values, kind="stable")
    cumulative = np.cumsum(weights[order])
    cutoff = quantile * cumulative[-1]
    tol = 4 * np.finfo(float).eps * cumulative[-1]
    position = np.searchsorted(cumulative, cutoff - tol, side="left")
    return float(values[order[min(position, len(values) - 1)]])


def equal_year_weights(rows):
    return 1. / rows.groupby("year").year.transform("size").to_numpy()


def minimal_multiplier(rows, target):
    if (rows.price <= 0).any():
        raise ValueError("Multiplicative frontier requires strictly positive base prices")
    ratio = rows.realised_break_even.to_numpy() / rows.price.to_numpy()
    factor = max(0., weighted_quantile(ratio, equal_year_weights(rows), target))
    # Floating division followed by multiplication can fall below the equality
    # boundary by one ulp. Move only if needed to realise the chosen quantile.
    weights = equal_year_weights(rows)
    for _ in range(4):
        held = factor * rows.price.to_numpy() >= rows.realised_break_even.to_numpy()
        if np.average(held, weights=weights) >= target - 1e-12:
            return factor
        factor = np.nextafter(factor, np.inf)
    raise ArithmeticError("Could not represent the target coverage boundary")


def assert_same_cohort(rows, models=MODELS):
    expected = None
    truth = None
    for model in models:
        d = rows[rows.model == model]
        if d.empty or d.duplicated(KEYS).any():
            raise ValueError(f"Invalid cohort for {model}")
        keys = set(map(tuple, d[KEYS].to_numpy()))
        if expected is not None and keys != expected:
            raise ValueError("Models do not share the same evaluation cohort")
        now = d.set_index(KEYS).realised_break_even.sort_index()
        if truth is not None and not np.allclose(truth, now, rtol=1e-10, atol=1e-8):
            raise ValueError("Models have different realised break-even outcomes")
        expected, truth = keys, now
    return expected


def summarize_prices(rows, factor=1.):
    d = rows.copy()
    d["price"] = d.price * factor
    error = d.realised_break_even - d.price
    d["held"] = d.price >= d.realised_break_even
    d["loss"] = np.maximum(.8 * error, -.2 * error)
    d["shortfall"] = np.maximum(error, 0.) * d.actual_lentil_t_ha
    annual = d.groupby("year")[["price", "held", "loss", "shortfall"]].mean()
    return {"n_cases": len(d), "n_years": int(d.year.nunique()),
            "n_departments": int(d.dep.nunique()), "factor": float(factor),
            "mean_price_year_equal": float(annual.price.mean()),
            "median_price": float(d.price.median()), "held_cases": float(d.held.mean()),
            "held_year_equal": float(annual.held.mean()),
            "contract_loss": float(annual.loss.mean()),
            "shortfall_eur_ha": float(annual.shortfall.mean())}


def summarize_honest_policies(policies, source, keys, reference_truth, old_keys):
    """Keep identically named policies from different experiments identifiable."""
    output = []
    for model, d in policies.groupby("model"):
        if d.duplicated(KEYS).any() or set(map(tuple, d[KEYS].to_numpy())) != keys:
            raise ValueError("Honest policies do not match the comparison cohort")
        if not np.allclose(d.set_index(KEYS).realised_break_even.sort_index(), reference_truth,
                           rtol=1e-10, atol=1e-8):
            raise ValueError("Honest policies have different realised break-even outcomes")
        for cohort, selected in [("all_192", d), ("original_133", d[[tuple(v) in old_keys for v in d[KEYS].to_numpy()]])]:
            output.append({"cohort": cohort, "model": model, "policy_source": source,
                           "kind": "PAST_ONLY_POLICY", **summarize_prices(selected)})
    return output


def frontier(rows, old_keys, targets=TARGETS):
    assert_same_cohort(rows)
    output = []
    for cohort, selected in [("all_192", rows), ("original_133", rows[[tuple(v) in old_keys for v in rows[KEYS].to_numpy()]])]:
        assert_same_cohort(selected)
        for model, d in selected.groupby("model"):
            output.append({"cohort": cohort, "model": model, "kind": "UNSCALED_OUT_OF_TIME",
                           "target": None, **summarize_prices(d)})
            for target in targets:
                factor = minimal_multiplier(d, target)
                output.append({"cohort": cohort, "model": model, "kind": "EXPOST_ORACLE",
                               "target": float(target), **summarize_prices(d, factor)})
    return pd.DataFrame(output)


def draw_plot(table, policies, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {"trend": "#af6500", "linear": "#7562a3", "qrf": "#007c83", "qrf_dense": "#2464b5"}
    fig, axes = plt.subplots(1, 2, figsize=(14, 6.8), sharey=True)
    for ax, cohort in zip(axes, ["all_192", "original_133"]):
        selected = table[table.cohort == cohort]
        for model in MODELS:
            line = selected[(selected.model == model) & (selected.kind == "EXPOST_ORACLE")].sort_values("held_year_equal")
            ax.plot(line.held_year_equal * 100, line.mean_price_year_equal, "o--",
                    color=colors[model], label=LABELS[model], markersize=4)
            point = selected[(selected.model == model) & (selected.kind == "UNSCALED_OUT_OF_TIME")]
            ax.scatter(point.held_year_equal * 100, point.mean_price_year_equal,
                       marker="s", color=colors[model], s=50, zorder=4)
        if len(policies):
            honest = policies[policies.cohort == cohort]
            initial = honest[honest.policy_source == "initial_q80"]
            if len(initial):
                ax.scatter(initial.held_year_equal * 100, initial.mean_price_year_equal,
                           color="#7e878d", marker="x", s=25, alpha=.45,
                           label=f"Politiques initiales ({initial.model.nunique()})")
            selected_raw = honest[honest.policy_source == "sensitivity_raw"]
            selected_expanded = honest[honest.policy_source == "sensitivity_expanded"]
            for base, label in [("trend", "M0 sélection passée"), ("qrf", "QRF sélection passée")]:
                chosen = selected_raw[selected_raw.model == base + "__past_selected"]
                if len(chosen):
                    ax.scatter(chosen.held_year_equal * 100, chosen.mean_price_year_equal,
                               color=colors[base], marker="*", s=230, edgecolor="black",
                               linewidth=.6, label=label, zorder=6)
            for index, base in enumerate(["trend", "qrf"]):
                chosen = selected_expanded[selected_expanded.model == base + "__past_selected"]
                if len(chosen):
                    ax.scatter(chosen.held_year_equal * 100, chosen.mean_price_year_equal,
                               facecolors="none", edgecolors=colors[base], marker="D", s=85,
                               linewidth=1.7, label="Sélections, base élargie" if index == 0 else None,
                               zorder=5)
        ax.axvline(80, color="#c53b40", linewidth=1.3, label="Objectif 80 %")
        ax.set_title("192 cas communs" if cohort == "all_192" else "133 cas d’origine")
        ax.set_xlabel("Contrats tenus · moyenne des taux annuels (%)")
        ax.grid(alpha=.2)
        ax.legend(fontsize=8, loc="upper left")
    axes[0].set_ylabel("Prix proposé · moyenne annuelle (€/t)")
    fig.suptitle("À protection réalisée comparable : prix requis par chaque modèle", fontsize=14)
    fig.text(.5, .015,
        "Pointillés : EXPOST_ORACLE, réglés avec les réponses du test. Carrés : prix bruts hors temps.\n"
        "Étoiles : calibration et sélection utilisant seulement les années antérieures (quantiles candidats 0,8 / 0,9 / 0,95).\n"
        "Losanges creux : même sélection avec distributions de rendement élargies. Les courbes oracle restent non déployables.",
        ha="center", fontsize=9)
    fig.tight_layout(rect=[0, .1, 1, .94])
    fig.savefig(output / "price_protection_frontier.png", dpi=170)
    fig.savefig(output / "price_protection_frontier.svg")
    plt.close(fig)


def run(args):
    args.output.mkdir(parents=True, exist_ok=True)
    base_file = ROOT / "experiments/colab_2026_10_31/colab_benchmark/predictions.csv"
    dense_file = ROOT / "experiments/qrf_optimization/predictions.csv"
    panel_file = ROOT / "data/panel_rendements.csv"
    old_file = ROOT / "data/backtest.json"
    base = pd.read_csv(base_file, dtype={"dep": str})
    dense = pd.read_csv(dense_file, dtype={"dep": str})
    rows = pd.concat([base[base.model.isin(MODELS[:-1])], dense[dense.model == "qrf_dense"]], ignore_index=True)
    panel = pd.read_csv(panel_file, dtype={"dep": str})
    yields = panel[panel.culture == "lentille"][["dep", "annee", "rendement_qha"]].rename(columns={"annee": "year"})
    yields["actual_lentil_t_ha"] = yields.rendement_qha / 10
    rows = rows.merge(yields[KEYS + ["actual_lentil_t_ha"]], on=KEYS, validate="many_to_one")
    old_keys = {(int(r["annee"]), r["dep"]) for r in json.loads(old_file.read_text())["detail"]}
    keys = assert_same_cohort(rows)
    if len(keys) != 192 or len(old_keys) != 133 or not old_keys.issubset(keys):
        raise ValueError("Unexpected comparison cohorts")
    table = frontier(rows, old_keys)
    table.to_csv(args.output / "frontier.csv", index=False)
    honest_rows, inputs = [], [Path(__file__), base_file, dense_file, panel_file, old_file]
    reference_truth = rows[rows.model == "trend"].set_index(KEYS).realised_break_even.sort_index()
    sources = {"initial_q80": args.policies,
               "sensitivity_raw": args.sensitivity_policies,
               "sensitivity_expanded": args.expanded_policies}
    for source, filename in sources.items():
        if not filename.exists():
            continue
        inputs.append(filename)
        policies = pd.read_csv(filename, dtype={"dep": str})
        if "actual_lentil_t_ha" not in policies:
            policies = policies.merge(yields[KEYS + ["actual_lentil_t_ha"]], on=KEYS, validate="many_to_one")
        honest_rows.extend(summarize_honest_policies(policies, source, keys, reference_truth, old_keys))
    honest = pd.DataFrame(honest_rows)
    honest.to_csv(args.output / "honest_policy_points.csv", index=False)
    focus = table[(table.kind == "EXPOST_ORACLE") & np.isclose(table.target, .8)]
    comparisons = []
    for cohort, d in focus.groupby("cohort"):
        baseline = d[d.model == "trend"].iloc[0]
        for _, row in d.iterrows():
            comparisons.append({"cohort": cohort, "model": row.model,
                "oracle_target": .8, "factor": float(row.factor),
                "held_year_equal": float(row.held_year_equal),
                "mean_price_year_equal": float(row.mean_price_year_equal),
                "delta_mean_price_vs_M0": float(row.mean_price_year_equal-baseline.mean_price_year_equal),
                "relative_price_gain_vs_M0": float(1-row.mean_price_year_equal/baseline.mean_price_year_equal)})
    result = {"status": "EXPOST_ORACLE_DIAGNOSTIC_NOT_DEPLOYABLE",
        "method": "For each fixed model and cohort, the weighted empirical quantile of realised_break_even/base_price gives the minimum common multiplicative factor for target held rate. Each year has equal total weight.",
        "targets": list(TARGETS), "models": list(MODELS), "at_80": comparisons,
        "honest_policy_points_available": bool(len(honest)),
        "honest_policy_sources": {source: str(filename.relative_to(ROOT)) for source, filename in sources.items() if filename.exists()},
        "selected_policy_points": honest[honest.model.isin(["trend__past_selected", "qrf__past_selected"])].to_dict("records") if len(honest) else [],
        "limitations": ["Evaluation-year outcomes determine oracle factors; no future performance claim.",
            "This controls a single global multiplicative scale, not arbitrary price changes per case or department.",
            "Discrete outcomes can overshoot target coverage by the weight of a boundary case or ties.",
            "Equal average protection does not imply equal protection for every department or year."],
        "sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
        "packages": {n: importlib.metadata.version(n) for n in ("numpy", "pandas", "matplotlib")}}
    (args.output / "results.json").write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    lines = ["# Prix à protection comparable : diagnostic EXPOST_ORACLE", "",
        "Ce diagnostic ajuste un multiplicateur commun sur les résultats des années testées. Il permet de comparer le niveau de prix nécessaire pour atteindre une protection réalisée proche de 80 %, à qualité relative des prix départementaux inchangée. **Il utilise les réponses du test et ne constitue donc ni une politique déployable ni un nouveau backtest hors temps.**", "",
        "Chaque année reçoit le même poids. Le facteur est le quantile pondéré des ratios prix d’équilibre réalisé / prix proposé. La couverture atteinte peut dépasser légèrement la cible lorsque le seuil tombe sur un cas ou sur des ex æquo.", "",
        "| Cohorte | Modèle | Facteur oracle | Tenus, années | Prix moyen €/t | Écart de prix vs M0 |",
        "|---|---|---:|---:|---:|---:|"]
    for row in comparisons:
        lines.append(f"| {row['cohort']} | {LABELS[row['model']]} | {row['factor']:.3f} | {row['held_year_equal']:.1%} | {row['mean_price_year_equal']:.0f} | {row['delta_mean_price_vs_M0']:+.0f} €/t |")
    if len(honest):
        lines += ["", "## Sélections fondées seulement sur le passé", "",
            "Ces points sont distincts de la frontière oracle : aucun multiplicateur n'est réajusté avec les réponses du test. La sensibilité élargit les quantiles de calibration candidats à 0,8 / 0,9 / 0,95, tout en conservant l'objectif de 80 % dans le sélecteur. Les politiques sont exécutées symétriquement pour M0 et QRF.", "",
            "| Cohorte | Distribution de départ | Modèle sélectionné | Tenus, cas | Tenus, années | Prix moyen €/t |",
            "|---|---|---|---:|---:|---:|"]
        selected = honest[honest.policy_source.isin(["sensitivity_raw", "sensitivity_expanded"]) & honest.model.isin(["trend__past_selected", "qrf__past_selected"])]
        for _, row in selected.iterrows():
            base_label = "Brute" if row.policy_source == "sensitivity_raw" else "Élargie"
            name = "M0" if row.model.startswith("trend") else "QRF"
            lines.append(f"| {row.cohort} | {base_label} | {name} | {row.held_cases:.1%} | {row.held_year_equal:.1%} | {row.mean_price_year_equal:.0f} |")
    lines += ["", "`frontier.csv` donne également les niveaux 60, 70, 75, 85 et 90 %, et les points bruts sans recalibration. Les graphiques distinguent les courbes oracle des carrés bruts hors temps et, lorsqu’elles sont disponibles, des politiques calibrées uniquement sur le passé.", "",
        "Les points honnêtes sont calculés avec leurs prix déjà produits, sans réajustement sur le test. Ils permettent de voir quelle part de la marge de progression diagnostiquée est effectivement capturée avant l’année à prédire. Le CSV conserve toutes les politiques, identifiées par `policy_source` pour ne pas confondre les mêmes noms entre expériences. La figure montre les 26 points initiaux en petit, les deux sélections sur distributions brutes en étoiles et les deux sélections sur distributions élargies en losanges creux.", "",
        "Cette frontière concerne des multiplicateurs globaux, pas le minimum théorique de toute politique possible. Un prix moyen plus faible à ce taux global ne garantit pas un gain dans chaque département. Le taux affiché est une moyenne de taux annuels, distinct du taux calculé sur tous les cas.", "",
        "Reproduction : `python pipeline/analyze_price_frontier.py`. Aucun export de production n’est modifié."]
    (args.output / "README.md").write_text("\n".join(lines) + "\n")
    draw_plot(table, honest, args.output)
    print(pd.DataFrame(comparisons).to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policies", type=Path, default=ROOT / "experiments/contract_policies/predictions.csv")
    parser.add_argument("--sensitivity-policies", type=Path, default=ROOT / "experiments/contract_policies_sensitivity/predictions.csv")
    parser.add_argument("--expanded-policies", type=Path, default=ROOT / "experiments/contract_policies_expanded/predictions.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/price_frontier")
    run(parser.parse_args())
