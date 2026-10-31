"""Reject changed execution inputs and preserve append-only RPG predictions."""
from copy import deepcopy
import gzip
import json
from zipfile import ZipFile

import pandas as pd
import pytest

from contract_economics import contract_basis, evaluate
from merge_advanced_runs import (ALIAS_CSV, ALIAS_MANIFEST, MANDATORY_FILES, RENAMES,
    digest_bytes, merge_runs, spec_signature, validate_specs)


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
