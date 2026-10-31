"""Plot the actual full-period fixed-price results for all five legumes.

Usage from any directory:
    python scripts/plot_advanced_results.py
    python scripts/plot_advanced_results.py --input /path/global_summary.csv

Reads only period=full, contract=fixed, group_type=all, group=all. No scores are
generated or imputed. Each panel includes every candidate/calibration and the
four separately evaluated temporal selectors. A highlighted new candidate is
the cheapest observed new configuration reaching 80%, a retrospective choice,
not a deployed model or the performance of the temporal selector.

Near-coincident selector markers are shifted in display points only, with a
leader to the exact data position; the axes and reported values stay unchanged.
Exports are headless PNG/PDF with fixed styling and no PDF creation timestamp.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, MaxNLocator
from matplotlib.transforms import ScaledTranslation
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CULTURES = (
    ("lentille", "Lentille"),
    ("pois_chiche", "Pois chiche"),
    ("haricot", "Haricot sec"),
    ("pois", "Pois protéagineux"),
    ("feverole", "Féverole"),
)
REFERENCE_STYLES = {
    "trend": {"color": "#0072B2", "marker": "o", "label": "M0 initial · toutes calibrations"},
    "qrf_seasonal": {"color": "#D55E00", "marker": "^", "label": "QRF précédent · toutes calibrations"},
}
SELECTOR_STYLES = {
    "selector/all_models": {"color": "#762A83", "marker": "*", "size": 160,
                            "label": "Sélecteur · tous modèles"},
    "selector/m0_only": {"color": "#0072B2", "marker": "s", "size": 65,
                         "label": "Sélecteur · M0 initial"},
    "selector/m0_extended": {"color": "#009E73", "marker": "D", "size": 65,
                             "label": "Sélecteur · M0 étendu"},
    "selector/qrf_reference": {"color": "#D55E00", "marker": "P", "size": 75,
                               "label": "Sélecteur · QRF précédent"},
}
TARGET = .8
NEW_COLOR = "#171717"
MODEL_LABELS = {
    "trend_dense": "M0 · 13 quantiles",
    "trend_joint_gaussian": "M0 · copule gaussienne",
    "trend_joint_empirical": "M0 · copule empirique",
    "qrf_combined_sparse": "QRF · variables combinées · 3 quantiles",
    "qrf_combined_dense": "QRF · variables combinées · 13 quantiles",
    "qrf_nasa_sparse": "QRF · séquences NASA · 3 quantiles",
    "qrf_nasa_dense": "QRF · séquences NASA · 13 quantiles",
    "qrf_sim_sparse": "QRF · SIM · 3 quantiles",
    "qrf_sim_dense": "QRF · SIM · 13 quantiles",
    "qrf_soil_sparse": "QRF · SIM et sols · 3 quantiles",
    "qrf_soil_dense": "QRF · SIM et sols · 13 quantiles",
    "qrf_soil_absolute": "QRF · météo absolue et anomalies",
    "qrf_soil_shrinkage": "QRF · niveau régional régularisé",
    "qrf_features05": "QRF · moitié des variables",
    "qrf_lgb_mixture": "Mélange QRF–LightGBM",
    "qrf_joint_gaussian": "QRF · copule gaussienne",
    "qrf_joint_empirical": "QRF · copule empirique",
    "qrf_agri_sparse": "QRF · météo CLC · 3 quantiles",
    "qrf_agri_dense": "QRF · météo CLC · 13 quantiles",
    "qrf_cropsoil_dense": "QRF · sol des parcelles RPG",
    "qrf_wheat_dense": "QRF · modèle du blé enrichi",
    "qrf_rpg_weather_sparse": "QRF · météo RPG · 3 quantiles",
    "qrf_rpg_weather_dense": "QRF · météo RPG · 13 quantiles",
    "lgb_sparse": "LightGBM · 3 quantiles",
    "lgb_dense": "LightGBM · 13 quantiles",
    "lgb_leaf15": "LightGBM · 15 feuilles",
    "cat_sparse": "CatBoost · 3 quantiles",
    "cat_dense": "CatBoost · 13 quantiles",
    "cat_depth6": "CatBoost · profondeur 6",
}


def number_fr(value, decimals=0):
    return f"{value:,.{decimals}f}".replace(",", "\u202f").replace(".", ",")


def policy_label(policy):
    model, calibration = str(policy).rsplit("/", 1)
    match = re.fullmatch(r"qrf_leaf(\d+)_depth(\d+)", model)
    if match:
        label = f"QRF · feuille {match[1]}, profondeur {match[2]}"
    else:
        label = MODEL_LABELS.get(model, model)
    return f"{label} · {calibration}"


def read_results(path):
    data = pd.read_csv(path)
    required = {"period", "contract", "group_type", "group", "culture", "policy",
                "realized_unit_cost", "held", "n", "n_years"}
    missing = required - set(data)
    if missing:
        raise ValueError(f"Missing summary columns: {sorted(missing)}")
    keep = ((data.period == "full") & (data.contract == "fixed")
            & (data.group_type == "all") & (data.group.astype(str) == "all"))
    data = data.loc[keep].copy()
    expected = {name for name, _ in CULTURES}
    if set(data.culture) != expected:
        raise ValueError(f"Expected all five crops; found {sorted(data.culture.unique())}")
    if data.duplicated(["culture", "policy"]).any():
        raise ValueError("Duplicate crop/policy in full-period fixed-price summary")
    for column in ("realized_unit_cost", "held", "n", "n_years"):
        data[column] = pd.to_numeric(data[column], errors="raise")
    if not np.isfinite(data[["realized_unit_cost", "held", "n", "n_years"]]).all().all():
        raise ValueError("Summary contains non-finite costs, protection or cohort counts")
    if (data.realized_unit_cost < 0).any() or not data.held.between(0, 1).all():
        raise ValueError("Costs must be nonnegative and held must be a fraction in [0,1]")
    if ((data.n <= 0) | (data.n_years <= 0)).any():
        raise ValueError("Positive observation/year counts are required")
    data["model"] = data.policy.str.rsplit("/", n=1).str[0]
    for culture, rows in data.groupby("culture"):
        absent = set(SELECTOR_STYLES) - set(rows.policy)
        if absent:
            raise ValueError(f"{culture}: missing temporal selectors {sorted(absent)}")
        if not set(REFERENCE_STYLES).issubset(set(rows.model)):
            raise ValueError(f"{culture}: missing M0 or previous QRF reference")
        if rows.n.nunique() != 1 or rows.n_years.nunique() != 1:
            raise ValueError(f"{culture}: policies use different observation/year counts")
    return data.sort_values(["culture", "policy"]).reset_index(drop=True)


def cheapest_new_candidate(rows):
    eligible = rows[(~rows.policy.str.startswith("selector/"))
                    & (~rows.model.isin(REFERENCE_STYLES)) & (rows.held >= TARGET)]
    if eligible.empty:
        return None
    columns = ["realized_unit_cost"]
    if "shortfall_eur_ha" in eligible:
        columns.append("shortfall_eur_ha")
    columns.append("policy")
    return eligible.sort_values(columns).iloc[0]


def selector_offsets(ax, rows):
    """Separate nearby selectors in display space without changing their data."""
    selectors = rows[rows.policy.isin(SELECTOR_STYLES)].set_index("policy")
    policies = list(SELECTOR_STYLES)
    points = np.array([[selectors.loc[p, "realized_unit_cost"], selectors.loc[p, "held"] * 100]
                       for p in policies])
    display = ax.transData.transform(points)
    threshold = 14 * ax.figure.dpi / 72
    parent = list(range(len(policies)))

    def find(i):
        while parent[i] != i:
            i = parent[i]
        return i

    for i in range(len(policies)):
        for j in range(i + 1, len(policies)):
            if np.linalg.norm(display[i] - display[j]) < threshold:
                parent[find(j)] = find(i)
    groups = {}
    for i in range(len(policies)):
        groups.setdefault(find(i), []).append(i)
    offsets = {p: (0., 0.) for p in policies}
    for members in groups.values():
        if len(members) <= 1:
            continue
        # Angles and ordering are fixed so repeated exports remain identical.
        angles = np.linspace(np.pi / 2, np.pi / 2 + 2 * np.pi, len(members), endpoint=False)
        for i, angle in zip(members, angles):
            offsets[policies[i]] = (13 * np.cos(angle), 13 * np.sin(angle))
    return offsets


def draw_selectors(ax, rows):
    offsets = selector_offsets(ax, rows)
    for policy, style in SELECTOR_STYLES.items():
        row = rows.loc[rows.policy == policy].iloc[0]
        x, y = row.realized_unit_cost, row.held * 100
        dx, dy = offsets[policy]
        if dx or dy:
            ax.scatter([x], [y], s=8, color=style["color"], zorder=6)
            ax.annotate("", xy=(x, y), xytext=(dx, dy), textcoords="offset points",
                        arrowprops={"arrowstyle": "-", "color": style["color"], "lw": .7},
                        zorder=6)
        transform = ax.transData + ScaledTranslation(dx / 72, dy / 72, ax.figure.dpi_scale_trans)
        ax.scatter([x], [y], s=style["size"], marker=style["marker"], color=style["color"],
                   edgecolors="white", linewidths=.9, transform=transform,
                   clip_on=False, zorder=8)


def annotate_candidate(ax, rows, best):
    if best is None:
        ax.text(.97, .96, "Aucun nouveau candidat\nà 80 % dans ce tableau",
                transform=ax.transAxes, ha="right", va="top", fontsize=8.5,
                color="#555555", bbox={"facecolor": "white", "edgecolor": "none", "alpha": .9})
        return
    x, y = best.realized_unit_cost, best.held * 100
    ax.scatter([x], [y], s=145, marker="o", facecolors="none", edgecolors=NEW_COLOR,
               linewidths=1.5, zorder=7)
    # Use the least populated top corner for one concise callout per panel.
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    xn = (rows.realized_unit_cost - x0) / (x1 - x0)
    yn = (rows.held * 100 - y0) / (y1 - y0)
    left_count = ((xn < .55) & (yn > .60)).sum()
    right_count = ((xn >= .45) & (yn > .60)).sum()
    left = left_count <= right_count
    label = "Nouveau candidat admissible\n" + textwrap.fill(policy_label(best.policy), width=36)
    label += f"\n{number_fr(x)} €/t ; {number_fr(y, 1)} %"
    ax.annotate(label, xy=(x, y), xytext=(.03 if left else .97, .96),
                textcoords="axes fraction", ha="left" if left else "right", va="top",
                fontsize=8, color=NEW_COLOR, linespacing=1.25,
                bbox={"facecolor": "white", "edgecolor": "#D8D8D8", "lw": .5,
                      "boxstyle": "round,pad=.35", "alpha": .95},
                arrowprops={"arrowstyle": "-", "color": "#666666", "lw": .7,
                            "shrinkA": 4, "shrinkB": 8}, zorder=9)


def legend_handles():
    handles = [Line2D([], [], linestyle="none", marker="o", markersize=4,
                      color="#A8ADB3", label="Autres candidats · toutes calibrations")]
    for style in REFERENCE_STYLES.values():
        handles.append(Line2D([], [], linestyle="none", marker=style["marker"], markersize=6,
                              color=style["color"], label=style["label"]))
    for style in SELECTOR_STYLES.values():
        handles.append(Line2D([], [], linestyle="none", marker=style["marker"],
                              markersize=10 if style["marker"] == "*" else 7,
                              color=style["color"], label=style["label"]))
    handles.append(Line2D([], [], linestyle="none", marker="o", markersize=9,
                          markerfacecolor="none", markeredgewidth=1.5, color=NEW_COLOR,
                          label="Nouveau candidat le moins cher à ≥80 % · choix rétrospectif"))
    return handles


def make_figure(data):
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 12,
        "axes.labelsize": 10, "xtick.labelsize": 9, "ytick.labelsize": 9,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": "#B8BEC5", "axes.linewidth": .7,
        "figure.facecolor": "white", "axes.facecolor": "white",
        "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.facecolor": "white",
    })
    fig = plt.figure(figsize=(16, 10.6), dpi=120)
    grid = fig.add_gridspec(2, 6, left=.065, right=.975, bottom=.225, top=.865,
                            hspace=.43, wspace=.75)
    spans = [(0, slice(0, 2)), (0, slice(2, 4)), (0, slice(4, 6)),
             (1, slice(1, 3)), (1, slice(3, 5))]
    axes = [fig.add_subplot(grid[row, columns]) for row, columns in spans]
    ymin = max(0., min(float(data.held.min() * 100), 80.) - 5.)
    ymax = min(100., max(float(data.held.max() * 100), 80.) + 5.)
    panels = []
    for ax, (culture, title) in zip(axes, CULTURES):
        rows = data[data.culture == culture]
        regular = rows[~rows.policy.str.startswith("selector/")]
        ax.scatter(regular.realized_unit_cost, regular.held * 100, s=15, color="#A8ADB3",
                   alpha=.45, linewidths=0, zorder=2, rasterized=True)
        for name, style in REFERENCE_STYLES.items():
            reference = rows[rows.model == name].sort_values("realized_unit_cost")
            ax.scatter(reference.realized_unit_cost, reference.held * 100, s=48,
                       color=style["color"], marker=style["marker"], edgecolors="white",
                       linewidths=.65, zorder=5)
        xlo, xhi = float(rows.realized_unit_cost.min()), float(rows.realized_unit_cost.max())
        padding = max((xhi - xlo) * .10, max(xhi, 1) * .025)
        ax.set_xlim(max(0., xlo - padding), xhi + padding)
        ax.set_ylim(ymin, ymax)
        ax.axhline(80., color="#585E66", linewidth=1, linestyle=(0, (5, 4)), zorder=1)
        ax.text(.99, 80., " 80 %", transform=ax.get_yaxis_transform(), va="bottom",
                ha="right", fontsize=8, color="#585E66")
        ax.grid(axis="y", color="#E8EBEF", linewidth=.6, zorder=0)
        ax.xaxis.set_major_locator(MaxNLocator(nbins=4))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: number_fr(x)))
        ax.yaxis.set_major_locator(MaxNLocator(nbins=6, integer=True))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{number_fr(y)} %"))
        ax.set_title(f"{title}  ·  {int(rows.n.iloc[0])} cas", loc="left", fontweight="bold", pad=11)
        panels.append((ax, rows, cheapest_new_candidate(rows)))
    # Layout is final before near-coincident markers are separated in display units.
    fig.canvas.draw()
    for ax, rows, best in panels:
        draw_selectors(ax, rows)
        annotate_candidate(ax, rows, best)
    fig.suptitle("Prix fixe : coût du contrat et marge au moins égale au blé",
                 x=.065, y=.965, ha="left", fontsize=19, fontweight="bold", color="#17212B")
    if {"evaluation_min_year", "evaluation_max_year"}.issubset(data):
        period = f"{int(data.evaluation_min_year.min())}–{int(data.evaluation_max_year.max())}"
    else:
        period = "Période complète"
    fig.text(.065, .915,
             f"{period} · mêmes cas au sein de chaque culture · vers le haut : davantage de contrats tenus ; vers la gauche : moins cher",
             fontsize=10.5, color="#4B5563")
    fig.text(.018, .55, "Marge légumineuse ≥ marge blé · part des cas observés",
             rotation=90, va="center", ha="center", fontsize=11, color="#293340")
    fig.text(.52, .175, "Règlement agricole réalisé / tonnes acceptées (€/t départ ferme)",
             ha="center", fontsize=11, color="#293340")
    fig.legend(handles=legend_handles(), loc="upper center", bbox_to_anchor=(.52, .145),
               ncol=4, frameon=False, fontsize=8.5, columnspacing=1.9, handletextpad=.6,
               labelspacing=1.1)
    fig.text(.065, .043,
             "Le cercle noir repère un choix après comparaison ; les sélecteurs sont évalués en choisissant uniquement dans le passé.",
             fontsize=8.7, color="#4B5563")
    fig.text(.065, .022,
             "Les marqueurs de sélecteurs superposés sont décalés pour rester lisibles ; leur trait pointe vers la valeur exacte. Aucun score n'est déplacé dans les données.",
             fontsize=8.2, color="#66717D")
    return fig


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "experiments/advanced_policies/global_summary.csv")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "experiments/advanced_policies/figures")
    parser.add_argument("--dpi", type=int, default=180, help="PNG resolution; PDF remains vector apart from the gray point cloud")
    args = parser.parse_args()
    if not args.input.is_file():
        parser.error(f"Actual completed summary is not available: {args.input}")
    if not 72 <= args.dpi <= 600:
        parser.error("--dpi must be between 72 and 600")
    data = read_results(args.input)
    fig = make_figure(data)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = args.output_dir / "prix_fixe_cout_protection"
    digest = hashlib.sha256(args.input.read_bytes()).hexdigest()
    fig.savefig(stem.with_suffix(".png"), dpi=args.dpi,
                metadata={"Software": "HackTheFork plot_advanced_results.py", "Source SHA256": digest})
    fig.savefig(stem.with_suffix(".pdf"), dpi=args.dpi,
                metadata={"Title": "HackTheFork — Prix fixe : coût et protection",
                          "Author": "HackTheFork", "Subject": f"Source summary SHA256: {digest}",
                          "CreationDate": None, "ModDate": None})
    plt.close(fig)
    print(f"Saved {stem.with_suffix('.png')} and {stem.with_suffix('.pdf')} from {len(data)} actual summary rows")


if __name__ == "__main__":
    main()
