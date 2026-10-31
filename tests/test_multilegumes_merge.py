import copy
import gzip
import hashlib
import json

import pandas as pd
import pytest

from contract_economics import contract_basis, evaluate
from merge_multilegumes_runs import (MANDATORY_FILES, merge_runs, sha256, spec_signature,
    validate_audits, validate_specs)


def fixtures(tmp_path):
    current = tmp_path / "checkout"
    previous, replacement = current / "previous", current / "replacement"
    current.mkdir()
    hashes = {}
    for name in MANDATORY_FILES | {"data/meteo_saisonnier_cultures.csv", "pipeline/crop_weather.py"}:
        path = current / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("current " + name)
        hashes[name] = sha256(path)
    h = {crop: {"charges_ble": 700, "charges_culture": cost, "charges_lentille": cost,
        "aide": 105, "rotation": 150, "bonus": 255, "qualite": .1, "tau": .8,
        "prix_ble": None, "forfait": 5} for crop, cost in (("lentille", 500), ("haricot", 1000))}

    def create(directory, cultures, old=False):
        directory.mkdir()
        spec = {"options": {"cultures": cultures, "models": ["trend"], "years": [2019],
            "samples": 20000, "seed": 42, "threads": 1, "seasonal_file": "meteo_saisonnier_cultures.csv",
            "seasonal_columns": None}, "packages": {"numpy": "2.3.5"}, "files": copy.deepcopy(hashes),
            "seasonal_columns": {crop: [crop + "_weather"] for crop in cultures},
            "distribution": "same", "wheat_model": "same", "economic_basis": "same", "target": .8,
            "evaluation_years": [2019], "warmup_years": []}
        if old:
            spec["files"]["data/cultures.yaml"] = hashlib.sha256(b"previous costs").hexdigest()
        manifest = {"signature": spec_signature(spec), "spec": spec}
        rows, audits, cohorts = [], [], {}
        for crop in cultures:
            hyp = copy.deepcopy(h[crop])
            if old and crop == "haricot":
                hyp.update(charges_culture=700, charges_lentille=700)
            need = 200 * 5 - 700 + hyp["charges_culture"] - 105 - 150
            for shape in ("fixed", "indexed", "tiers"):
                basis = float(contract_basis(shape, 1.8, 200, 1.8))
                coefficient = 1000. if shape != "indexed" else 5.
                result = evaluate(coefficient, basis, need, 1.8)
                residual = need - float(result["paid_eur_ha"])
                rows.append({"culture": crop, "year": 2019, "dep": "01", "model": "trend", "contract": shape,
                    "actual_wheat_price": 200., "actual_wheat_yield": 5., "actual_need_eur_ha": need,
                    "actual_crop_yield_raw": 2., "accepted_yield_actual": 1.8, "refused_fraction": .1,
                    "simulation_history_max": 2018, "old_cohort": True, "coefficient": coefficient,
                    "required_coefficient": need / basis, "actual_basis": basis,
                    "simulation_basis_mean": basis, "simulation_accepted_mean": 1.8,
                    "held": bool(result["held"]), "paid_actual_eur_ha": float(result["paid_eur_ha"]),
                    "shortfall_eur_ha": float(result["shortfall_eur_ha"]),
                    "expected_unit_cost": coefficient * basis / 1.8,
                    "contract_loss_eur_ha": max(.8 * residual, -.2 * residual)})
            audits.append({"culture": crop, "year": 2019, "model": "trend", "hypotheses": hyp,
                "training_years": [2017, 2018], "training_max": 2018, "test_departments": ["01"], "n_test": 1})
            cohorts[crop] = {"old_n": 1, "modern_n": 1, "common_n": 1, "old_only": [], "modern_only": []}
        for name, value in (("manifest.json", manifest), ("audit.json", audits), ("cohorts.json", cohorts)):
            (directory / name).write_text(json.dumps(value))
        pd.DataFrame(rows).to_csv(directory / "predictions.csv", index=False)
        return manifest

    old_manifest = create(previous, ["lentille", "haricot"], True)
    new_manifest = create(replacement, ["haricot"])
    return current, previous, replacement, h, old_manifest, new_manifest


def resign(manifest):
    manifest["signature"] = spec_signature(manifest["spec"])
    return manifest


def test_exact_reuse_and_full_replacement_provenance(tmp_path):
    root, old, new, h, _, _ = fixtures(tmp_path)
    destination = root / "composite"
    manifest = merge_runs(old, new, destination, ["haricot"], root, lambda crop: h[crop])
    result = pd.read_csv(destination / "predictions.csv", dtype={"dep": str}, float_precision="round_trip")
    for crop, source in (("lentille", old), ("haricot", new)):
        expected = pd.read_csv(source / "predictions.csv", dtype={"dep": str}, float_precision="round_trip")
        expected = expected[expected.culture == crop].sort_values("contract").reset_index(drop=True)
        actual = result[result.culture == crop].sort_values("contract").reset_index(drop=True)
        pd.testing.assert_frame_equal(actual, expected)
    assert manifest["spec"]["composition"]["crop_source"] == {"lentille": "previous", "haricot": "replacement"}
    assert manifest["spec"]["composition"]["sources"]["previous"]["artifact_sha256"]["predictions.csv"] == sha256(old / "predictions.csv")
    assert manifest["output_sha256"]["predictions.csv"] == sha256(destination / "predictions.csv")
    assert manifest["signature"] == spec_signature(manifest["spec"])
    assert len(json.loads((destination / "audit.json").read_text())) == 2


@pytest.mark.parametrize("file", ["pipeline/multicrop_models.py", "data/meteo_dept_cultures.csv",
    "data/panel_rendements.csv", "data/prix_ble.csv", "data/hypotheses.yaml"])
def test_changed_code_or_common_data_cannot_be_mixed(tmp_path, file):
    _, _, _, _, old, new = fixtures(tmp_path)
    new["spec"]["files"][file] = "changed"
    with pytest.raises(ValueError, match="common statistical inputs"):
        validate_specs(old, resign(new), ["haricot"])


def test_versions_seed_and_features_must_agree(tmp_path):
    _, _, _, _, old, new = fixtures(tmp_path)
    for field, changed, message in (("packages", {"numpy": "other"}, "Package versions"),
            ("options", {**new["spec"]["options"], "seed": 99}, "seed options"),
            ("seasonal_columns", {"haricot": ["different"]}, "Seasonal feature")):
        mutated = copy.deepcopy(new)
        mutated["spec"][field] = changed
        with pytest.raises(ValueError, match=message):
            validate_specs(old, resign(mutated), ["haricot"])


def test_unchanged_crop_economics_must_equal_current_configuration(tmp_path):
    root, old, new, h, _, _ = fixtures(tmp_path)
    h["lentille"]["charges_culture"] += 1
    with pytest.raises(ValueError, match="Economic hypotheses changed"):
        merge_runs(old, new, root / "composite", ["haricot"], root, lambda crop: h[crop])


def test_replacement_cannot_relabel_stale_observed_margins(tmp_path):
    root, old, new, h, _, _ = fixtures(tmp_path)
    rows = pd.read_csv(new / "predictions.csv", dtype={"dep": str})
    rows["actual_need_eur_ha"] -= 300
    rows.to_csv(new / "predictions.csv", index=False)
    with pytest.raises(ValueError, match="needs are stale"):
        merge_runs(old, new, root / "composite", ["haricot"], root, lambda crop: h[crop])


def test_incomplete_audit_and_future_training_are_rejected(tmp_path):
    _, old, _, h, _, _ = fixtures(tmp_path)
    audits = json.loads((old / "audit.json").read_text())
    with pytest.raises(ValueError, match="Incomplete"):
        validate_audits([], ["lentille"], [2019], ["trend"], h)
    audits[0]["training_max"] = 2019
    with pytest.raises(ValueError, match="chronology"):
        validate_audits(audits, ["lentille"], [2019], ["trend"], h)


def test_source_manifests_and_checkout_are_verified(tmp_path):
    root, old, new, h, old_manifest, new_manifest = fixtures(tmp_path)
    new_manifest["spec"]["options"]["seed"] = 99
    with pytest.raises(ValueError, match="manifest signature"):
        validate_specs(old_manifest, new_manifest, ["haricot"])
    (root / "pipeline/model.py").write_text("edited after run")
    with pytest.raises(ValueError, match="Current source differs"):
        merge_runs(old, new, root / "composite", ["haricot"], root, lambda crop: h[crop])


def test_gzip_sources_preserve_original_csv_provenance(tmp_path):
    root, old, new, h, _, _ = fixtures(tmp_path)
    original = merge_runs(old, new, root / "plain_composite", ["haricot"], root, lambda crop: h[crop])
    for source in (old, new):
        data = (source / "predictions.csv").read_bytes()
        (source / "predictions.csv.gz").write_bytes(gzip.compress(data))
        (source / "predictions.csv").unlink()
    compressed = merge_runs(old, new, root / "compressed_composite", ["haricot"], root, lambda crop: h[crop])
    assert compressed["signature"] == original["signature"]
    assert compressed["output_sha256"] == original["output_sha256"]
