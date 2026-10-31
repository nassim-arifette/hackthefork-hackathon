"""Compose the frozen advanced benchmark with a genuine RPG-weather rerun.

The second run executes the *unchanged* benchmark and two unchanged agricultural
weather candidates against an explicitly archived input alias. Only the SIM
agricultural CSV and its provenance manifest may differ. This composer renames
those two new experiments; it never adjusts a price or fabricates a prediction.

Both runs require executed-inputs.zip containing every file tracked by their
manifest. The RPG archive additionally includes the original RPG feature CSV
and source manifest. The alias manifest schema ``rpg_weather_alias_v1`` binds
both inputs and their parent hashes, and the alias must be exactly the source
bytes with ``_sim_rpg_`` changed to ``_sim_agri_`` in its header only.

The combined manifest deliberately has no flat executed ``files`` field: each
source run retains its own immutable executed specification and archive hash.
This is a composition, not a claim that the expanded experiment ran in one job.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import gzip
import hashlib
from io import BytesIO
import json
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

import numpy as np
import pandas as pd

from analyze_multilegumes import validate_raw
from benchmark_multilegumes import CONTRACTS, assert_common_cohort, atomic_json, summarize
from contract_economics import evaluate


RENAMES = {"qrf_agri_sparse": "qrf_rpg_weather_sparse", "qrf_agri_dense": "qrf_rpg_weather_dense"}
ALIAS_CSV = "data/sim_agri_features.csv"
ALIAS_MANIFEST = "data/sim_agri_manifest.json"
ALLOWED_CHANGED_FILES = {ALIAS_CSV, ALIAS_MANIFEST}
MANDATORY_FILES = {
    "pipeline/benchmark_advanced.py", "pipeline/advanced_models.py", "pipeline/advanced_weather.py",
    "pipeline/crop_weather.py", "pipeline/fetch_sim_features.py", "pipeline/multicrop_models.py",
    "pipeline/benchmark_multilegumes.py", "pipeline/contract_economics.py", "pipeline/common.py",
    "pipeline/model.py", "data/panel_rendements.csv", "data/meteo_dept_cultures.csv",
    "data/prix_ble.csv", "data/hypotheses.yaml", "data/cultures.yaml",
    "data/meteo_saisonnier_cultures.csv", "data/meteo_advanced_cultures.csv", "data/sim_features.csv",
    "data/soil_features.csv", ALIAS_CSV, ALIAS_MANIFEST,
}
ROW_KEYS = ["culture", "year", "dep", "model", "contract"]
DIAGNOSTIC_KEYS = ["culture", "year", "dep", "model"]
RESIDUAL_COLUMNS = ["crop_residual_standardized", "wheat_residual_standardized"]
OBSERVED_COLUMNS = ["actual_wheat_price", "actual_wheat_yield", "actual_need_eur_ha",
    "actual_crop_yield_raw", "accepted_yield_actual", "refused_fraction", "actual_basis",
    "required_coefficient", "past_mean_accepted", "old_cohort"]


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def spec_signature(spec):
    return digest_bytes(json.dumps(spec, sort_keys=True).encode())


def csv_path(directory, name):
    path = Path(directory) / name
    if not path.exists():
        path = Path(str(path) + ".gz")
    if not path.is_file():
        raise ValueError(f"Missing source artifact {name} in {directory}")
    return path


def logical_csv_sha256(path):
    opener = gzip.open if Path(path).suffix == ".gz" else open
    digest = hashlib.sha256()
    with opener(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_specs(primary_manifest, rpg_manifest):
    for label, manifest in (("primary", primary_manifest), ("RPG", rpg_manifest)):
        if manifest.get("signature") != spec_signature(manifest["spec"]):
            raise ValueError(f"Invalid {label} manifest signature")
        if not MANDATORY_FILES.issubset(manifest["spec"]["files"]):
            raise ValueError(f"Missing mandatory provenance files in {label} manifest")
    primary, rpg = primary_manifest["spec"], rpg_manifest["spec"]
    if primary["packages"] != rpg["packages"]:
        raise ValueError("Package versions changed between source runs")
    if primary["files"].keys() != rpg["files"].keys():
        raise ValueError("Source runs track different code/data files")
    changed = sorted(name for name in primary["files"] if primary["files"][name] != rpg["files"][name])
    if set(changed) - ALLOWED_CHANGED_FILES:
        raise ValueError(f"Code, economics or common inputs changed: {changed}")
    if ALIAS_MANIFEST not in changed:
        raise ValueError("RPG rerun requires its own changed alias provenance manifest")
    if set(rpg["candidates"]) != set(RENAMES):
        raise ValueError("RPG run must contain exactly the two agricultural-weather candidates")
    if not {"trend", *RENAMES}.issubset(primary["candidates"]):
        raise ValueError("Primary run must contain M0 and both original agricultural candidates")
    for name in RENAMES:
        if primary["candidates"][name] != rpg["candidates"][name]:
            raise ValueError(f"Candidate configuration changed: {name}")
    if set(rpg["options"].get("models") or ()) != set(RENAMES):
        raise ValueError("RPG run's explicit model options do not match its two candidates")
    primary_options = {k: v for k, v in primary["options"].items() if k != "models"}
    rpg_options = {k: v for k, v in rpg["options"].items() if k != "models"}
    if primary_options != rpg_options:
        raise ValueError("Crop, year, seed, simulation or thread options changed")
    ignored = {"options", "files", "candidates"}
    if ({k: v for k, v in primary.items() if k not in ignored}
            != {k: v for k, v in rpg.items() if k not in ignored}):
        raise ValueError("Other executed benchmark definitions differ")
    return changed


def read_archive(directory, spec):
    archive = Path(directory) / "executed-inputs.zip"
    if not archive.is_file():
        raise ValueError(f"Executed source archive required: {archive}")
    payload = {}
    with ZipFile(archive) as bundle:
        names = bundle.namelist()
        for name, digest in spec["files"].items():
            parts = PurePosixPath(name)
            if parts.is_absolute() or ".." in parts.parts or names.count(name) != 1:
                raise ValueError(f"Missing, duplicate or invalid archive member: {name}")
            value = bundle.read(name)
            if digest_bytes(value) != digest:
                raise ValueError(f"Executed archive member differs from manifest: {name}")
            payload[name] = value
        if ALIAS_MANIFEST in payload:
            alias = json.loads(payload[ALIAS_MANIFEST])
            if alias.get("kind") == "rpg_weather_alias_v1":
                for field, digest_field in (("source_file", "source_sha256"),
                                            ("source_manifest_file", "source_manifest_sha256")):
                    name = alias[field]
                    parts = PurePosixPath(name)
                    if parts.is_absolute() or ".." in parts.parts or names.count(name) != 1:
                        raise ValueError(f"RPG source missing/duplicated in archive: {name}")
                    value = bundle.read(name)
                    if digest_bytes(value) != alias[digest_field]:
                        raise ValueError(f"RPG original source hash mismatch: {name}")
                    payload[name] = value
    return payload, sha256(archive)


def verify_alias(primary_payload, rpg_payload, primary_spec, rpg_spec):
    alias = json.loads(rpg_payload[ALIAS_MANIFEST])
    if alias.get("kind") != "rpg_weather_alias_v1":
        raise ValueError("Unknown RPG alias provenance format")
    expected = {"alias_file": ALIAS_CSV,
        "alias_sha256": rpg_spec["files"][ALIAS_CSV],
        "parent_alias_sha256": primary_spec["files"][ALIAS_CSV],
        "parent_manifest_sha256": primary_spec["files"][ALIAS_MANIFEST],
        "column_replace": {"from": "_sim_rpg_", "to": "_sim_agri_"}}
    for key, value in expected.items():
        if alias.get(key) != value:
            raise ValueError(f"Invalid RPG alias binding: {key}")
    if alias.get("source_file") != "data/sim_rpg_features.csv":
        raise ValueError("Unexpected original RPG feature path")
    if alias.get("source_manifest_file") != "data/sim_rpg_manifest.json":
        raise ValueError("Unexpected original RPG provenance path")
    original = rpg_payload[alias["source_file"]]
    head, separator, body = original.partition(b"\n")
    if not separator or b"_sim_rpg_" not in head or b"_sim_agri_" in head:
        raise ValueError("Original RPG CSV header does not contain the expected namespace")
    expected_bytes = head.replace(b"_sim_rpg_", b"_sim_agri_") + separator + body
    if rpg_payload[ALIAS_CSV] != expected_bytes:
        raise ValueError("RPG alias changed values or more than the CSV header")
    primary_frame = pd.read_csv(BytesIO(primary_payload[ALIAS_CSV]), dtype={"dep": str}, float_precision="round_trip")
    aliased_frame = pd.read_csv(BytesIO(rpg_payload[ALIAS_CSV]), dtype={"dep": str}, float_precision="round_trip")
    if list(primary_frame.columns) != list(aliased_frame.columns):
        raise ValueError("Aliased RPG feature schema differs from original agricultural input")
    for frame in (primary_frame, aliased_frame):
        if frame.duplicated(["dep", "annee"]).any() or not np.isfinite(frame.drop(columns="dep")).all().all():
            raise ValueError("Invalid or missing RPG alias feature values/keys")
    assert_frame_exact(aliased_frame[["dep", "annee"]], primary_frame[["dep", "annee"]],
                       ["dep", "annee"], "RPG input department/year coverage differs")
    return alias


def load_source(directory):
    directory = Path(directory)
    values = {name: json.loads((directory / name).read_text())
              for name in ("manifest.json", "audit.json", "cohorts.json")}
    hashes = {name: sha256(directory / name) for name in values}
    for name in ("predictions.csv", "residual_diagnostics.csv"):
        path = csv_path(directory, name)
        values[name] = pd.read_csv(path, dtype={"dep": str}, float_precision="round_trip")
        hashes[name] = logical_csv_sha256(path)
    values["artifact_hashes"] = hashes
    return values


def assert_frame_exact(actual, expected, keys, message):
    try:
        pd.testing.assert_frame_equal(actual.sort_values(keys).reset_index(drop=True),
                                      expected.sort_values(keys).reset_index(drop=True), check_exact=True)
    except AssertionError as exc:
        raise ValueError(message) from exc


def validate_source(source, directory):
    spec = source["manifest.json"]["spec"]
    models = list(spec["candidates"])
    cultures, years = spec["options"]["cultures"], spec["options"]["years"]
    if (not cultures or not years or len(set(cultures)) != len(cultures)
            or len(set(years)) != len(years)):
        raise ValueError("Source requires unique nonempty culture/year options")
    wanted = {(c, int(y), m) for c in cultures for y in years for m in models}
    audits = source["audit.json"]
    found = [(a["culture"], int(a["year"]), a["model"]) for a in audits]
    if len(found) != len(set(found)) or set(found) != wanted:
        raise ValueError("Incomplete or duplicate model/year audit entries")
    rows = source["predictions.csv"]
    diagnostics = source["residual_diagnostics.csv"]
    if list(rows.columns).count("model") != 1 or rows.duplicated(ROW_KEYS).any():
        raise ValueError("Duplicate prediction keys")
    if set(rows.culture) != set(cultures) or set(rows.year) != set(years) or set(rows.model) != set(models):
        raise ValueError("Prediction crop/year/model coverage differs from manifest")
    for _, group in rows.groupby("culture"):
        assert_common_cohort(group, models)
    if set(source["cohorts.json"]) != set(cultures):
        raise ValueError("Cohort summaries omit or add a crop")
    for culture, cohort in source["cohorts.json"].items():
        evaluated = rows[(rows.culture == culture) & (rows.year >= 2019)]
        observed = evaluated[["year", "dep", "old_cohort"]].drop_duplicates()
        if observed.duplicated(["year", "dep"]).any():
            raise ValueError("Historical cohort labels differ between candidates")
        modern_only = [[int(r.year), r.dep] for r in observed[~observed.old_cohort].sort_values(["year", "dep"]).itertuples()]
        old_only = list(map(tuple, cohort["old_only"]))
        if (cohort["modern_n"] != len(observed) or cohort["common_n"] != int(observed.old_cohort.sum())
                or cohort["modern_only"] != modern_only
                or cohort["old_n"] != cohort["common_n"] + len(old_only)
                or len(old_only) != len(set(old_only))
                or set(old_only) & set(map(tuple, observed[["year", "dep"]].to_numpy()))):
            raise ValueError("Cohort summary counts/keys differ from predictions")
    if not (rows.simulation_history_max < rows.year).all():
        raise ValueError("Simulation uses current/future years")
    if "dependence_max_year" in rows:
        if not (rows.dependence_max_year.isna() | (rows.dependence_max_year < rows.year)).all():
            raise ValueError("Dependence uses current/future diagnostics")
    if diagnostics.duplicated(DIAGNOSTIC_KEYS).any():
        raise ValueError("Duplicate residual diagnostic keys")
    expected_diagnostics = rows[DIAGNOSTIC_KEYS + RESIDUAL_COLUMNS].drop_duplicates()
    assert_frame_exact(diagnostics, expected_diagnostics, DIAGNOSTIC_KEYS,
                       "Residual diagnostics do not match raw predictions")
    economics_by_crop = {}
    for audit in audits:
        c, year, name = audit["culture"], audit["year"], audit["model"]
        if (not audit["training_years"] or audit["training_max"] >= year
                or max(audit["training_years"]) != audit["training_max"]):
            raise ValueError("Audit training chronology is not strictly past-only")
        if audit.get("candidate") != spec["candidates"][name]:
            raise ValueError("Audit candidate configuration differs from executed manifest")
        if audit.get("dependence_max_year") is not None and audit["dependence_max_year"] >= year:
            raise ValueError("Audit dependence chronology is not strictly past-only")
        h = audit["hypotheses"]
        if c in economics_by_crop and economics_by_crop[c] != h:
            raise ValueError("Economic hypotheses differ across model/year audit entries")
        economics_by_crop[c] = h
        subset = rows[(rows.culture == c) & (rows.year == year) & (rows.model == name)]
        if set(subset.dep) != set(audit["test_departments"]) or subset.dep.nunique() != audit["n_test"]:
            raise ValueError("Prediction cohort differs from audit")
    for culture, group in rows.groupby("culture"):
        h = economics_by_crop[culture]
        need = group.actual_wheat_price * group.actual_wheat_yield - h["charges_ble"] + h["charges_culture"] - h["aide"] - h["rotation"]
        net = group.actual_crop_yield_raw * (1 - h["qualite"])
        if not np.allclose(need, group.actual_need_eur_ha, rtol=0, atol=1e-9):
            raise ValueError("Observed economic needs differ from executed hypotheses")
        if not np.allclose(net, group.accepted_yield_actual, rtol=0, atol=1e-12):
            raise ValueError("Accepted yields differ from executed hypotheses")
        assessed = evaluate(group.coefficient, group.actual_basis, group.actual_need_eur_ha, group.accepted_yield_actual)
        for column, calculated in (("paid_actual_eur_ha", assessed["paid_eur_ha"]),
                                    ("shortfall_eur_ha", assessed["shortfall_eur_ha"])):
            if not np.allclose(group[column], calculated, rtol=0, atol=1e-9):
                raise ValueError(f"Raw economic result inconsistent: {column}")
        if not np.array_equal(group.held.to_numpy(), assessed["held"]):
            raise ValueError("Raw held verdict inconsistent with >= margin rule")
    checkpoints = Path(directory) / "checkpoints"
    if checkpoints.exists():
        paths = list(checkpoints.glob("*.json"))
        expected_names = {f"{c}-{y}-{m}.json" for c, y, m in wanted}
        if {p.name for p in paths} != expected_names:
            raise ValueError("Incomplete or unexpected checkpoint set")
        audit_map = {(a["culture"], a["year"], a["model"]): a for a in audits}
        for path in paths:
            saved = json.loads(path.read_text())
            if saved["signature"] != source["manifest.json"]["signature"] or len(saved["audits"]) != 1:
                raise ValueError("Checkpoint signature/audit mismatch")
            audit = saved["audits"][0]
            key = (audit["culture"], audit["year"], audit["model"])
            if audit != audit_map.get(key):
                raise ValueError("Checkpoint audit differs from aggregate")
            subset = rows[(rows.culture == key[0]) & (rows.year == key[1]) & (rows.model == key[2])]
            # None/NaN in dependence metadata is the same explicit missing value.
            recovered = pd.DataFrame(saved["rows"]).reindex(columns=rows.columns)
            recovered = recovered.astype(subset.dtypes.to_dict())
            assert_frame_exact(recovered, subset, ROW_KEYS, "Checkpoint predictions differ from aggregate")
    return economics_by_crop


def merge_runs(primary_directory, rpg_directory, output):
    primary_directory, rpg_directory, output = map(Path, (primary_directory, rpg_directory, output))
    if output.resolve() in (primary_directory.resolve(), rpg_directory.resolve()):
        raise ValueError("Composition output must differ from its immutable source directories")
    primary, rpg = load_source(primary_directory), load_source(rpg_directory)
    changed = validate_specs(primary["manifest.json"], rpg["manifest.json"])
    primary_spec, rpg_spec = primary["manifest.json"]["spec"], rpg["manifest.json"]["spec"]
    primary_payload, primary_archive_hash = read_archive(primary_directory, primary_spec)
    rpg_payload, rpg_archive_hash = read_archive(rpg_directory, rpg_spec)
    alias = verify_alias(primary_payload, rpg_payload, primary_spec, rpg_spec)
    primary_economics = validate_source(primary, primary_directory)
    if validate_source(rpg, rpg_directory) != primary_economics:
        raise ValueError("Economic hypotheses differ between source runs")
    if primary["cohorts.json"] != rpg["cohorts.json"]:
        raise ValueError("Historical/cohort summaries differ between source runs")
    primary_rows, rpg_rows = primary["predictions.csv"], rpg["predictions.csv"]
    if list(primary_rows.columns) != list(rpg_rows.columns):
        raise ValueError("Prediction schemas differ despite identical benchmark sources")
    observed_keys = ["culture", "year", "dep", "contract"]
    reference = primary_rows[primary_rows.model == "trend"][observed_keys + OBSERVED_COLUMNS]
    for _, group in rpg_rows.groupby("model"):
        assert_frame_exact(group[observed_keys + OBSERVED_COLUMNS], reference, observed_keys,
                           "RPG rerun changed observed economic outcomes or cohort")
    renamed = rpg_rows.copy()
    renamed["model"] = renamed.model.map(RENAMES)
    combined = pd.concat([primary_rows, renamed], ignore_index=True)
    validate_raw(combined)
    candidates = deepcopy(primary_spec["candidates"])
    for old, new in RENAMES.items():
        candidates[new] = deepcopy(rpg_spec["candidates"][old]) | {
            "original_name": old, "feature_group": "rpg_weather", "ablation_parent": old,
            "feature_semantics": "RPG2015 crop-specific SIM weather weights; documented CLC fallback",
            "executed_candidate": deepcopy(rpg_spec["candidates"][old])}
    renamed_audits = deepcopy(rpg["audit.json"])
    for audit in renamed_audits:
        old = audit["model"]
        audit["model"], audit["original_name"] = RENAMES[old], old
        audit["executed_candidate"] = audit["candidate"]
        audit["candidate"] = deepcopy(candidates[RENAMES[old]])
    renamed_diagnostics = rpg["residual_diagnostics.csv"].copy()
    renamed_diagnostics["model"] = renamed_diagnostics.model.map(RENAMES)
    diagnostics = pd.concat([primary["residual_diagnostics.csv"], renamed_diagnostics], ignore_index=True)
    source_records = {}
    for label, source, archive_hash in (("primary", primary, primary_archive_hash), ("rpg", rpg, rpg_archive_hash)):
        source_records[label] = {"executed_signature": source["manifest.json"]["signature"],
            "executed_spec": source["manifest.json"]["spec"], "artifact_sha256": source["artifact_hashes"],
            "executed_archive_sha256": archive_hash, "all_tracked_archive_members_verified": True}
    spec = {"execution": "composition of immutable source runs; no combined run was executed",
        "options": deepcopy(primary_spec["options"]) | {"models": list(candidates)},
        "packages": primary_spec["packages"], "target": primary_spec["target"],
        "evaluation_years": primary_spec["evaluation_years"], "candidates": candidates,
        "composition": {"method": "append renamed RPG rerun predictions without repricing or numeric transformations",
            "model_source": {**{m: "primary" for m in primary_spec["candidates"]},
                             **{m: "rpg" for m in RENAMES.values()}},
            "renames": RENAMES, "allowed_changed_files": sorted(ALLOWED_CHANGED_FILES),
            "changed_files": changed, "rpg_alias": alias, "sources": source_records,
            "composer_sha256": sha256(Path(__file__))}}
    signature = spec_signature(spec)
    output.mkdir(parents=True, exist_ok=True)
    if (output / "manifest.json").exists() and json.loads((output / "manifest.json").read_text())["signature"] != signature:
        raise ValueError("Composition input/code changed; use a new output directory")
    combined.to_csv(output / "predictions.csv", index=False)
    diagnostics.to_csv(output / "residual_diagnostics.csv", index=False)
    # Verify round-trip exactness of every numeric forecast after serialisation.
    restored = pd.read_csv(output / "predictions.csv", dtype={"dep": str}, float_precision="round_trip")
    assert_frame_exact(restored[restored.model.isin(primary_spec["candidates"])], primary_rows,
                       ROW_KEYS, "Primary predictions changed during composition")
    assert_frame_exact(restored[restored.model.isin(RENAMES.values())], renamed,
                       ROW_KEYS, "RPG predictions changed during composition")
    summary = summarize(combined)
    pd.DataFrame(summary).to_csv(output / "summary.csv", index=False)
    atomic_json(output / "summary.json", summary)
    atomic_json(output / "audit.json", primary["audit.json"] + renamed_audits)
    atomic_json(output / "cohorts.json", primary["cohorts.json"])
    names = ("predictions.csv", "residual_diagnostics.csv", "summary.csv", "summary.json", "audit.json", "cohorts.json")
    manifest = {"signature": signature, "spec": spec,
                "output_sha256": {name: sha256(output / name) for name in names}}
    atomic_json(output / "manifest.json", manifest)
    (output / "COMPOSITION.md").write_text(
        "# Composition de l'expérience météo RPG\n\n"
        "Le benchmark principal est conservé intégralement. Deux expériences supplémentaires "
        "utilisent le même code et les mêmes réglages avec des variables SIM pondérées par les "
        "parcelles RPG2015 ; le repli CLC est documenté dans la provenance source.\n\n"
        "Les alias techniques `qrf_agri_sparse` et `qrf_agri_dense` du second calcul sont renommés "
        "`qrf_rpg_weather_sparse` et `qrf_rpg_weather_dense`. Aucun prix, rendement simulé, paiement "
        "ou verdict n'est recalculé par l'assemblage. Les spécifications exécutées et archives "
        "restent séparées dans `manifest.json`, avec contrôle de chaque entrée archivée, des "
        "cohortes, de l'économie observée et de l'identité des valeurs après export.\n", encoding="utf-8")
    return manifest


def parser():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--primary", type=Path, required=True)
    ap.add_argument("--rpg", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    return ap


if __name__ == "__main__":
    arguments = parser().parse_args()
    result = merge_runs(arguments.primary, arguments.rpg, arguments.output)
    print(json.dumps({"signature": result["signature"], "output": str(arguments.output)}))
