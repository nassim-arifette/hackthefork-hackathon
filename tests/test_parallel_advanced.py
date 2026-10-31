"""Crop partitioning must preserve the frozen spec and numeric checkpoint data."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import zipfile

import pandas as pd
import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/parallel_advanced.py"
SPEC = importlib.util.spec_from_file_location("parallel_advanced_tested", SCRIPT)
parallel = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(parallel)


def setup_run(tmp_path):
    root, output = tmp_path / "source", tmp_path / "result"
    (root / "pipeline").mkdir(parents=True)
    (root / "data").mkdir()
    output.mkdir()
    (root / "pipeline/benchmark_advanced.py").write_text("# frozen model\n")
    (root / "data/input.csv").write_text("a,b\n1,2\n")
    spec = {"files": {"pipeline/benchmark_advanced.py": parallel.sha256(root / "pipeline/benchmark_advanced.py"),
                      "data/input.csv": parallel.sha256(root / "data/input.csv")},
        "packages": {}, "options": {"cultures": ["lentille", "pois"], "years": [2016, 2017],
            "models": None, "samples": 20000, "seed": 42, "threads": 1},
        "candidates": {"trend": {"distribution": "three"}, "qrf": {"distribution": "dense"}},
        "unavailable_candidates": {}}
    manifest = {"spec": spec, "signature": parallel.spec_signature(spec)}
    parallel.atomic_json(output / "manifest.json", manifest)
    archive_path = output / "executed-inputs.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        for name in spec["files"]:
            archive.write(root / name, name)
    return root, output, manifest, archive_path


def saved_unit(signature, crop, year, model):
    identity = {"culture": crop, "year": year, "model": model}
    rows = [{**identity, "dep": dep, "contract": contract,
             "value": .1 + .2, "nested_values": [1.1, -4., .0000000000000003]}
            for dep in ("01", "77") for contract in ("fixed", "indexed", "tiers")]
    return {"signature": signature, "rows": rows,
        "audits": [{**identity, "threshold": .1 + .2}],
        "diagnostics": [{**identity, "dep": dep, "residual": .1 + .2} for dep in ("01", "77")]}


def fake_benchmark(manifest):
    def create(args, candidates, unavailable, extra):
        spec = deepcopy(manifest["spec"])
        spec["options"] = {k: v for k, v in vars(args).items() if k not in ("output", "data_dir")}
        signature = parallel.spec_signature(spec)
        parallel.atomic_json(args.output / "manifest.json", {"signature": signature, "spec": spec})
        return signature

    def common(frame, models):
        assert set(frame.model) == set(models)
        keys = [set(map(tuple, group[["year", "dep", "contract"]].to_numpy())) for _, group in frame.groupby("model")]
        assert all(key == keys[0] for key in keys)

    return SimpleNamespace(load_data=lambda path: (None, None, []),
        candidate_registry=lambda: manifest["spec"]["candidates"],
        available_candidates=lambda registry, raw, weather, crops, requested: (registry, {}),
        create_manifest=create, assert_common_cohort=common,
        summarize=lambda frame: [{"n": len(frame), "value_sum": float(frame.value.sum())}])


def test_changed_data_or_archive_is_rejected(tmp_path):
    root, output, manifest, archive = setup_run(tmp_path)
    assert parallel.verify_manifest(root, output, archive)["signature"] == manifest["signature"]
    (root / "data/input.csv").write_text("a,b\n1,3\n")
    with pytest.raises(ValueError, match="changed or missing"):
        parallel.verify_manifest(root, output, archive)
    (root / "data/input.csv").write_text("a,b\n1,2\n")
    with zipfile.ZipFile(archive, "w") as changed:
        changed.write(root / "pipeline/benchmark_advanced.py", "pipeline/benchmark_advanced.py")
        changed.writestr("data/input.csv", "changed")
    with pytest.raises(ValueError, match="archive mismatch"):
        parallel.verify_manifest(root, output, archive)


def test_only_culture_option_may_change(tmp_path):
    root, output, parent, _ = setup_run(tmp_path)
    child = deepcopy(parent)
    child["spec"]["options"]["cultures"] = ["lentille"]
    child["signature"] = parallel.spec_signature(child["spec"])
    parallel.check_partition_spec(parent, child, "lentille")
    child["spec"]["options"]["seed"] = 43
    child["signature"] = parallel.spec_signature(child["spec"])
    with pytest.raises(ValueError, match="more than cultures"):
        parallel.check_partition_spec(parent, child, "lentille")


def test_checkpoint_identity_and_float_payload_are_preserved(tmp_path):
    source, destination = tmp_path / "a.json", tmp_path / "b.json"
    saved = saved_unit("parent", "lentille", 2016, "trend")
    parallel.atomic_json(source, saved)
    assert parallel.reuse_checkpoint(source, destination, "parent", "child", "lentille", 2016, "trend")
    copied = json.loads(destination.read_text())
    assert parallel.checkpoint_payload(copied) == parallel.checkpoint_payload(saved)
    assert copied["reused_from"]["checkpoint_sha256"] == parallel.sha256(source)
    assert not parallel.reuse_checkpoint(source, destination, "parent", "child", "lentille", 2016, "trend")
    with pytest.raises(ValueError, match="different crop"):
        parallel.validate_checkpoint(copied, "child", "pois", 2016, "trend")
    copied["rows"][0]["value"] += 1
    parallel.atomic_json(destination, copied)
    with pytest.raises(ValueError, match="disagrees"):
        parallel.reuse_checkpoint(source, destination, "parent", "child", "lentille", 2016, "trend")


def test_two_crop_partition_resume_and_merge_preserve_original_order_and_values(tmp_path):
    root, output, parent, _ = setup_run(tmp_path)
    original = saved_unit(parent["signature"], "lentille", 2016, "trend")
    original_path = output / "checkpoints/lentille-2016-trend.json"
    parallel.atomic_json(original_path, original)
    original_bytes = original_path.read_bytes()
    benchmark = fake_benchmark(parent)
    children = parallel.prepare_partitions(root, output, parent, benchmark)
    assert sum(child["reused_checkpoints"] for child in children) == 1
    for child in children:
        for year in (2016, 2017):
            for model in ("trend", "qrf"):
                destination = Path(child["directory"]) / "checkpoints" / f"{child['culture']}-{year}-{model}.json"
                if not destination.exists():
                    parallel.atomic_json(destination, saved_unit(child["signature"], child["culture"], year, model))
        parallel.atomic_json(Path(child["directory"]) / "cohorts.json", {child["culture"]: {"modern_n": 4}})
    result = parallel.consolidate(output, parent, children, benchmark)
    assert result["checkpoints"] == 8
    assert result["rows"] == 48
    assert original_path.read_bytes() == original_bytes
    for year in (2016, 2017):
        for crop in ("lentille", "pois"):
            for model in ("trend", "qrf"):
                path = output / "checkpoints" / f"{crop}-{year}-{model}.json"
                saved = json.loads(path.read_text())
                assert parallel.checkpoint_payload(saved) == parallel.checkpoint_payload(saved_unit(parent["signature"], crop, year, model))
                assert saved["signature"] == parent["signature"]
                if path != original_path:
                    assert "executed_child_signature" in saved
    predictions = pd.read_csv(output / "predictions.csv", float_precision="round_trip")
    assert predictions.value.iloc[0] == .1 + .2
    assert list(predictions[["year", "culture", "model"]].drop_duplicates().itertuples(index=False, name=None)) == [
        (year, crop, model) for year in (2016, 2017) for crop in ("lentille", "pois") for model in ("trend", "qrf")]
    assert json.loads((output / "manifest.json").read_text()) == parent


def test_process_stop_matching_rejects_other_script_or_output(tmp_path):
    root, output, _, _ = setup_run(tmp_path)
    proc = tmp_path / "proc" / "123"
    proc.mkdir(parents=True)
    (proc / "cwd").symlink_to(root, target_is_directory=True)
    command = ["python", "-u", str(root / "pipeline/benchmark_advanced.py"), "--output", str(output)]
    (proc / "cmdline").write_bytes(b"\0".join(arg.encode() for arg in command) + b"\0")
    assert parallel.verify_process(123, root, output, proc_root=proc.parent)
    with pytest.raises(ValueError, match="different output"):
        parallel.verify_process(123, root, output / "other", proc_root=proc.parent)
    command[2] = "unrelated.py"
    (proc / "cmdline").write_bytes(b"\0".join(arg.encode() for arg in command) + b"\0")
    with pytest.raises(ValueError, match="other than"):
        parallel.verify_process(123, root, output, proc_root=proc.parent)
    assert not parallel.verify_process(999, root, output, proc_root=proc.parent)


def test_child_command_preserves_all_execution_arguments(tmp_path):
    root, output, parent, _ = setup_run(tmp_path)
    child = {"directory": str(output / "partitions/lentille"), "culture": "lentille"}
    command = parallel.child_command(root, child, parent["spec"]["options"])
    assert command[command.index("--samples") + 1] == "20000"
    assert command[command.index("--threads") + 1] == "1"
    assert command[command.index("--seed") + 1] == "42"
    assert "--models" not in command
    options = {**parent["spec"]["options"], "models": ["trend", "qrf"]}
    command = parallel.child_command(root, child, options)
    assert command[-3:] == ["--models", "trend", "qrf"]
