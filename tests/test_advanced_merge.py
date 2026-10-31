"""Reject changed execution inputs and preserve append-only RPG predictions."""
from copy import deepcopy
import gzip
import json
from zipfile import ZipFile

import pandas as pd
import pytest

from contract_economics import contract_basis, evaluate
from merge_advanced_runs import (ALIAS_CSV, ALIAS_MANIFEST, MANDATORY_FILES, RENAMES,
    digest_bytes, merge_runs, sha256, spec_signature, validate_specs)


def fixtures(tmp_path):
    primary, rpg = tmp_path / "primary", tmp_path / "rpg"
    payload = {name: ("fixed input " + name).encode() for name in MANDATORY_FILES}
    payload[ALIAS_CSV] = b"dep,annee,lentille_sim_agri_swi\n01,2018,0.4\n02,2018,0.5\n"
    payload[ALIAS_MANIFEST] = b'{"source":"CLC2012"}'
    rpg_payload = deepcopy(payload)
    original = b"dep,annee,lentille_sim_rpg_swi\n01,2018,0.6\n02,2018,0.8\n"
    original_manifest = b'{"source":"RPG2015","fallback":"CLC2012"}'
    rpg_payload["data/sim_rpg_features.csv"] = original
    rpg_payload["data/sim_rpg_manifest.json"] = original_manifest
    rpg_payload[ALIAS_CSV] = original.replace(b"_sim_rpg_", b"_sim_agri_")
    alias = {"kind": "rpg_weather_alias_v1", "source_file": "data/sim_rpg_features.csv",
        "source_sha256": digest_bytes(original), "source_manifest_file": "data/sim_rpg_manifest.json",
        "source_manifest_sha256": digest_bytes(original_manifest), "alias_file": ALIAS_CSV,
        "alias_sha256": digest_bytes(rpg_payload[ALIAS_CSV]),
        "parent_alias_sha256": digest_bytes(payload[ALIAS_CSV]),
        "parent_manifest_sha256": digest_bytes(payload[ALIAS_MANIFEST]),
        "column_replace": {"from": "_sim_rpg_", "to": "_sim_agri_"}}
    rpg_payload[ALIAS_MANIFEST] = json.dumps(alias).encode()
    candidates = {"trend": {"feature_group": "legacy"},
        "qrf_agri_sparse": {"feature_group": "agri", "distribution": "three"},
        "qrf_agri_dense": {"feature_group": "agri", "distribution": "dense"}}
    h = {"charges_ble": 700, "charges_culture": 500, "aide": 105, "rotation": 150, "qualite": .1}
    manifests = []
    for directory, source_payload, models in ((primary, payload, list(candidates)), (rpg, rpg_payload, list(RENAMES))):
        directory.mkdir()
        spec = {"options": {"cultures": ["lentille"], "years": [2018, 2019], "samples": 20000,
            "seed": 42, "threads": 1, "models": None if directory == primary else list(RENAMES)},
            "packages": {"numpy": "2.3.5"}, "target": .8, "evaluation_years": [2019],
            "files": {name: digest_bytes(source_payload[name]) for name in MANDATORY_FILES},
            "candidates": {name: deepcopy(candidates[name]) for name in models}, "unavailable_candidates": {}}
        manifest = {"spec": spec, "signature": spec_signature(spec)}
        rows, audits, diagnostics = [], [], []
        for year in (2018, 2019):
            for model in models:
                for dep in ("01", "02"):
                    diagnostic = {"culture": "lentille", "year": year, "dep": dep, "model": model,
                        "crop_residual_standardized": float(int(dep)), "wheat_residual_standardized": float(int(dep)) / 2}
                    diagnostics.append(diagnostic)
                    for shape in ("fixed", "indexed", "tiers"):
                        need = 200 * 5 - 700 + 500 - 105 - 150
                        basis = float(contract_basis(shape, 1.8, 200, 1.8))
                        coefficient = (1000. if shape != "indexed" else 5.) + (2 if directory == rpg else 0)
                        calculated = evaluate(coefficient, basis, need, 1.8)
                        residual = need - float(calculated["paid_eur_ha"])
                        rows.append({**diagnostic, "contract": shape, "region": "R1",
                            "actual_wheat_price": 200., "actual_wheat_yield": 5., "actual_need_eur_ha": need,
                            "actual_crop_yield_raw": 2., "accepted_yield_actual": 1.8, "refused_fraction": .1,
                            "simulation_history_max": year - 1, "old_cohort": True,
                            "coefficient": coefficient, "required_coefficient": need / basis,
                            "actual_basis": basis, "past_mean_accepted": 1.8,
                            "simulation_basis_mean": basis, "simulation_accepted_mean": 1.8,
                            "held": bool(calculated["held"]), "paid_actual_eur_ha": float(calculated["paid_eur_ha"]),
                            "shortfall_eur_ha": float(calculated["shortfall_eur_ha"]),
                            "expected_unit_cost": coefficient * basis / 1.8,
                            "contract_loss_eur_ha": max(.8 * residual, -.2 * residual),
                            "dependence_max_year": None})
                audits.append({"culture": "lentille", "year": year, "model": model,
                    "candidate": candidates[model], "hypotheses": h, "training_years": list(range(2010, year)),
                    "training_max": year - 1, "test_departments": ["01", "02"], "n_test": 2,
                    "dependence_max_year": None})
        cohorts = {"lentille": {"old_n": 2, "modern_n": 2, "common_n": 2,
                                "old_only": [], "modern_only": []}}
        for name, value in (("manifest.json", manifest), ("audit.json", audits), ("cohorts.json", cohorts)):
            (directory / name).write_text(json.dumps(value))
        pd.DataFrame(rows).to_csv(directory / "predictions.csv", index=False)
        pd.DataFrame(diagnostics).to_csv(directory / "residual_diagnostics.csv", index=False)
        with ZipFile(directory / "executed-inputs.zip", "w") as archive:
            for name, content in source_payload.items():
                archive.writestr(name, content)
        manifests.append(manifest)
    return primary, rpg, manifests


def resign(manifest):
    manifest["signature"] = spec_signature(manifest["spec"])
    return manifest


def test_composition_preserves_all_values_and_both_executed_sources(tmp_path):
    primary, rpg, source_manifests = fixtures(tmp_path)
    output = tmp_path / "combined"
    manifest = merge_runs(primary, rpg, output)
    rows = pd.read_csv(output / "predictions.csv", dtype={"dep": str}, float_precision="round_trip")
    for directory, names in ((primary, {}), (rpg, RENAMES)):
        expected = pd.read_csv(directory / "predictions.csv", dtype={"dep": str}, float_precision="round_trip")
        if names:
            expected.model = expected.model.map(names)
        actual = rows[rows.model.isin(expected.model)].reset_index(drop=True)
        pd.testing.assert_frame_equal(actual, expected, check_exact=True)
    assert "files" not in manifest["spec"]
    assert manifest["signature"] == spec_signature(manifest["spec"])
    for label, source in zip(("primary", "rpg"), source_manifests):
        assert manifest["spec"]["composition"]["sources"][label]["executed_spec"] == source["spec"]
    assert len(json.loads((output / "audit.json").read_text())) == 10
    assert manifest["spec"]["candidates"]["qrf_rpg_weather_dense"]["ablation_parent"] == "qrf_agri_dense"


@pytest.mark.parametrize("path", ["pipeline/advanced_models.py", "pipeline/benchmark_advanced.py",
    "data/hypotheses.yaml", "data/prix_ble.csv", "data/sim_features.csv", "data/soil_features.csv"])
def test_changed_common_sources_or_economics_are_rejected(tmp_path, path):
    _, _, manifests = fixtures(tmp_path)
    primary, rpg = manifests
    rpg["spec"]["files"][path] = "changed"
    with pytest.raises(ValueError, match="common inputs changed"):
        validate_specs(primary, resign(rpg))


@pytest.mark.parametrize("mutation,message", [
    (lambda s: s["packages"].update(numpy="other"), "Package versions"),
    (lambda s: s["options"].update(seed=43), "seed"),
    (lambda s: s["candidates"]["qrf_agri_dense"].update(distribution="other"), "Candidate configuration"),
])
def test_versions_options_and_hyperparameters_must_match(tmp_path, mutation, message):
    _, _, manifests = fixtures(tmp_path)
    primary, rpg = manifests
    mutation(rpg["spec"])
    with pytest.raises(ValueError, match=message):
        validate_specs(primary, resign(rpg))


def test_modified_archived_input_is_rejected(tmp_path):
    primary, rpg, _ = fixtures(tmp_path)
    path = rpg / "executed-inputs.zip"
    with ZipFile(path) as archive:
        payload = {name: archive.read(name) for name in archive.namelist()}
    payload["pipeline/advanced_models.py"] += b"\nchanged"
    with ZipFile(path, "w") as archive:
        for name, content in payload.items():
            archive.writestr(name, content)
    with pytest.raises(ValueError, match="archive member differs"):
        merge_runs(primary, rpg, tmp_path / "bad")


def test_alias_may_only_change_header_not_feature_values(tmp_path):
    primary, rpg, manifests = fixtures(tmp_path)
    manifest = manifests[1]
    path = rpg / "executed-inputs.zip"
    with ZipFile(path) as archive:
        payload = {name: archive.read(name) for name in archive.namelist()}
    payload[ALIAS_CSV] = payload[ALIAS_CSV].replace(b"0.6", b"0.7")
    alias = json.loads(payload[ALIAS_MANIFEST])
    alias["alias_sha256"] = digest_bytes(payload[ALIAS_CSV])
    payload[ALIAS_MANIFEST] = json.dumps(alias).encode()
    for name in (ALIAS_CSV, ALIAS_MANIFEST):
        manifest["spec"]["files"][name] = digest_bytes(payload[name])
    (rpg / "manifest.json").write_text(json.dumps(resign(manifest)))
    with ZipFile(path, "w") as archive:
        for name, content in payload.items():
            archive.writestr(name, content)
    with pytest.raises(ValueError, match="changed values"):
        merge_runs(primary, rpg, tmp_path / "bad")


def test_changed_observed_economics_are_rejected(tmp_path):
    primary, rpg, _ = fixtures(tmp_path)
    rows = pd.read_csv(rpg / "predictions.csv", dtype={"dep": str})
    rows["actual_need_eur_ha"] -= 100
    rows.to_csv(rpg / "predictions.csv", index=False)
    with pytest.raises(ValueError, match="Observed economic needs"):
        merge_runs(primary, rpg, tmp_path / "bad")


def test_future_audit_and_partial_checkpoint_set_are_rejected(tmp_path):
    primary, rpg, _ = fixtures(tmp_path)
    path = rpg / "audit.json"
    original = json.loads(path.read_text())
    changed = deepcopy(original)
    changed[0]["training_max"] = changed[0]["year"]
    path.write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="chronology"):
        merge_runs(primary, rpg, tmp_path / "bad_audit")
    path.write_text(json.dumps(original))
    (rpg / "checkpoints").mkdir()
    (rpg / "checkpoints/partial.json").write_text("{}")
    with pytest.raises(ValueError, match="checkpoint set"):
        merge_runs(primary, rpg, tmp_path / "bad_checkpoint")


def test_gzip_artifacts_keep_logical_csv_provenance_and_composition(tmp_path):
    primary, rpg, _ = fixtures(tmp_path)
    plain = merge_runs(primary, rpg, tmp_path / "plain")
    for directory in (primary, rpg):
        for name in ("predictions.csv", "residual_diagnostics.csv"):
            path = directory / name
            path.with_suffix(path.suffix + ".gz").write_bytes(gzip.compress(path.read_bytes()))
            path.unlink()
    compressed = merge_runs(primary, rpg, tmp_path / "compressed")
    assert plain["signature"] == compressed["signature"]
    assert plain["output_sha256"] == compressed["output_sha256"]


def partition_fixture(primary):
    """Represent actual crop execution plus a reused serial checkpoint."""
    from benchmark_multilegumes import summarize
    manifest = json.loads((primary / "manifest.json").read_text())
    rows = pd.read_csv(primary / "predictions.csv", dtype={"dep": str}, float_precision="round_trip")
    diagnostics = pd.read_csv(primary / "residual_diagnostics.csv", dtype={"dep": str}, float_precision="round_trip")
    audits = json.loads((primary / "audit.json").read_text())
    child_dir = primary / "partitions/lentille"
    (child_dir / "checkpoints").mkdir(parents=True)
    (primary / "checkpoints").mkdir()
    child_spec = deepcopy(manifest["spec"])
    child_spec["options"]["cultures"] = ["lentille"]
    child_signature = spec_signature(child_spec)
    (child_dir / "manifest.json").write_text(json.dumps({"spec": child_spec, "signature": child_signature}))
    provenance = []
    for i, audit in enumerate(audits):
        year, model = audit["year"], audit["model"]
        name = f"lentille-{year}-{model}.json"
        part = rows[(rows.year == year) & (rows.model == model)]
        diags = diagnostics[(diagnostics.year == year) & (diagnostics.model == model)]
        payload = {"rows": part.astype(object).where(pd.notna(part), None).to_dict("records"),
                   "audits": [audit], "diagnostics": diags.to_dict("records")}
        parent_path, child_path = primary / "checkpoints" / name, child_dir / "checkpoints" / name
        parent = {"signature": manifest["signature"], **payload}
        child = {"signature": child_signature, **payload}
        if i == 0:
            parent_path.write_text(json.dumps(parent))
            child["reused_from"] = {"logical_signature": manifest["signature"],
                                    "checkpoint": name, "checkpoint_sha256": sha256(parent_path)}
            child_path.write_text(json.dumps(child))
        else:
            child_path.write_text(json.dumps(child))
            parent.update(executed_child_signature=child_signature,
                          executed_child_checkpoint_sha256=sha256(child_path))
            parent_path.write_text(json.dumps(parent))
        provenance.append({"checkpoint": name, "parent_sha256": sha256(parent_path),
                           "child_sha256": sha256(child_path), "child_signature": child_signature})
    (primary / "partition_checkpoint_provenance.json").write_text(json.dumps(provenance))
    summary = summarize(rows)
    (primary / "summary.json").write_text(json.dumps(summary))
    pd.DataFrame(summary).to_csv(primary / "summary.csv", index=False)
    wrapper = primary / "parallel_advanced.executed.py"
    wrapper.write_text("# immutable wrapper fixture\n")
    outputs = ["predictions.csv", "summary.json", "summary.csv", "audit.json",
               "residual_diagnostics.csv", "cohorts.json", "partition_checkpoint_provenance.json"]
    layout = {"kind": "independent_crop_partitions", "status": "completed", "workers": 2,
        "logical_signature": manifest["signature"], "source_archive_sha256": sha256(primary / "executed-inputs.zip"),
        "wrapper_source": wrapper.name, "wrapper_sha256": sha256(wrapper),
        "thread_environment": {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"},
        "children": [{"culture": "lentille", "directory": "/content/runtime/partitions/lentille",
            "signature": child_signature, "exit_code": 0, "total": len(audits),
            "spec_difference": {"options.cultures": ["lentille"]}}],
        "results": {"rows": len(rows), "checkpoints": len(provenance),
                    "outputs_sha256": {name: sha256(primary / name) for name in outputs}}}
    (primary / "partition_execution.json").write_text(json.dumps(layout))
    manifest["execution_layout"] = layout
    (primary / "manifest.json").write_text(json.dumps(manifest))
    return child_dir


def test_partition_execution_keeps_logical_and_actual_specs_distinct(tmp_path):
    primary, rpg, _ = fixtures(tmp_path)
    partition_fixture(primary)
    result = merge_runs(primary, rpg, tmp_path / "combined")
    source = result["spec"]["composition"]["sources"]["primary"]
    assert "executed_spec" not in source
    assert source["logical_spec"]["options"]["cultures"] == ["lentille"]
    assert source["partition_execution"]["verified_checkpoint_pairs"] == 6
    assert source["partition_execution"]["child_executed_specs"]["lentille"]["options"]["cultures"] == ["lentille"]


@pytest.mark.parametrize("tamper,message", [("wrapper", "wrapper hash"),
    ("child_spec", "one-crop restriction"), ("checkpoint", "checkpoint bytes")])
def test_partition_proofs_must_match_saved_executions(tmp_path, tamper, message):
    primary, rpg, _ = fixtures(tmp_path)
    child_dir = partition_fixture(primary)
    if tamper == "wrapper":
        (primary / "parallel_advanced.executed.py").write_text("# modified\n")
    elif tamper == "child_spec":
        path = child_dir / "manifest.json"
        child = json.loads(path.read_text())
        child["spec"]["options"]["seed"] = 43
        child["signature"] = spec_signature(child["spec"])
        path.write_text(json.dumps(child))
    else:
        path = next((child_dir / "checkpoints").glob("*.json"))
        path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match=message):
        merge_runs(primary, rpg, tmp_path / "bad")


def test_auxiliary_acceleration_source_and_execution_history_are_preserved(tmp_path):
    primary, rpg, _ = fixtures(tmp_path)
    partition_fixture(primary)
    manifest = json.loads((primary / "manifest.json").read_text())
    layout = manifest["execution_layout"]
    prior = deepcopy(layout)
    prior["status"] = "interrupted"
    original_wrapper = primary / prior["wrapper_source"]
    archive = primary / "executions/attempt1"
    archive.mkdir(parents=True)
    prior_wrapper = archive / "parallel_advanced.py"
    prior_wrapper.write_bytes(original_wrapper.read_bytes())
    prior["wrapper_source"] = str(prior_wrapper.relative_to(primary))
    helper = primary / "executions/batched_prediction.py"
    helper.write_text("# exact batched prediction fixture\n")
    layout["auxiliary_files"] = {str(helper.relative_to(primary)): sha256(helper)}
    layout["execution_history"] = [prior]
    checkpoint = next((primary / "partitions/lentille/checkpoints").glob("*.json"))
    layout["start_checkpoint_sha256"] = {str(checkpoint.relative_to(primary)): sha256(checkpoint)}
    layout["workers"] = 5
    layout["runtime"] = {"python": "3.13.5", "machine": "x86_64", "logical_cpus": 12, "platform": "Linux"}
    (primary / "partition_execution.json").write_text(json.dumps(layout))
    (primary / "manifest.json").write_text(json.dumps(manifest))
    result = merge_runs(primary, rpg, tmp_path / "with_history")
    copied = result["spec"]["composition"]["sources"]["primary"]["partition_execution"]["layout"]
    assert copied["execution_history"] == [prior]
    assert copied["auxiliary_files"] == layout["auxiliary_files"]
    assert copied["workers"] == 5 and copied["runtime"]["logical_cpus"] == 12
    assert copied["start_checkpoint_sha256"] == layout["start_checkpoint_sha256"]
    helper.write_text("# modified acceleration code\n")
    with pytest.raises(ValueError, match="auxiliary execution file differs"):
        merge_runs(primary, rpg, tmp_path / "bad_auxiliary")


def test_pre_restart_checkpoint_hash_is_binding(tmp_path):
    primary, rpg, _ = fixtures(tmp_path)
    partition_fixture(primary)
    manifest = json.loads((primary / "manifest.json").read_text())
    layout = manifest["execution_layout"]
    checkpoint = next((primary / "partitions/lentille/checkpoints").glob("*.json"))
    layout["start_checkpoint_sha256"] = {str(checkpoint.relative_to(primary)): "incorrect"}
    (primary / "partition_execution.json").write_text(json.dumps(layout))
    (primary / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="saved before resumption"):
        merge_runs(primary, rpg, tmp_path / "bad_resumption")


def numpy_runtime(**extra):
    return {"python": "3.13.16", "machine": "x86_64", "logical_cpus": 12, "platform": "Linux",
        "numpy_version": "2.3.5", "numpy_dispatch_override": "AVX512F,AVX512_SKX",
        "numpy_cpu_features": {"SSE2": True, "AVX2": True, "AVX512F": False, "AVX512_SKX": False},
        "numpy_cpu_baseline": ["SSE", "SSE2"], "numpy_cpu_dispatch": ["AVX2", "AVX512_SKX"], **extra}


def record_partition_runtime(directory, runtime):
    manifest = json.loads((directory / "manifest.json").read_text())
    manifest["execution_layout"]["runtime"] = runtime
    (directory / "manifest.json").write_text(json.dumps(manifest))
    (directory / "partition_execution.json").write_text(json.dumps(manifest["execution_layout"]))


def record_serial_runtime(directory, runtime):
    record = {"NPY_DISABLE_CPU_FEATURES": runtime["numpy_dispatch_override"],
              "runtime": runtime, "reason": "Fresh subprocess before importing NumPy"}
    (directory / "execution_environment.json").write_text(json.dumps(record))


def test_numpy_profile_matches_serial_and_partition_without_requiring_same_cpu_brand(tmp_path):
    primary, rpg, _ = fixtures(tmp_path)
    partition_fixture(primary)
    record_partition_runtime(primary, numpy_runtime())
    record_serial_runtime(rpg, numpy_runtime(machine="a_different_recorded_cpu", logical_cpus=32))
    (primary / "execution.json").write_text(json.dumps({"partition_pid": 123, "status": "launched"}))
    result = merge_runs(primary, rpg, tmp_path / "combined")
    composition = result["spec"]["composition"]
    assert composition["numpy_execution_profile_check"] == "effective_dispatch_and_override"
    environments = {key: source["execution_environment"] for key, source in composition["sources"].items()}
    assert environments["primary"]["profile"] == environments["rpg"]["profile"]
    assert environments["primary"]["evidence"]["execution.json"]["sha256"] == sha256(primary / "execution.json")
    assert environments["rpg"]["evidence"]["execution_environment.json"]["metadata"]["runtime"]["logical_cpus"] == 32


@pytest.mark.parametrize("change", ["override", "effective_flags", "missing_profile", "missing_override", "missing_flags"])
def test_numpy_execution_profile_mismatches_are_rejected(tmp_path, change):
    primary, rpg, _ = fixtures(tmp_path)
    partition_fixture(primary)
    record_partition_runtime(primary, numpy_runtime())
    runtime = numpy_runtime()
    if change == "override":
        runtime["numpy_dispatch_override"] = None
    elif change == "effective_flags":
        runtime["numpy_cpu_features"]["AVX512F"] = True
    elif change == "missing_flags":
        runtime.pop("numpy_cpu_features")
    if change != "missing_profile":
        record_serial_runtime(rpg, runtime)
    if change == "missing_override":
        path = rpg / "execution_environment.json"
        metadata = json.loads(path.read_text())
        metadata.pop("NPY_DISABLE_CPU_FEATURES")
        metadata["runtime"].pop("numpy_dispatch_override")
        path.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="NumPy execution profile"):
        merge_runs(primary, rpg, tmp_path / "bad")


def test_legacy_missing_numpy_evidence_is_not_claimed_verified(tmp_path):
    primary, rpg, _ = fixtures(tmp_path)
    result = merge_runs(primary, rpg, tmp_path / "legacy")
    assert result["spec"]["composition"]["numpy_execution_profile_check"] == "unrecorded_not_verified"


def test_override_only_serial_metadata_is_not_claimed_effective_flags(tmp_path):
    primary, rpg, _ = fixtures(tmp_path)
    for directory in (primary, rpg):
        (directory / "execution_environment.json").write_text(json.dumps({"NPY_DISABLE_CPU_FEATURES": "AVX512F"}))
    result = merge_runs(primary, rpg, tmp_path / "legacy_serial")
    assert result["spec"]["composition"]["numpy_execution_profile_check"] == "recorded_fields_only"


@pytest.mark.parametrize("prior_recorded", [True, False])
def test_resumed_checkpoints_cannot_hide_different_or_unrecorded_numpy_profile(tmp_path, prior_recorded):
    primary, rpg, _ = fixtures(tmp_path)
    partition_fixture(primary)
    record_partition_runtime(primary, numpy_runtime())
    record_serial_runtime(rpg, numpy_runtime())
    manifest = json.loads((primary / "manifest.json").read_text())
    layout = manifest["execution_layout"]
    prior = deepcopy(layout)
    prior["status"] = "interrupted"
    if prior_recorded:
        prior["runtime"]["numpy_dispatch_override"] = None
    else:
        prior.pop("runtime")
    checkpoint = next((primary / "partitions/lentille/checkpoints").glob("*.json"))
    layout["execution_history"] = [prior]
    layout["start_checkpoint_sha256"] = {str(checkpoint.relative_to(primary)): sha256(checkpoint)}
    (primary / "manifest.json").write_text(json.dumps(manifest))
    (primary / "partition_execution.json").write_text(json.dumps(layout))
    with pytest.raises(ValueError, match="NumPy execution profile.*resumed"):
        merge_runs(primary, rpg, tmp_path / "mixed")


def test_same_numpy_profile_allows_partitioned_reruns_and_checkpoint_resumption(tmp_path):
    primary, rpg, _ = fixtures(tmp_path)
    for directory in (primary, rpg):
        partition_fixture(directory)
        record_partition_runtime(directory, numpy_runtime())
    manifest = json.loads((primary / "manifest.json").read_text())
    layout = manifest["execution_layout"]
    prior = deepcopy(layout)
    prior["status"] = "interrupted"
    prior["runtime"]["machine"] = "another_cpu_brand"
    prior["runtime"]["logical_cpus"] = 2
    prior["runtime"]["numpy_dispatch_override"] = "AVX512_SKX, AVX512F"
    checkpoint = next((primary / "partitions/lentille/checkpoints").glob("*.json"))
    layout["execution_history"] = [prior]
    layout["start_checkpoint_sha256"] = {str(checkpoint.relative_to(primary)): sha256(checkpoint)}
    (primary / "manifest.json").write_text(json.dumps(manifest))
    (primary / "partition_execution.json").write_text(json.dumps(layout))
    result = merge_runs(primary, rpg, tmp_path / "same_profile")
    assert result["spec"]["composition"]["numpy_execution_profile_check"] == "effective_dispatch_and_override"
    assert all("partition_execution" in source for source in result["spec"]["composition"]["sources"].values())
