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


def numpy_execution_profile(runtime):
    """Normalize recorded dispatcher evidence, never infer absent CPU flags.

    A serial launcher may record only its environment override. That evidence
    is weaker than the effective flags captured in a fresh V3 worker process.
    CPU brand and core count are deliberately outside the numerical profile.
    """
    if runtime is None:
        return None
    if not isinstance(runtime, dict):
        raise ValueError("Invalid NumPy execution metadata")
    override_keys = [key for key in ("numpy_dispatch_override", "NPY_DISABLE_CPU_FEATURES") if key in runtime]
    fields = ("numpy_cpu_features", "numpy_cpu_baseline", "numpy_cpu_dispatch", "numpy_version")
    if not override_keys and not any(key in runtime for key in fields):
        return numpy_execution_profile(runtime.get("runtime"))
    profile = {}
    for key in override_keys:
        value = runtime[key]
        if value is not None and not isinstance(value, str):
            raise ValueError("Invalid NumPy dispatcher override")
        normalized = sorted(set(part.strip() for part in (value or "").split(",") if part.strip()))
        if "disabled_features" in profile and profile["disabled_features"] != normalized:
            raise ValueError("Conflicting NumPy dispatcher override aliases")
        profile["disabled_features"] = normalized
    if "numpy_cpu_features" in runtime:
        features = runtime["numpy_cpu_features"]
        if (not isinstance(features, dict) or not features
                or any(not isinstance(key, str) or not key or type(value) is not bool
                       for key, value in features.items())):
            raise ValueError("Invalid effective NumPy CPU feature flags")
        profile["effective_features"] = dict(sorted(features.items()))
    for name in ("numpy_cpu_baseline", "numpy_cpu_dispatch"):
        if name in runtime:
            values = runtime[name]
            if not isinstance(values, list) or any(not isinstance(value, str) or not value for value in values):
                raise ValueError("Invalid NumPy dispatcher capability list")
            profile[name] = sorted(set(values))
    if "numpy_version" in runtime:
        if not isinstance(runtime["numpy_version"], str) or not runtime["numpy_version"]:
            raise ValueError("Invalid recorded NumPy version")
        profile["numpy_version"] = runtime["numpy_version"]
    nested = numpy_execution_profile(runtime.get("runtime"))
    if nested is not None:
        if any(profile[key] != nested[key] for key in set(profile) & set(nested)):
            raise ValueError("Conflicting nested NumPy execution metadata")
        profile.update(nested)
    return profile


def require_matching_numpy_profiles(left, right, context):
    if left != right:
        if left is None or right is None:
            raise ValueError(f"NumPy execution profile missing for one {context}")
        differing = sorted(key for key in set(left) | set(right) if left.get(key) != right.get(key))
        raise ValueError(f"NumPy execution profiles differ for {context}: {differing}")


def execution_environment(directory, partition, package_numpy):
    """Preserve serial/partition evidence and reject mixed resumed profiles."""
    directory = Path(directory)
    evidence = {}
    for name in ("execution_environment.json", "execution.json"):
        path = directory / name
        if path.exists():
            metadata = json.loads(path.read_text())
            if not isinstance(metadata, dict):
                raise ValueError(f"Invalid execution metadata: {name}")
            evidence[name] = {"sha256": sha256(path), "metadata": metadata}
    serial = numpy_execution_profile(evidence.get("execution_environment.json", {}).get("metadata"))
    layout = partition["layout"] if partition is not None else None
    profile = numpy_execution_profile(layout.get("runtime")) if layout else serial
    if layout and serial is not None:
        # An override-only serial declaration can corroborate a richer worker
        # record, but cannot replace missing effective-worker evidence.
        if profile is None or any(profile.get(key) != value for key, value in serial.items()):
            raise ValueError("Serial and partition NumPy execution metadata differ")
    if profile is not None and profile.get("numpy_version", package_numpy) != package_numpy:
        raise ValueError("Recorded NumPy execution version differs from the signed package version")
    if layout and profile is not None and layout.get("start_checkpoint_sha256"):
        history = layout.get("execution_history", [])
        if not history:
            require_matching_numpy_profiles(profile, serial, "reused serial checkpoints")
        def check_history(execution):
            require_matching_numpy_profiles(profile, numpy_execution_profile(execution.get("runtime")),
                                            "resumed execution attempts")
            for previous in execution.get("execution_history", []):
                check_history(previous)
        for previous in history:
            check_history(previous)
    if layout:
        evidence["partition_runtime"] = deepcopy(layout.get("runtime"))
    return {"profile": profile, "evidence": evidence,
        "scope": ("effective_dispatch_and_override" if profile is not None
                  and "effective_features" in profile and "disabled_features" in profile else
                  "recorded_fields_only" if profile is not None else "unrecorded_not_verified")}


def verify_partition_layout(source, directory, archive_hash):
    """Bind a logical full run to its actual immutable crop executions.

    Runtime absolute child directories are descriptive metadata only. Every
    verified child and checkpoint is resolved inside this downloaded run.
    """
    directory = Path(directory).resolve()
    manifest = source["manifest.json"]
    layout = manifest.get("execution_layout")
    layout_file = directory / "partition_execution.json"
    if layout is None:
        if layout_file.exists():
            raise ValueError("Partition execution exists without a completed manifest layout")
        return None
    if (layout.get("kind") != "independent_crop_partitions" or layout.get("status") != "completed"
            or layout.get("workers") not in range(1, 6)
            or layout.get("logical_signature") != manifest["signature"]):
        raise ValueError("Invalid or incomplete partition execution layout")
    if not layout_file.is_file() or json.loads(layout_file.read_text()) != layout:
        raise ValueError("Partition layout file differs from completed manifest")
    if layout.get("source_archive_sha256") != archive_hash:
        raise ValueError("Partition execution used a different source archive")
    if layout.get("thread_environment") != {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}:
        raise ValueError("Partition numerical thread environment differs")
    def verify_execution_files(execution, ancestor=False):
        if (execution.get("logical_signature") != manifest["signature"]
                or execution.get("source_archive_sha256") != archive_hash):
            raise ValueError("Execution history belongs to a different logical run or source archive")
        wrapper_name = execution.get("wrapper_source", "")
        wrapper = (directory / wrapper_name).resolve()
        if (not wrapper_name or Path(wrapper_name).is_absolute()
                or not wrapper.is_relative_to(directory)):
            raise ValueError("Invalid archived partition wrapper path")
        if not wrapper.is_file() or sha256(wrapper) != execution.get("wrapper_sha256"):
            raise ValueError("Archived partition wrapper hash differs")
        auxiliary = execution.get("auxiliary_files", {})
        if not isinstance(auxiliary, dict):
            raise ValueError("Invalid auxiliary execution-file mapping")
        for name, expected in auxiliary.items():
            path = (directory / name).resolve()
            if (Path(name).is_absolute() or not path.is_relative_to(directory)
                    or not path.is_file() or sha256(path) != expected):
                raise ValueError(f"Archived auxiliary execution file differs: {name}")
        saved_at_start = execution.get("start_checkpoint_sha256", {})
        if not isinstance(saved_at_start, dict):
            raise ValueError("Invalid resumed-checkpoint hash mapping")
        for name, expected in saved_at_start.items():
            path = (directory / name).resolve()
            if (Path(name).is_absolute() or not path.is_relative_to(directory)
                    or not path.is_file() or sha256(path) != expected):
                raise ValueError(f"Checkpoint saved before resumption was changed: {name}")
        runtime = execution.get("runtime")
        if runtime is not None:
            if (not isinstance(runtime, dict)
                    or any(not isinstance(runtime.get(key), str) or not runtime[key]
                           for key in ("python", "machine", "platform"))
                    or (runtime.get("logical_cpus") is not None
                        and (not isinstance(runtime["logical_cpus"], int) or runtime["logical_cpus"] < 1))):
                raise ValueError("Invalid execution runtime metadata")
        history = execution.get("execution_history", [])
        if not isinstance(history, list):
            raise ValueError("Invalid execution history")
        for prior in history:
            verify_execution_files(prior, ancestor=True)

    verify_execution_files(layout)
    spec = manifest["spec"]
    cultures, years = spec["options"]["cultures"], spec["options"]["years"]
    models = list(spec["candidates"])
    children = layout.get("children", [])
    if len(children) != len(cultures) or {c["culture"] for c in children} != set(cultures):
        raise ValueError("Partition children do not cover the full crop set exactly once")
    child_specs, child_signatures = {}, {}
    for child in children:
        culture = child["culture"]
        child_dir = (directory / "partitions" / culture).resolve()
        if not child_dir.is_relative_to(directory):
            raise ValueError("Partition child resolves outside the downloaded run")
        expected_spec = deepcopy(spec)
        expected_spec["options"]["cultures"] = [culture]
        expected_signature = spec_signature(expected_spec)
        child_manifest = json.loads((child_dir / "manifest.json").read_text())
        if (child_manifest.get("spec") != expected_spec or child_manifest.get("signature") != expected_signature
                or child.get("signature") != expected_signature or child.get("exit_code") != 0
                or child.get("total") != len(years) * len(models)
                or child.get("spec_difference") != {"options.cultures": [culture]}):
            raise ValueError("Child execution differs from its one-crop restriction")
        child_specs[culture], child_signatures[culture] = expected_spec, expected_signature
    required_outputs = {"predictions.csv", "summary.json", "summary.csv", "audit.json",
        "residual_diagnostics.csv", "cohorts.json", "partition_checkpoint_provenance.json"}
    hashes = layout.get("results", {}).get("outputs_sha256", {})
    if set(hashes) != required_outputs:
        raise ValueError("Partition result hashes do not cover every consolidated output")
    for name, expected in hashes.items():
        actual = logical_csv_sha256(csv_path(directory, name)) if name.endswith(".csv") else sha256(directory / name)
        if actual != expected:
            raise ValueError(f"Consolidated partition output hash differs: {name}")
    provenance_file = directory / "partition_checkpoint_provenance.json"
    records = json.loads(provenance_file.read_text())
    expected_units = {f"{c}-{y}-{m}.json": (c, y, m) for c in cultures for y in years for m in models}
    if len(records) != len(expected_units) or {r["checkpoint"] for r in records} != set(expected_units):
        raise ValueError("Partition checkpoint provenance is incomplete or duplicated")
    if (layout["results"].get("checkpoints") != len(records)
            or layout["results"].get("rows") != len(source["predictions.csv"])):
        raise ValueError("Partition result counts differ from consolidated artifacts")
    for record in records:
        name = record["checkpoint"]
        culture, year, model = expected_units[name]
        parent_path = directory / "checkpoints" / name
        child_path = directory / "partitions" / culture / "checkpoints" / name
        if (not parent_path.is_file() or not child_path.is_file()
                or sha256(parent_path) != record["parent_sha256"]
                or sha256(child_path) != record["child_sha256"]
                or record["child_signature"] != child_signatures[culture]):
            raise ValueError("Partition checkpoint bytes or child signature differ from provenance")
        parent, child = json.loads(parent_path.read_text()), json.loads(child_path.read_text())
        if parent.get("signature") != manifest["signature"] or child.get("signature") != child_signatures[culture]:
            raise ValueError("Partition checkpoint logical/executed signatures differ")
        for kind in ("rows", "audits", "diagnostics"):
            if parent.get(kind) != child.get(kind):
                raise ValueError("Partition consolidation changed a numerical checkpoint payload")
        if parent.get("executed_child_signature") is not None:
            if (parent["executed_child_signature"] != child_signatures[culture]
                    or parent.get("executed_child_checkpoint_sha256") != record["child_sha256"]):
                raise ValueError("Consolidated checkpoint does not bind its actual child execution")
        else:
            reused = child.get("reused_from", {})
            if (reused.get("logical_signature") != manifest["signature"]
                    or reused.get("checkpoint") != name or reused.get("checkpoint_sha256") != record["parent_sha256"]):
                raise ValueError("Reused checkpoint does not bind its original serial execution")
    return {"layout": deepcopy(layout), "layout_sha256": sha256(layout_file),
        "checkpoint_provenance_sha256": sha256(provenance_file),
        "child_executed_specs": child_specs, "verified_checkpoint_pairs": len(records),
        "scope": "The original signature describes a logical full run. Actual executions restrict it "
                 "to one crop; reused serial checkpoints and consolidated child checkpoints are bound separately."}


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
    primary_partition = verify_partition_layout(primary, primary_directory, primary_archive_hash)
    rpg_partition = verify_partition_layout(rpg, rpg_directory, rpg_archive_hash)
    environments = {
        "primary": execution_environment(primary_directory, primary_partition, primary_spec["packages"]["numpy"]),
        "rpg": execution_environment(rpg_directory, rpg_partition, rpg_spec["packages"]["numpy"])}
    require_matching_numpy_profiles(environments["primary"]["profile"], environments["rpg"]["profile"],
                                    "primary and RPG runs")
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
    for label, source, archive_hash, partition in (("primary", primary, primary_archive_hash, primary_partition),
                                                  ("rpg", rpg, rpg_archive_hash, rpg_partition)):
        source_records[label] = {"executed_signature": source["manifest.json"]["signature"],
            "executed_spec": source["manifest.json"]["spec"], "artifact_sha256": source["artifact_hashes"],
            "executed_archive_sha256": archive_hash, "all_tracked_archive_members_verified": True,
            "execution_environment": environments[label]}
        if partition is not None:
            record = source_records[label]
            record["logical_signature"] = record.pop("executed_signature")
            record["logical_spec"] = record.pop("executed_spec")
            record["partition_execution"] = partition
    spec = {"execution": "composition of immutable source runs; no combined run was executed",
        "options": deepcopy(primary_spec["options"]) | {"models": list(candidates)},
        "packages": primary_spec["packages"], "target": primary_spec["target"],
        "evaluation_years": primary_spec["evaluation_years"], "candidates": candidates,
        "composition": {"method": "append renamed RPG rerun predictions without repricing or numeric transformations",
            "model_source": {**{m: "primary" for m in primary_spec["candidates"]},
                             **{m: "rpg" for m in RENAMES.values()}},
            "renames": RENAMES, "allowed_changed_files": sorted(ALLOWED_CHANGED_FILES),
            "changed_files": changed, "rpg_alias": alias, "sources": source_records,
            "numpy_execution_profile_check": ("unrecorded_not_verified" if environments["primary"]["profile"] is None
                                               else environments["primary"]["scope"]),
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
