"""Combine unchanged crop runs with exact reruns after crop-cost updates.

No coefficient, payment, margin or model prediction is repriced here. Replacement
crops must be rerun through the full historical simulation. Other crops may be
reused only when their audited economic inputs still equal the current inputs,
and model code, statistical inputs, package versions and run settings agree.
"""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from benchmark_multilegumes import assert_common_cohort, atomic_json, summarize
from contract_economics import accepted_yield, crop_hypotheses, signed_required_income
from multicrop_models import ROOT


MANDATORY_FILES = {
    "pipeline/multicrop_models.py", "pipeline/benchmark_multilegumes.py",
    "pipeline/contract_economics.py", "pipeline/common.py", "pipeline/model.py",
    "data/panel_rendements.csv", "data/meteo_dept_cultures.csv", "data/prix_ble.csv",
    "data/hypotheses.yaml", "data/cultures.yaml",
}
ALLOWED_CHANGED_FILES = {"data/cultures.yaml"}
ARTIFACTS = ("manifest.json", "predictions.csv", "audit.json", "cohorts.json")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def logical_csv_sha256(path):
    """Hash the original CSV bytes even when Git stores its gzip encoding."""
    path = Path(path)
    opener = gzip.open if path.suffix == ".gz" else open
    digest = hashlib.sha256()
    with opener(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def spec_signature(spec):
    return hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()


def validate_specs(old_manifest, new_manifest, replacement_cultures):
    """Reject differences that cannot be attributed to the crop configuration."""
    for label, manifest in (("old", old_manifest), ("replacement", new_manifest)):
        if manifest.get("signature") != spec_signature(manifest["spec"]):
            raise ValueError(f"Invalid {label} manifest signature")
        if not MANDATORY_FILES.issubset(manifest["spec"]["files"]):
            raise ValueError(f"Missing provenance files in {label} manifest")
    old, new = old_manifest["spec"], new_manifest["spec"]
    replacement = set(replacement_cultures)
    if set(new["options"]["cultures"]) != replacement:
        raise ValueError("Replacement run cultures must exactly match the requested replacements")
    if not replacement or not replacement.issubset(set(old["options"]["cultures"])):
        raise ValueError("Replacement crops must belong to the original full benchmark")
    if old["packages"] != new["packages"]:
        raise ValueError("Package versions changed between source runs")
    if old["files"].keys() != new["files"].keys():
        raise ValueError("Source manifests track different code or data files")
    different_files = sorted(name for name in old["files"] if old["files"][name] != new["files"][name])
    if set(different_files) - ALLOWED_CHANGED_FILES:
        raise ValueError(f"Code or common statistical inputs changed: {different_files}")
    old_options = {k: v for k, v in old["options"].items() if k != "cultures"}
    new_options = {k: v for k, v in new["options"].items() if k != "cultures"}
    if old_options != new_options:
        raise ValueError("Model, years, simulation or seed options changed")
    for crop in replacement:
        if old.get("seasonal_columns", {}).get(crop) != new.get("seasonal_columns", {}).get(crop):
            raise ValueError(f"Seasonal feature definitions changed for {crop}")
    excluded = {"options", "packages", "files", "seasonal_columns"}
    if {k: v for k, v in old.items() if k not in excluded} != {k: v for k, v in new.items() if k not in excluded}:
        raise ValueError("Simulation, target, or evaluation definitions changed")
    return different_files


def validate_current_files(spec, current_root=ROOT):
    """The replacement run must correspond exactly to the checked-out inputs."""
    root = Path(current_root).resolve()
    for name, digest in spec["files"].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root) or not path.is_file() or sha256(path) != digest:
            raise ValueError(f"Current source differs from the replacement run: {name}")


def validate_audits(audits, cultures, years, models, hypotheses_by_crop):
    """Every reused/replaced fit must have current hypotheses and past-only data."""
    wanted = {(culture, int(year), model) for culture in cultures for year in years for model in models}
    relevant = [audit for audit in audits if audit["culture"] in cultures]
    found = [(audit["culture"], int(audit["year"]), audit["model"]) for audit in relevant]
    if len(found) != len(set(found)) or set(found) != wanted:
        raise ValueError("Incomplete or duplicate model/year audit entries")
    for audit in relevant:
        if audit["hypotheses"] != hypotheses_by_crop[audit["culture"]]:
            raise ValueError(f"Economic hypotheses changed for reused/current crop {audit['culture']}")
        if (audit["training_max"] >= audit["year"] or
                max(audit["training_years"]) != audit["training_max"]):
            raise ValueError("Training chronology is not strictly past-only")
    return relevant


def validate_predictions(rows, cultures, spec, audits, hypotheses_by_crop):
    rows = rows[rows.culture.isin(cultures)].copy()
    if set(rows.culture) != set(cultures):
        raise ValueError("Missing requested crop observations")
    if set(rows.model) != set(spec["options"]["models"]):
        raise ValueError("Missing model predictions")
    if set(rows.year) != set(spec["options"]["years"]):
        raise ValueError("Missing year predictions")
    for culture, group in rows.groupby("culture"):
        assert_common_cohort(group, spec["options"]["models"])
        h = hypotheses_by_crop[culture]
        need = signed_required_income(group.actual_wheat_price, group.actual_wheat_yield,
            h["charges_ble"], h["charges_culture"], h["aide"], h["rotation"])
        accepted = accepted_yield(group.actual_crop_yield_raw, h["qualite"])
        if not np.allclose(need, group.actual_need_eur_ha, rtol=0., atol=1e-9):
            raise ValueError(f"Observed economic needs are stale for {culture}")
        if not np.allclose(accepted, group.accepted_yield_actual, rtol=0., atol=1e-12):
            raise ValueError(f"Accepted yields are stale for {culture}")
        if not (group.refused_fraction == h["qualite"]).all():
            raise ValueError(f"Refused fractions are stale for {culture}")
        if not (group.simulation_history_max < group.year).all():
            raise ValueError("Simulation history includes the evaluated year")
    for audit in audits:
        group = rows[(rows.culture == audit["culture"]) & (rows.year == audit["year"]) &
                     (rows.model == audit["model"])]
        departments = set(group.dep)
        if departments != set(audit["test_departments"]) or len(departments) != audit["n_test"]:
            raise ValueError("Prediction cohort differs from the model audit")
    return rows


def load_source(directory):
    directory = Path(directory)
    loaded = {name: json.loads((directory / name).read_text())
              for name in ("manifest.json", "audit.json", "cohorts.json")}
    prediction_path = directory / "predictions.csv"
    if not prediction_path.exists():
        prediction_path = directory / "predictions.csv.gz"
    loaded["predictions.csv"] = pd.read_csv(prediction_path, dtype={"dep": str}, float_precision="round_trip")
    loaded["artifact_hashes"] = {name: (logical_csv_sha256(prediction_path) if name == "predictions.csv"
                                         else sha256(directory / name)) for name in ARTIFACTS}
    return loaded


def merge_runs(old_directory, replacement_directory, output, replacement_cultures,
               current_root=ROOT, hypothesis_loader=crop_hypotheses):
    """Preserve exact selected rows, while retaining both source provenances."""
    old_directory, replacement_directory, output = map(Path, (old_directory, replacement_directory, output))
    if output.resolve() in (old_directory.resolve(), replacement_directory.resolve()):
        raise ValueError("Composite output must not overwrite either source run")
    old, new = load_source(old_directory), load_source(replacement_directory)
    old_manifest, new_manifest = old["manifest.json"], new["manifest.json"]
    changed = validate_specs(old_manifest, new_manifest, replacement_cultures)
    validate_current_files(new_manifest["spec"], current_root)
    old_spec, new_spec = old_manifest["spec"], new_manifest["spec"]
    cultures = old_spec["options"]["cultures"]
    replaced = set(replacement_cultures)
    reused = set(cultures) - replaced
    hypotheses_by_crop = {culture: hypothesis_loader(culture) for culture in cultures}
    years, models = old_spec["options"]["years"], old_spec["options"]["models"]
    previous_audits = validate_audits(old["audit.json"], reused, years, models, hypotheses_by_crop)
    replacement_audits = validate_audits(new["audit.json"], replaced, years, models, hypotheses_by_crop)
    previous_rows = validate_predictions(old["predictions.csv"], reused, old_spec, previous_audits,
                                         hypotheses_by_crop) if reused else old["predictions.csv"].iloc[:0]
    replacement_rows = validate_predictions(new["predictions.csv"], replaced, new_spec, replacement_audits,
                                             hypotheses_by_crop)
    if set(previous_rows.columns) != set(replacement_rows.columns):
        raise ValueError("Source prediction schemas differ")
    rows = pd.concat([previous_rows, replacement_rows], ignore_index=True).sort_values(
        ["culture", "year", "model", "dep", "contract"]).reset_index(drop=True)
    if rows.duplicated(["culture", "year", "model", "dep", "contract"]).any():
        raise ValueError("Composite contains duplicate model/crop/year cases")
    audit = sorted(previous_audits + replacement_audits, key=lambda x: (x["culture"], x["year"], x["model"]))
    cohorts = {culture: (new if culture in replaced else old)["cohorts.json"][culture] for culture in cultures}
    for culture in replaced:
        if old["cohorts.json"][culture] != new["cohorts.json"][culture]:
            raise ValueError("A cost-only rerun unexpectedly changed an evaluation cohort")
    spec = copy.deepcopy(new_spec)
    spec["options"]["cultures"] = cultures
    spec["seasonal_columns"] = old_spec.get("seasonal_columns", {})

    def source_label(directory):
        resolved = directory.resolve()
        return str(resolved.relative_to(Path(current_root).resolve())) if resolved.is_relative_to(
            Path(current_root).resolve()) else directory.name

    source_details = {
        "previous": {"directory": source_label(old_directory), "signature": old_manifest["signature"],
                     "artifact_sha256": old["artifact_hashes"], "used_cultures": sorted(reused)},
        "replacement": {"directory": source_label(replacement_directory), "signature": new_manifest["signature"],
                        "artifact_sha256": new["artifact_hashes"], "used_cultures": sorted(replaced)}}
    spec["composition"] = {"method": "exact crop rows; no repricing or model modification",
        "sources": source_details, "changed_files": changed, "hypotheses": hypotheses_by_crop,
        "crop_source": {culture: "replacement" if culture in replaced else "previous" for culture in cultures},
        "merge_script_sha256": sha256(Path(__file__)), "effective_fit_count": len(audit)}
    manifest = {"kind": "composite_exact_crop_reuse", "signature": spec_signature(spec), "spec": spec}
    manifest_path = output / "manifest.json"
    if manifest_path.exists() and json.loads(manifest_path.read_text()).get("signature") != manifest["signature"]:
        raise ValueError("Existing composite output has a different provenance; use a new directory")
    output.mkdir(parents=True, exist_ok=True)
    temporary = output / "predictions.csv.tmp"
    rows.to_csv(temporary, index=False)
    temporary.replace(output / "predictions.csv")
    atomic_json(output / "audit.json", audit)
    atomic_json(output / "cohorts.json", cohorts)
    summary = summarize(rows)
    atomic_json(output / "summary.json", summary)
    pd.DataFrame(summary).to_csv(output / "summary.csv", index=False)
    manifest["output_sha256"] = {name: sha256(output / name) for name in
        ("predictions.csv", "audit.json", "cohorts.json", "summary.csv", "summary.json")}
    atomic_json(manifest_path, manifest)
    atomic_json(output / "progress.json", {"status": "completed", "completed": len(audit),
        "total": len(audit), "active": "composite after economic update",
        "reused_fits": len(previous_audits), "rerun_fits": len(replacement_audits)})
    charges = "\n".join(f"| {culture} | {hypotheses_by_crop[culture]['charges_culture']} | "
        f"{'recalcul complet' if culture in replaced else 'résultats identiques réutilisés'} |" for culture in cultures)
    (output / "COMPOSITION.md").write_text(
        "# Composition exacte après mise à jour économique\n\n"
        f"Ce dossier rassemble {len(audit)} ajustements culture–année–modèle : "
        f"{len(previous_audits)} résultats réutilisés à hypothèses strictement identiques et "
        f"{len(replacement_audits)} recalculs complets après modification des charges. "
        "Aucun prix n'a été corrigé par une approximation sur l'ancien résultat.\n\n"
        "| Culture | Charges €/ha | Origine |\n| --- | ---: | --- |\n" + charges + "\n\n"
        "Le script vérifie l'identité des versions de dépendances, modèles, données météo, rendements, "
        "prix du blé, options de simulation et variables saisonnières. Seul `data/cultures.yaml` peut "
        "différer entre les deux exécutions. Pour les cultures réutilisées, les hypothèses numériques "
        "de chaque entraînement doivent être exactement celles de la configuration courante. "
        "Il vérifie aussi les cohortes, années d'apprentissage, besoins économiques et tonnes acceptées.\n\n"
        f"- Source initiale : `{source_label(old_directory)}`, signature `{old_manifest['signature']}`.\n"
        f"- Recalcul : `{source_label(replacement_directory)}`, signature `{new_manifest['signature']}`.\n"
        f"- Source effective par culture et empreintes des fichiers : `manifest.json`.\n\n"
        "Les fichiers `predictions.csv.gz` sont lus automatiquement si le CSV non compressé n'est pas "
        "présent. Les empreintes de provenance portent sur les octets CSV décompressés : compresser "
        "pour publication ne change pas l'identité du résultat.\n\n"
        "Reproduire directement le résultat avec la configuration courante est possible en relançant "
        "les cinq cultures, sans assemblage :\n\n```bash\n"
        "python pipeline/benchmark_multilegumes.py \\\n"
        "  --seasonal-file data/meteo_saisonnier_cultures.csv \\\n"
        "  --samples 20000 --seed 42 --threads 1 \\\n"
        "  --output experiments/multilegumes_full_current\n```\n",
        encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--replacement", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replace-cultures", nargs="+", default=["haricot", "pois"])
    args = parser.parse_args()
    result = merge_runs(args.previous, args.replacement, args.output, args.replace_cultures)
    print(json.dumps({"status": "complete", "signature": result["signature"],
                      "composition": result["spec"]["composition"]["crop_source"]}))
