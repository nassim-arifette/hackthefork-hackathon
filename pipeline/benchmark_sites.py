"""Reproducible, exploratory site/procurement benchmark on the exported RPG parcels.

Run ``python pipeline/benchmark_sites.py`` from any directory. This script imports
neither the model nor its optional training dependencies. Whole parcels are taken
in increasing unit-cost order; this is a procurement rule, not an exact integer
optimization. Every grid search includes its supplied baseline site.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
APP_DATA = ROOT / "app" / "src" / "data"
DEFAULT_OUTPUT = ROOT / "experiments" / "sites"
RAD = math.pi / 180
LEGACY_SITES = {300: (2.53429, 49.04568), 5000: (3.12829, 48.55168)}


@dataclass(frozen=True)
class Parameters:
    target_t: float
    mode: str = "landed"
    delivered_price: float = 1600.0
    loss: float = 0.10
    fixed_gross_t: float = 5.0
    transport_gross_t_km: float = 0.12
    sorting_gross_t: float = 180.0
    detour: float = 1.3

    def validate(self) -> None:
        if self.mode not in {"collection", "landed"}:
            raise ValueError("mode must be collection or landed")
        values = [self.target_t, self.delivered_price, self.loss, self.fixed_gross_t,
                  self.transport_gross_t_km, self.sorting_gross_t, self.detour]
        if not all(math.isfinite(x) for x in values):
            raise ValueError("parameters must be finite")
        if self.target_t <= 0 or not 0 <= self.loss < 1 or self.detour <= 0:
            raise ValueError("positive target/detour and loss in [0,1) required")
        if min(self.delivered_price, self.fixed_gross_t, self.transport_gross_t_km,
               self.sorting_gross_t) < 0:
            raise ValueError("costs and prices must be nonnegative")


@dataclass
class Parcels:
    ids: list[str]
    dep: np.ndarray
    area: np.ndarray
    net_t: np.ndarray
    lon: np.ndarray
    lat: np.ndarray
    farm_price: np.ndarray
    export_loss: float = 0.10


def load_parcels(directory: Path = APP_DATA) -> tuple[Parcels, dict, list[Path]]:
    files = [directory / "parcels.json", directory / "thresholds.json", directory / "meta.json",
             ROOT / "data" / "pilote_300t" / "contrats.json"]
    raw = json.loads(files[0].read_text())
    thresholds = json.loads(files[1].read_text())
    h = json.loads(files[2].read_text())["hypotheses"]
    pilot = json.loads(files[3].read_text())["synthetique_2027"]
    stars = {d["dep"]: d["p_star"] for d in thresholds["par_departement"]}
    rows = [p for p in raw if p[2] == "ble" and p[6] > 0]
    a = np.asarray([[p[3], p[6], p[8], p[9]] for p in rows], dtype=float)
    dep = np.asarray([p[1] for p in rows])
    parcels = Parcels([p[0] for p in rows], dep, a[:, 0], a[:, 1], a[:, 2], a[:, 3],
                      np.asarray([stars[d] for d in dep], dtype=float),
                      float(h["part_non_valorisee"]["valeur"]))
    config = {
        "site": tuple(h["site_acheteur"]["valeur"]),
        "loss": parcels.export_loss,
        "fixed_gross_t": h["forfait_collecte_eur_t"]["valeur"],
        "transport_gross_t_km": h["cout_transport_eur_t_km"]["valeur"],
        "sorting_gross_t": pilot["tri_eur_t_brute_recue"],
        "detour": h["facteur_detour_route"]["valeur"],
        "sorting_source": pilot["source_cout_tri_url"],
        "sorting_status": pilot["statut_cout_tri"],
    }
    return parcels, config, files


def distances(parcels: Parcels, site: tuple[float, float], detour: float) -> np.ndarray:
    lon, lat = site
    a = np.sin((parcels.lat - lat) * RAD / 2) ** 2 + np.cos(parcels.lat * RAD) * math.cos(lat * RAD) \
        * np.sin((parcels.lon - lon) * RAD / 2) ** 2
    return 2 * 6371 * np.arcsin(np.sqrt(np.clip(a, 0, 1))) * detour


def evaluate(parcels: Parcels, site: tuple[float, float], p: Parameters, *, legacy: bool = False) -> dict:
    """Select whole parcels and evaluate exactly the same allocation used by search.

    collection: fixed delivered quote; the collection allowance is contained in
    that quote, so buyer landed cost is quote + sorting, not quote + collection.
    landed: distinct regional farm prices + collection + sorting; no price cap.
    legacy=True reproduces the former gross/net accounting for regression only.
    """
    p.validate()
    if len(site) != 2 or not all(math.isfinite(x) for x in site):
        raise ValueError("finite longitude and latitude required")
    net_fraction = 1 - p.loss
    tonnes = parcels.net_t * net_fraction / (1 - parcels.export_loss)
    dist = distances(parcels, site, p.detour)
    collection = (p.fixed_gross_t + p.transport_gross_t_km * dist) / (1 if legacy else net_fraction)
    sorting = p.sorting_gross_t / net_fraction
    regional_landed = parcels.farm_price + collection + sorting
    eligible = np.flatnonzero(parcels.farm_price + collection <= p.delivered_price) \
        if p.mode == "collection" else np.arange(len(tonnes))
    # Sorting is constant across suppliers; keep the same exact sort key as the app.
    metric = dist if p.mode == "collection" else parcels.farm_price + collection
    # Stable original index is the second sort key, including coincident parcels.
    order = eligible[np.lexsort((eligible, metric[eligible]))]
    cumulative = np.cumsum(tonnes[order])
    count = min(len(order), int(np.searchsorted(cumulative, p.target_t, side="left")) + 1)
    idx = order[:count]
    net = float(cumulative[count - 1]) if count else 0.0
    reached = net >= p.target_t
    weights = tonnes[idx] / net if net else np.asarray([])
    mean = lambda arr: float(np.dot(weights, arr[idx])) if net else None
    collection_mean = mean(collection)
    farm_mean = mean(parcels.farm_price) if p.mode == "landed" else \
        (p.delivered_price - collection_mean if net else None)
    landed_mean = (farm_mean + collection_mean + sorting) if net else None
    return {
        "status": "feasible_expected_volume" if reached else "insufficient_expected_volume",
        "reached": reached,
        "longitude": float(site[0]), "latitude": float(site[1]),
        "parcels": count, "area_ha": float(parcels.area[idx].sum()),
        "expected_net_t": net, "surplus_t": max(0.0, net - p.target_t),
        "mean_route_km": mean(dist), "max_route_km": float(dist[idx].max()) if net else None,
        "farm_eur_net_t": farm_mean, "collection_eur_net_t": collection_mean,
        "sorting_eur_net_t": sorting, "landed_eur_net_t": landed_mean,
        "budget_eur": net * landed_mean if net else 0.0,
        "objective_eur_net_t": (collection_mean if p.mode == "collection" else landed_mean) if reached else None,
        "selected_ids": [parcels.ids[i] for i in idx],
        "departments_net_t": {str(d): float(tonnes[idx][parcels.dep[idx] == d].sum()) for d in np.unique(parcels.dep[idx])},
    }


def optimize(parcels: Parcels, baseline: tuple[float, float], p: Parameters) -> dict:
    """Best observed grid candidate, refined twice, with baseline non-regression.

    This is a deterministic heuristic over theoretical coordinates. It neither
    proves global optimality nor establishes the existence of a usable facility.
    """
    best = evaluate(parcels, baseline, p)
    tested = 1
    if not len(parcels.lon):
        return best | {"candidates_tested": tested}
    if sum(parcels.net_t) * (1 - p.loss) / (1 - parcels.export_loss) < p.target_t:
        return best | {"candidates_tested": tested}

    def score(r: dict) -> float:
        return r["objective_eur_net_t"] if r["reached"] else math.inf

    def scan(lo0: float, lo1: float, la0: float, la1: float, dx: float, dy: float) -> None:
        nonlocal best, tested
        # Match the browser's inclusive, incremented grid, then evaluate rounded coordinates.
        lo = lo0
        while lo <= lo1 + 1e-10:
            la = la0
            while la <= la1 + 1e-10:
                candidate = evaluate(parcels, (round(lo, 5), round(la, 5)), p)
                tested += 1
                if score(candidate) < score(best) - 1e-10:
                    best = candidate
                la += dy
            lo += dx

    scan(float(parcels.lon.min()), float(parcels.lon.max()), float(parcels.lat.min()), float(parcels.lat.max()), .06, .04)
    if best["reached"]:
        lo, la = best["longitude"], best["latitude"]
        scan(lo - .06, lo + .06, la - .04, la + .04, .01, .007)
        lo, la = best["longitude"], best["latitude"]
        scan(lo - .01, lo + .01, la - .007, la + .007, .002, .0014)
    return best | {"candidates_tested": tested}


def row(scenario: str, location: str, p: Parameters, result: dict) -> dict:
    return {"scenario": scenario, "location": location, **asdict(p),
            **{k: v for k, v in result.items() if k not in {"selected_ids", "departments_net_t"}},
            "departments_net_t": json.dumps(result["departments_net_t"], ensure_ascii=False, sort_keys=True),
            "selected_ids_sha256": hashlib.sha256("\n".join(result["selected_ids"]).encode()).hexdigest()}


def benchmark(output: Path = DEFAULT_OUTPUT) -> list[dict]:
    parcels, config, source_files = load_parcels()
    tracked_files = source_files + [Path(__file__)]
    hashes = {str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest() for f in tracked_files}
    current = config["site"]
    defaults = {k: config[k] for k in ("loss", "fixed_gross_t", "transport_gross_t_km", "sorting_gross_t", "detour")}
    results = []
    selections = []
    for target in (300, 5000):
        for price in (1500, 1600):
            p = Parameters(target, mode="collection", delivered_price=price, **defaults)
            for name, site in (("current_legacy", current), ("old_distance_search_legacy", LEGACY_SITES[target])):
                results.append(row("legacy_regression", name, p, evaluate(parcels, site, p, legacy=True)))
            base = evaluate(parcels, current, p)
            best = optimize(parcels, current, p)
            results.extend((row("fixed_delivered_quote", "current", p, base),
                            row("fixed_delivered_quote", "old_distance_site", p, evaluate(parcels, LEGACY_SITES[target], p)),
                            row("fixed_delivered_quote", "searched", p, best)))
            selections.append({"scenario": "fixed_delivered_quote", "parameters": asdict(p), "result": best})
            print(f"collection target={target} price={price}: {base['objective_eur_net_t']} -> {best['objective_eur_net_t']}", flush=True)
        variants = [("central", {}), ("loss_0", {"loss": 0.0}), ("loss_20", {"loss": .2}),
                    ("transport_006", {"transport_gross_t_km": .06}), ("transport_020", {"transport_gross_t_km": .20}),
                    ("sorting_100", {"sorting_gross_t": 100.0}), ("sorting_300", {"sorting_gross_t": 300.0})]
        for name, overrides in variants:
            p = Parameters(target, **(defaults | overrides))
            base = evaluate(parcels, current, p)
            best = optimize(parcels, current, p)
            results.extend((row(f"landed_{name}", "current", p, base), row(f"landed_{name}", "searched", p, best)))
            selections.append({"scenario": f"landed_{name}", "parameters": asdict(p), "result": best})
            print(f"landed target={target} {name}: {base['objective_eur_net_t']} -> {best['objective_eur_net_t']}", flush=True)
    if any(hashlib.sha256(f.read_bytes()).hexdigest() != hashes[str(f.relative_to(ROOT))] for f in tracked_files):
        raise RuntimeError("Benchmark inputs changed during computation; rerun after exports finish.")
    output.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for r in results for key in r))
    with (output / "results.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
    (output / "selected_parcels.json").write_text(json.dumps(selections, ensure_ascii=False, indent=2) + "\n")
    manifest = {"command": "python pipeline/benchmark_sites.py", "numpy_version": np.__version__,
                "source_sha256": hashes,
                "scenario_site": list(current), "parameters": defaults,
                "sorting_status": config["sorting_status"], "sorting_source": config["sorting_source"]}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    (output / "README.md").write_text(report(results, config), encoding="utf-8")
    return results


def report(results: list[dict], config: dict) -> str:
    def n(x: float | None, digits: int = 2) -> str:
        return "non atteint" if x is None else f"{x:,.{digits}f}".replace(",", " ").replace(".", ",")

    lines = ["# Sites et approvisionnement : expérience reproductible", "",
             "`python pipeline/benchmark_sites.py` reproduit `results.csv`, les parcelles sélectionnées et le manifeste SHA-256 des entrées. Aucun appel réseau ni entraînement de modèle n'est nécessaire.", "",
             "## Deux décisions distinctes", "",
             "- **Prix rendu uniforme fixé** : seuls les producteurs dont P* départ ferme + collecte nette est au plus égal au prix rendu sont retenus ; les parcelles admissibles les plus proches sont prises entières. L'objectif de localisation est la collecte moyenne. Le prix rendu contient déjà la collecte : coût acheteur = prix rendu + tri net, sans ajouter deux fois le transport. Une économie de collecte augmente ici la part revenant au producteur ; elle ne réduit pas un prix rendu maintenu fixe.",
             "- **Prix départ ferme départementaux différenciés** : P* exporté pour chaque département + collecte + tri. Les parcelles sont prises entières par coût unitaire rendu croissant, sans plafond de prix. Ce régime commercial est une hypothèse supplémentaire ; il ne représente pas le contrat commun par tranches de l'application.", "",
             "Pour chaque candidat, le même évaluateur calcule la sélection, la distance Haversine × détour, le volume et le coût. Le site courant est candidat ; à paramètres identiques, la recherche ne peut donc dégrader son objectif. La grille de 0,06° × 0,04° est affinée deux fois. Le résultat est le meilleur candidat testé pour cette règle d'approvisionnement, **pas une preuve d'optimum global** : la sélection de parcelles entières est gloutonne et la grille est heuristique.", "",
             "## Régression de l'ancienne recherche", "",
             "Ces lignes reproduisent l'ancienne assiette de collecte (sans division brut/net) et les anciens sites optimisés sans prix. Elles servent uniquement à constater le défaut corrigé.", "",
             "| Cible | Prix rendu | Distance site courant | Distance ancien résultat | Collecte courante → ancien résultat |",
             "|---|---|---|---|---|"]
    for target in (300, 5000):
        for price in (1500, 1600):
            pair = [r for r in results if r["scenario"] == "legacy_regression" and r["target_t"] == target and r["delivered_price"] == price]
            a, b = pair
            lines.append(f"| {target} t | {price} €/t | {n(a['mean_route_km'])} km | {n(b['mean_route_km'])} km | {n(a['collection_eur_net_t'])} → {n(b['collection_eur_net_t'])} €/t |")
    lines += ["", "## Recherche corrigée sous prix rendu fixé", "",
              "L'ancien emplacement est aussi réévalué ci-dessous avec la même conversion brut/net que la recherche corrigée.", "",
              "| Cible | Prix rendu | Collecte courante → ancien site → recherche | Tonnes attendues sélectionnées | Parcelles | Site théorique retenu |",
              "|---|---|---|---|---|---|"]
    for target in (300, 5000):
        for price in (1500, 1600):
            a, old, b = [r for r in results if r["scenario"] == "fixed_delivered_quote" and r["target_t"] == target and r["delivered_price"] == price]
            lines.append(f"| {target} t | {price} €/t | {n(a['collection_eur_net_t'])} → {n(old['collection_eur_net_t'])} → {n(b['collection_eur_net_t'])} €/t | {n(b['expected_net_t'], 1)} t | {b['parcels']} | {b['longitude']:.5f}, {b['latitude']:.5f} |")
    lines += ["", "## Coût rendu complet et sensibilités", "",
              "Coût = règlement agricole au P* départemental + (forfait + coefficient × km routiers + tri) / fraction acceptée. Le budget porte sur toutes les tonnes des parcelles sélectionnées, y compris le surplus ; le dénominateur est ce même volume net sélectionné.", "",
              "| Cible | Scénario | Coût courant | Coût recherche | Gain | Net sélectionné |",
              "|---|---|---|---|---|---|"]
    for target in (300, 5000):
        names = list(dict.fromkeys(r["scenario"] for r in results if r["scenario"].startswith("landed_") and r["target_t"] == target))
        for name in names:
            a, b = [r for r in results if r["scenario"] == name and r["target_t"] == target]
            lines.append(f"| {target} t | {name.removeprefix('landed_')} | {n(a['landed_eur_net_t'])} €/t | {n(b['landed_eur_net_t'])} €/t | {n(a['landed_eur_net_t'] - b['landed_eur_net_t'])} €/t | {n(b['expected_net_t'], 1)} t |")
    lines += ["", "## Hypothèses et limites", "",
              f"- Site de référence : {config['site']}, fictif. Les points de grille ne constituent pas des silos ou sites de tri identifiés.",
              f"- Scénario central : perte {config['loss']:.0%}, collecte {config['fixed_gross_t']} €/t brute + {config['transport_gross_t_km']} €/t brute/km, détour {config['detour']}, tri {config['sorting_gross_t']} €/t brute. À 90 % de sortie, 180 €/t brute vaut 200 €/t nette. Le coefficient logistique comprend les retours ; aucune seconde multiplication par deux.",
              f"- Tri : [proxy optique en contexte bio]({config['sorting_source']}), repris du dossier synthétique ; ce n'est pas un devis industriel conventionnel.",
              "- La sensibilité qualité transforme les tonnes exportées par (1−perte)/(1−perte à l'export). Elle conserve les P* exportés : **sensibilité logistique uniquement**, sans recalibration de la protection agricole. Les sensibilités transport et tri modifient un seul paramètre à la fois.",
              "- Les volumes sont des espérances départementales, pas des livraisons garanties. Les hectares et identifiants des parcelles sont observés dans le RPG, mais leur disponibilité, agronomie et rotation ne sont pas vérifiées.",
              "- Aucune capacité disponible de réception, tri ou stockage, aucun engagement commercial, coût fixe, devis routier, donnée de séchage ni récupération des écarts n'est connu ici. Ces postes ne sont pas inventés ; les résultats ne démontrent aucune faisabilité industrielle. Stockage, conditionnement, investissement et frais généraux sont exclus.",
              "- Le pilote initial compare jusqu'à 300 t d'une collecte existante ; il ne crée pas un besoin attesté de site nouveau. Les 5 000 t sont une ambition de scénario.",
              "- Les fichiers exportés de prix plancher restent la source de l'expérience. Le manifeste permet d'identifier exactement leur version ; toute modification de calibration impose de relancer ce script.", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    benchmark(args.output)
