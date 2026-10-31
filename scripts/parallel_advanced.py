"""Resume an immutable advanced benchmark as independent crop partitions.

The logical full-run manifest/signature is preserved. Each child runs the
unchanged benchmark with ONLY its ``cultures`` option restricted to one crop.
Checkpoint rows, audits and residual diagnostics are never recomputed/repriced
by this wrapper. Every child source/package/spec is checked before execution,
and the completed checkpoints are consolidated under the original logical
signature with explicit child-execution provenance.

Per-crop partitioning is valid because dependence history is filtered by crop
and model, random seeds do not depend on iteration order, and the wheat fits
depend on the same past wheat data. Years remain sequential within each crop.
"""
from __future__ import annotations

import argparse
from collections import deque
from copy import deepcopy
import hashlib
import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import zipfile


CORE = ("rows", "audits", "diagnostics")
THREAD_ENV = {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def spec_signature(spec):
    return hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()


def atomic_json(path, record):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(record, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    temp.replace(path)


def verify_manifest(root, output, source_archive=None, check_packages=True):
    root, output = Path(root).resolve(), Path(output).resolve()
    manifest = json.loads((output / "manifest.json").read_text())
    spec = manifest["spec"]
    if spec_signature(spec) != manifest["signature"]:
        raise ValueError("Original logical manifest signature does not match its spec")
    if not spec.get("files"):
        raise ValueError("Original manifest has no source/data fingerprints")
    for name, expected in spec["files"].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root) or not path.is_file() or sha256(path) != expected:
            raise ValueError(f"Frozen source/data changed or missing: {name}")
    if check_packages:
        for package, expected in spec.get("packages", {}).items():
            actual = importlib.metadata.version(package)
            if actual != expected:
                raise ValueError(f"Package changed: {package} {actual} != {expected}")
    if source_archive is not None:
        with zipfile.ZipFile(source_archive) as archive:
            names = archive.namelist()
            for name, expected in spec["files"].items():
                matching = [entry for entry in names if entry == name or entry.endswith("/" + name)]
                if len(matching) != 1:
                    raise ValueError(f"Source archive lacks a unique member for {name}")
                if hashlib.sha256(archive.read(matching[0])).hexdigest() != expected:
                    raise ValueError(f"Source archive mismatch: {name}")
    return manifest


def check_partition_spec(parent, child, culture):
    expected = deepcopy(parent["spec"])
    expected["options"]["cultures"] = [culture]
    if child["spec"] != expected:
        differing = [key for key in set(expected) | set(child["spec"])
                     if expected.get(key) != child["spec"].get(key)]
        raise ValueError(f"Partition changed more than cultures: {culture}: {differing}")
    if child["signature"] != spec_signature(expected):
        raise ValueError("Child signature does not match the restricted spec")


def validate_checkpoint(saved, signature, culture, year, model):
    if saved.get("signature") != signature:
        raise ValueError("Checkpoint signature mismatch")
    for kind in CORE:
        if not isinstance(saved.get(kind), list) or not saved[kind]:
            raise ValueError(f"Checkpoint lacks {kind}")
        for row in saved[kind]:
            if (row.get("culture"), row.get("year"), row.get("model")) != (culture, year, model):
                raise ValueError(f"Checkpoint {kind} belongs to a different crop/year/model")
    return saved


def checkpoint_payload(saved):
    return {key: saved[key] for key in CORE}


def reuse_checkpoint(source, destination, old_signature, new_signature, culture, year, model):
    source, destination = Path(source), Path(destination)
    saved = validate_checkpoint(json.loads(source.read_text()), old_signature, culture, year, model)
    if destination.exists():
        existing = validate_checkpoint(json.loads(destination.read_text()), new_signature, culture, year, model)
        if checkpoint_payload(saved) != checkpoint_payload(existing):
            raise ValueError("Existing child checkpoint disagrees with original completed result")
        return False
    copied = {"signature": new_signature, **checkpoint_payload(saved), "reused_from": {
        "logical_signature": old_signature, "checkpoint": source.name,
        "checkpoint_sha256": sha256(source)}}
    atomic_json(destination, copied)
    return True


def prepare_partitions(root, output, manifest, benchmark):
    """Ask the frozen module to create and verify each child specification."""
    root, output = Path(root).resolve(), Path(output).resolve()
    options = manifest["spec"]["options"]
    if options.get("threads") != 1:
        raise ValueError("Parallel wrapper requires the original threads=1 setting")
    raw, weather, extra = benchmark.load_data(root / "data")
    registry = benchmark.candidate_registry()
    models = list(manifest["spec"]["candidates"])
    children = []
    for culture in options["cultures"]:
        path = output / "partitions" / culture
        path.mkdir(parents=True, exist_ok=True)
        child_options = deepcopy(options)
        child_options["cultures"] = [culture]
        args = argparse.Namespace(**child_options, output=path, data_dir=root / "data")
        candidates, unavailable = benchmark.available_candidates(registry, raw, weather, [culture], options.get("models"))
        benchmark.create_manifest(args, candidates, unavailable, extra)
        child = json.loads((path / "manifest.json").read_text())
        check_partition_spec(manifest, child, culture)
        reused = 0
        for year in options["years"]:
            for model in models:
                name = f"{culture}-{year}-{model}.json"
                source = output / "checkpoints" / name
                destination = path / "checkpoints" / name
                if source.exists():
                    reused += reuse_checkpoint(source, destination, manifest["signature"], child["signature"],
                                               culture, year, model)
                elif destination.exists():
                    validate_checkpoint(json.loads(destination.read_text()), child["signature"], culture, year, model)
        expected = {f"{culture}-{year}-{model}.json" for year in options["years"] for model in models}
        present = {p.name for p in (path / "checkpoints").glob("*.json")}
        if present - expected:
            raise ValueError(f"Unexpected child checkpoints: {sorted(present - expected)}")
        # Scheduling only: large crops start first to avoid a large final task
        # running alone. This estimate never enters fitting or summarization.
        observations = int((raw.culture == culture).sum()) if raw is not None else 1
        total = len(options["years"]) * len(models)
        children.append({"culture": culture, "directory": str(path), "signature": child["signature"],
                         "spec_difference": {"options.cultures": [culture]}, "reused_checkpoints": reused,
                         "total": total, "initial_completed": len(present),
                         "remaining_work_estimate": (total - len(present)) * observations})
    return children


def verify_process(pid, root, output, proc_root=Path("/proc")):
    """Only the explicitly requested frozen benchmark/output process may stop."""
    directory = Path(proc_root) / str(pid)
    if not directory.exists():
        return False
    argv = (directory / "cmdline").read_bytes().split(b"\0")
    argv = [arg.decode() for arg in argv if arg]
    cwd = (directory / "cwd").resolve()
    scripts = [Path(a) for a in argv if Path(a).name == "benchmark_advanced.py"]
    expected_script = (Path(root) / "pipeline/benchmark_advanced.py").resolve()
    if len(scripts) != 1 or (cwd / scripts[0]).resolve() != expected_script:
        raise ValueError("Refusing to stop a process other than the specified frozen benchmark")
    output_args = [a.split("=", 1)[1] for a in argv if a.startswith("--output=")]
    output_args += [argv[i + 1] for i, arg in enumerate(argv[:-1]) if arg == "--output"]
    if len(output_args) != 1 or (cwd / output_args[0]).resolve() != Path(output).resolve():
        raise ValueError("Refusing to stop benchmark process with a different output")
    return True


def stop_original(pid, root, output, timeout=10):
    if pid is None or not verify_process(pid, root, output):
        return {"requested_pid": pid, "stopped": False, "reason": "not requested or process already absent"}
    os.kill(pid, signal.SIGTERM)
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        path = Path("/proc") / str(pid) / "stat"
        if not path.exists() or path.read_text().split(") ", 1)[1].startswith("Z "):
            return {"requested_pid": pid, "stopped": True, "signal": "SIGTERM"}
        time.sleep(.1)
    raise RuntimeError("Original benchmark did not stop within 10 seconds; no child execution launched")


def child_command(root, child, options):
    command = [sys.executable, "-u", str(Path(root) / "pipeline/benchmark_advanced.py"),
               "--output", child["directory"], "--data-dir", str(Path(root) / "data"),
               "--cultures", child["culture"], "--years", *map(str, options["years"]),
               "--samples", str(options["samples"]), "--seed", str(options["seed"]),
               "--threads", str(options["threads"])]
    if options.get("models") is not None:
        command.extend(["--models", *options["models"]])
    return command


def consolidate(output, manifest, children, benchmark):
    """Restore original iteration order and publish a complete logical run."""
    import pandas as pd
    output = Path(output)
    by_crop = {child["culture"]: child for child in children}
    rows, audits, diagnostics, checkpoints = [], [], [], []
    options, models = manifest["spec"]["options"], list(manifest["spec"]["candidates"])
    for year in sorted(options["years"]):
        for culture in options["cultures"]:
            child = by_crop[culture]
            for model in models:
                name = f"{culture}-{year}-{model}.json"
                source = Path(child["directory"]) / "checkpoints" / name
                saved = validate_checkpoint(json.loads(source.read_text()), child["signature"], culture, year, model)
                destination = output / "checkpoints" / name
                if destination.exists():
                    original = validate_checkpoint(json.loads(destination.read_text()), manifest["signature"], culture, year, model)
                    if checkpoint_payload(original) != checkpoint_payload(saved):
                        raise ValueError(f"Original checkpoint differs from child result: {name}")
                else:
                    atomic_json(destination, {"signature": manifest["signature"], **checkpoint_payload(saved),
                        "executed_child_signature": child["signature"],
                        "executed_child_checkpoint_sha256": sha256(source),
                        "execution_layout": "independent_crop_partition"})
                rows.extend(saved["rows"])
                audits.extend(saved["audits"])
                diagnostics.extend(saved["diagnostics"])
                checkpoints.append({"checkpoint": name, "parent_sha256": sha256(destination),
                                    "child_sha256": sha256(source), "child_signature": child["signature"]})
    result = pd.DataFrame(rows)
    for _, group in result.groupby("culture"):
        benchmark.assert_common_cohort(group, models)
    result.to_csv(output / "predictions.csv", index=False)
    summary = benchmark.summarize(result)
    atomic_json(output / "summary.json", summary)
    pd.DataFrame(summary).to_csv(output / "summary.csv", index=False)
    atomic_json(output / "audit.json", audits)
    pd.DataFrame(diagnostics).to_csv(output / "residual_diagnostics.csv", index=False)
    cohorts = {}
    for child in children:
        data = json.loads((Path(child["directory"]) / "cohorts.json").read_text())
        if set(data) != {child["culture"]}:
            raise ValueError("Child cohort export does not describe exactly its crop")
        cohorts.update(data)
    atomic_json(output / "cohorts.json", cohorts)
    atomic_json(output / "partition_checkpoint_provenance.json", checkpoints)
    return {"rows": len(result), "checkpoints": len(checkpoints), "outputs_sha256": {
        name: sha256(output / name) for name in ("predictions.csv", "summary.json", "summary.csv",
        "audit.json", "residual_diagnostics.csv", "cohorts.json", "partition_checkpoint_provenance.json")}}


def run(args):
    root, output = args.root.resolve(), args.output.resolve()
    if args.workers not in (1, 2):
        raise ValueError("Use one or two crop workers")
    source_archive = args.source_archive
    if source_archive is None and (output / "executed-inputs.zip").exists():
        source_archive = output / "executed-inputs.zip"
    manifest = verify_manifest(root, output, source_archive)
    # Verify sources before importing and before stopping any process.
    sys.path.insert(0, str(root / "pipeline"))
    benchmark = importlib.import_module("benchmark_advanced")
    if Path(benchmark.__file__).resolve() != root / "pipeline/benchmark_advanced.py":
        raise ValueError("Imported benchmark came from a different checkout")
    stop = stop_original(args.stop_pid, root, output)
    # Original process is stopped before snapshotting its completed checkpoints.
    children = prepare_partitions(root, output, manifest, benchmark)
    started = time.monotonic()
    layout = {"kind": "independent_crop_partitions", "status": "running", "workers": args.workers,
        "logical_signature": manifest["signature"], "wrapper_sha256": sha256(__file__),
        "thread_environment": THREAD_ENV,
        "source_archive_sha256": sha256(source_archive) if source_archive else None,
        "stop_original": stop, "children": children,
        "invariance": "Only cultures is restricted; same source/data/package/options, seeds, per-crop sequential years and numerical checkpoint payloads"}
    wrapper_copy = output / "parallel_advanced.executed.py"
    if wrapper_copy.resolve() != Path(__file__).resolve():
        temporary = wrapper_copy.with_suffix(".py.tmp")
        temporary.write_bytes(Path(__file__).read_bytes())
        temporary.replace(wrapper_copy)
    layout["wrapper_source"] = wrapper_copy.name
    atomic_json(output / "partition_execution.json", layout)
    queue, active = deque(sorted(children, key=lambda child: -child["remaining_work_estimate"])), {}
    total = sum(child["total"] for child in children)
    try:
        while queue or active:
            while queue and len(active) < args.workers:
                child = queue.popleft()
                log = open(Path(child["directory"]) / "worker.log", "a", encoding="utf-8")
                command = child_command(root, child, manifest["spec"]["options"])
                process = subprocess.Popen(command, cwd=root, stdout=log, stderr=subprocess.STDOUT,
                                           env={**os.environ, **THREAD_ENV})
                active[child["culture"]] = (process, log, child)
                child["pid"] = process.pid
                child["command"] = command
                atomic_json(output / "partition_execution.json", layout)
            for culture, (process, log, child) in list(active.items()):
                status = process.poll()
                if status is None:
                    continue
                log.close()
                child["exit_code"] = status
                del active[culture]
                if status:
                    raise RuntimeError(f"Crop worker {culture} failed ({status}); completed checkpoints remain resumable")
            completed = sum(len(list((Path(child["directory"]) / "checkpoints").glob("*.json"))) for child in children)
            record = {"status": "running", "completed": completed, "total": total,
                "active": ", ".join(active) or "assembling", "queued_crops": len(queue),
                "elapsed_seconds": round(time.monotonic() - started, 1), "execution_layout": "crop_partitions"}
            atomic_json(output / "progress.json", record)
            print(json.dumps(record), flush=True)
            if active:
                time.sleep(2)
        verify_manifest(root, output, source_archive)
        # Check child manifests have not changed while their processes ran.
        for child in children:
            check_partition_spec(manifest, json.loads((Path(child["directory"]) / "manifest.json").read_text()), child["culture"])
        layout["results"] = consolidate(output, manifest, children, benchmark)
        layout["status"] = "completed"
        layout["elapsed_seconds"] = round(time.monotonic() - started, 1)
        atomic_json(output / "partition_execution.json", layout)
        final_manifest = dict(manifest)
        final_manifest["execution_layout"] = layout
        atomic_json(output / "manifest.json", final_manifest)
        atomic_json(output / "progress.json", {"status": "completed", "completed": total, "total": total,
            "active": "all crops complete", "elapsed_seconds": layout["elapsed_seconds"], "execution_layout": "crop_partitions"})
        print(json.dumps({"status": "completed", **layout["results"]}), flush=True)
    except BaseException:
        for process, log, child in active.values():
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child["termination_pending"] = True
            log.close()
        layout["status"] = "interrupted"
        atomic_json(output / "partition_execution.json", layout)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--stop-pid", type=int)
    parser.add_argument("--source-archive", type=Path)
    run(parser.parse_args())
