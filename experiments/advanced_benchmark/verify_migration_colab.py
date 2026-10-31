"""Replay targeted archived checkpoints on the new Colab runtime, without edits.

The comparison is deliberately scoped to the selected crop/year/model units.
It is not a proof that every hardware combination produces identical results.
Original checkpoints and frozen model sources are read only. Each invocation
creates a fresh verification run so checkpoint resumption cannot fake a replay.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import numbers
import os
from pathlib import Path
import platform
import sys
import time


CORE = ("rows", "audits", "diagnostics")
ROW_KEYS = ("culture", "year", "dep", "model", "contract")


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha256(path):
    return digest_bytes(Path(path).read_bytes())


def write_json(path, record):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(record, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    temporary.replace(path)


def core_bytes(saved):
    return json.dumps({name: saved[name] for name in CORE}, sort_keys=True,
                      separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def differences(before, after, path="", result=None):
    """Report exact mismatches and their scale without rounding them away."""
    if result is None:
        result = {"count": 0, "numeric_count": 0, "max_absolute_numeric_difference": 0.,
                  "max_relative_numeric_difference": 0., "examples": []}
    if isinstance(before, dict) and isinstance(after, dict):
        for key in sorted(set(before) | set(after)):
            if key not in before or key not in after:
                result["count"] += 1
                if len(result["examples"]) < 20:
                    result["examples"].append({"path": f"{path}.{key}", "reason": "missing key"})
            else:
                differences(before[key], after[key], f"{path}.{key}", result)
        return result
    if isinstance(before, list) and isinstance(after, list):
        if len(before) != len(after):
            result["count"] += 1
            if len(result["examples"]) < 20:
                result["examples"].append({"path": path, "reason": "different list length",
                                            "before": len(before), "after": len(after)})
        for index, (left, right) in enumerate(zip(before, after)):
            differences(left, right, f"{path}[{index}]", result)
        return result
    same_type = type(before) is type(after)
    if same_type and before == after:
        return result
    result["count"] += 1
    numeric = (isinstance(before, numbers.Real) and not isinstance(before, bool)
               and isinstance(after, numbers.Real) and not isinstance(after, bool))
    detail = {"path": path, "before": before, "after": after,
              "reason": "numeric value/type differs" if numeric else "value/type differs"}
    if numeric:
        delta = abs(float(before) - float(after))
        relative = delta / max(abs(float(before)), abs(float(after)), 1e-300)
        result["numeric_count"] += 1
        result["max_absolute_numeric_difference"] = max(result["max_absolute_numeric_difference"], delta)
        result["max_relative_numeric_difference"] = max(result["max_relative_numeric_difference"], relative)
        detail.update(absolute_difference=delta, relative_difference=relative)
    if len(result["examples"]) < 20:
        result["examples"].append(detail)
    return result


def row_comparison(before, after):
    left = {tuple(row[key] for key in ROW_KEYS): row for row in before}
    right = {tuple(row[key] for key in ROW_KEYS): row for row in after}
    same_cohort = len(left) == len(before) and len(right) == len(after) and set(left) == set(right)
    common = sorted(set(left) & set(right))
    contracts = {}
    for shape in sorted({key[-1] for key in common}):
        keys = [key for key in common if key[-1] == shape]
        record = {"n_cases": len(keys),
                  "changed_held_verdicts": sum(left[key]["held"] != right[key]["held"] for key in keys)}
        for column in ("coefficient", "paid_actual_eur_ha", "expected_unit_cost", "shortfall_eur_ha"):
            record[column + "_max_abs_difference"] = max(
                (abs(left[key][column] - right[key][column]) for key in keys), default=0.)
        contracts[shape] = record
    return {"same_cohort": same_cohort, "before_rows": len(before), "after_rows": len(after),
            "all_held_verdicts_identical": same_cohort and all(left[key]["held"] == right[key]["held"] for key in common),
            "per_contract": contracts}


def main(args):
    root, primary, output = args.root.resolve(), args.primary_output.resolve(), args.output.resolve()
    if output == primary or output.is_relative_to(primary) or output == root or output.is_relative_to(root):
        raise ValueError("Verification output must be outside frozen sources and primary results")
    output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir = output / f"replay-{stamp}"
    report_path = output / "migration_verification.json"
    child_dir = primary / "partitions" / args.culture
    child_manifest_path = child_dir / "manifest.json"
    child_manifest = json.loads(child_manifest_path.read_text())
    spec = child_manifest["spec"]
    if digest_bytes(json.dumps(spec, sort_keys=True).encode()) != child_manifest["signature"]:
        raise ValueError("Original child manifest has an invalid signature")
    if (spec["options"]["seed"], spec["options"]["samples"], spec["options"]["threads"]) != (42, 20000, 1):
        raise ValueError("Expected archived seed42/samples20000/threads1 configuration")
    changed_sources = []
    for name, expected in spec["files"].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root) or not path.is_file() or sha256(path) != expected:
            changed_sources.append(name)
    if changed_sources:
        raise ValueError(f"Frozen source/data mismatch: {changed_sources}")
    layout_path = primary / "partition_execution.json"
    layout = json.loads(layout_path.read_text()) if layout_path.exists() else {}
    before_start = layout.get("start_checkpoint_sha256", {})
    selected, absent = {}, []
    for model in args.models:
        path = child_dir / "checkpoints" / f"{args.culture}-{args.year}-{model}.json"
        if not path.exists():
            absent.append(model)
            continue
        content = path.read_bytes()
        saved = json.loads(content)
        if saved.get("signature") != child_manifest["signature"]:
            raise ValueError(f"Archived checkpoint does not match child execution: {path.name}")
        for kind in CORE:
            if not saved.get(kind) or any((row["culture"], row["year"], row["model"])
                    != (args.culture, args.year, model) for row in saved[kind]):
                raise ValueError(f"Archived checkpoint identity mismatch: {path.name}/{kind}")
        relative = str(path.relative_to(primary))
        digest = digest_bytes(content)
        selected[model] = {"saved": saved, "path": str(path), "sha256": digest,
            "core_sha256": digest_bytes(core_bytes(saved)),
            "matched_checkpoint_at_latest_partition_start": before_start.get(relative) == digest}
    packages = {name: importlib.metadata.version(name) for name in spec["packages"]}
    package_changes = {name: {"archived": spec["packages"][name], "current": value}
                       for name, value in packages.items() if value != spec["packages"][name]}
    report = {"status": "prepared", "created_utc": stamp, "scope": {
        "culture": args.culture, "year": args.year, "requested_models": args.models,
        "selected_models": list(selected), "missing_original_checkpoints": absent,
        "interpretation": "Targeted checkpoint replay on this runtime. Only checkpoints bound at the latest "
            "partition start predate this execution attempt; this is not a global hardware-invariance claim."},
        "runtime": {"python": platform.python_version(), "machine": platform.machine(),
                    "platform": platform.platform(), "logical_cpus": os.cpu_count()},
        "thread_environment": {name: os.environ.get(name) for name in
                               ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")},
        "original_child_manifest_sha256": sha256(child_manifest_path),
        "original_child_signature": child_manifest["signature"],
        "partition_layout_sha256": sha256(layout_path) if layout_path.exists() else None,
        "partition_runtime": layout.get("runtime"),
        "prior_runtimes": [old.get("runtime") for old in layout.get("execution_history", [])],
        "packages": packages, "package_changes": package_changes,
        "source_files_verified": len(spec["files"]),
        "helper_path": str(args.helper.resolve()), "helper_sha256": sha256(args.helper),
        "verification_script_sha256": sha256(Path(__file__)), "replay_directory": str(run_dir),
        "original_checkpoints": {name: {k: v for k, v in item.items() if k != "saved"}
                                 for name, item in selected.items()}}
    write_json(report_path, report)
    if not selected:
        report["status"] = "not_run_no_original_checkpoints"
        write_json(report_path, report)
        print(json.dumps(report, ensure_ascii=False))
        return 2
    sys.path.insert(0, str(root / "pipeline"))
    import benchmark_advanced as benchmark
    if Path(benchmark.__file__).resolve() != root / "pipeline/benchmark_advanced.py":
        raise ValueError("Benchmark imported from a different checkout")
    module_spec = importlib.util.spec_from_file_location("migration_batched_prediction", args.helper)
    helper = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = helper
    module_spec.loader.exec_module(helper)
    replay_args = argparse.Namespace(output=run_dir, data_dir=root / "data", cultures=[args.culture],
        models=list(selected), years=[args.year], samples=20000, seed=42, threads=1)
    started = time.monotonic()
    report["status"] = "running"
    write_json(report_path, report)
    try:
        with helper.install_batched_predictions(benchmark) as batching:
            benchmark.run(replay_args)
            batching_stats = batching.stats
        comparisons = {}
        for model, original in selected.items():
            replay_path = run_dir / "checkpoints" / f"{args.culture}-{args.year}-{model}.json"
            replay = json.loads(replay_path.read_text())
            before = {name: original["saved"][name] for name in CORE}
            after = {name: replay[name] for name in CORE}
            comparison = {"core_exact": core_bytes(original["saved"]) == core_bytes(replay),
                "original_checkpoint_sha256": original["sha256"], "replay_checkpoint_sha256": sha256(replay_path),
                "original_core_sha256": original["core_sha256"], "replay_core_sha256": digest_bytes(core_bytes(replay)),
                "original_predates_latest_partition_start": original["matched_checkpoint_at_latest_partition_start"],
                "differences": differences(before, after),
                **row_comparison(original["saved"]["rows"], replay["rows"])}
            comparisons[model] = comparison
            # A concurrently running worker must not replace an already saved source checkpoint.
            if sha256(original["path"]) != original["sha256"]:
                raise ValueError(f"Original checkpoint changed during verification: {model}")
        report.update(status="completed", elapsed_seconds=round(time.monotonic() - started, 3),
            batching_stats=batching_stats, comparisons=comparisons,
            all_core_exact=all(row["core_exact"] for row in comparisons.values()),
            all_cohorts_identical=all(row["same_cohort"] for row in comparisons.values()),
            all_verdicts_identical=all(row["all_held_verdicts_identical"] for row in comparisons.values()),
            replay_manifest_sha256=sha256(run_dir / "manifest.json"))
        write_json(report_path, report)
        write_json(run_dir / "migration_verification.json", report)
        print(json.dumps({"status": report["status"], "models": list(comparisons),
            "all_core_exact": report["all_core_exact"], "all_cohorts_identical": report["all_cohorts_identical"],
            "all_verdicts_identical": report["all_verdicts_identical"], "report": str(report_path)}, ensure_ascii=False))
        return 0 if report["all_core_exact"] and not package_changes else 1
    except BaseException as error:
        report.update(status="failed", elapsed_seconds=round(time.monotonic() - started, 3),
                      error_type=type(error).__name__, error=str(error))
        write_json(report_path, report)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("/content/hackthefork-advanced"))
    parser.add_argument("--primary-output", type=Path, default=Path("/content/hackthefork-advanced-results"))
    parser.add_argument("--output", type=Path, default=Path("/content/advanced-migration-verification"))
    parser.add_argument("--helper", type=Path, default=Path("/content/batched_prediction.py"))
    parser.add_argument("--culture", default="pois")
    parser.add_argument("--year", type=int, default=2018)
    parser.add_argument("--models", nargs="+", default=["trend", "qrf_seasonal", "qrf_soil_dense", "cat_sparse"])
    arguments = parser.parse_args()
    for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[variable] = "1"
    sys.exit(main(arguments))
