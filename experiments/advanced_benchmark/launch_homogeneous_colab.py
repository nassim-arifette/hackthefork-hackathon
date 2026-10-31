"""Reexecute all 36 arms from scratch on one controlled Colab CPU dispatcher.

No predictions or checkpoints from previous runs are copied. The two historical
source snapshots are reused unchanged: 34 primary arms and two RPG-weather arms.
Run this file after stopping the mixed-runtime experiment. It accepts no CLI
arguments and can also execute as notebook code; all imports here are stdlib so
NumPy's dispatch override is set before each fresh worker interpreter starts.
"""
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile


DISABLED_CPU_FEATURES = "AVX512F,AVX512CD,AVX512_SKX,AVX512_CLX,AVX512_CNL,AVX512_ICL"
WRAPPER = Path("/content/parallel_advanced_v3.py")
BATCHING = Path("/content/batched_prediction.py")
PRIMARY_ROOT = Path("/content/hackthefork-advanced")
RPG_ROOT = Path("/content/hackthefork-rpg")
PRIMARY_OLD = Path("/content/hackthefork-advanced-results")
PRIMARY_OUTPUT = Path("/content/hackthefork-homogeneous-results")
RPG_OUTPUT = Path("/content/hackthefork-rpg-homogeneous-results")
RPG_OLD_ARCHIVE = Path("/content/advanced-rpg-results.zip")

PREPARE = r'''
import hashlib
import json
from pathlib import Path
import sys
import zipfile

root, output, model_json, expected_count = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], int(sys.argv[4])
sys.path.insert(0, str(root / "pipeline"))
import benchmark_advanced as benchmark
args = benchmark.parser().parse_args(["--output", str(output), "--data-dir", str(root / "data"),
    "--samples", "20000", "--threads", "1", "--seed", "42"])
args.models = json.loads(model_json)
raw, weather, extra = benchmark.load_data(args.data_dir)
candidates, unavailable = benchmark.available_candidates(benchmark.candidate_registry(), raw, weather,
    args.cultures, args.models)
if len(candidates) != expected_count:
    raise ValueError(f"Expected {expected_count} candidates, found {len(candidates)}")
benchmark.create_manifest(args, candidates, unavailable, extra)
manifest = json.loads((output / "manifest.json").read_text())
with zipfile.ZipFile(output / "executed-inputs.zip") as source:
    names = source.namelist()
    for name, expected in manifest["spec"]["files"].items():
        members = [member for member in names if member == name or member.endswith("/" + name)]
        if len(members) != 1 or hashlib.sha256(source.read(members[0])).hexdigest() != expected:
            raise ValueError(f"Frozen archived source does not match prepared manifest: {name}")
print(json.dumps({"signature": manifest["signature"], "models": len(candidates),
                  "checkpoints_reused": 0, "expected_units": len(args.cultures)*len(args.years)*len(candidates)}))
'''


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def extract_frozen_archive(archive_bytes, destination):
    """Extract only source bytes; refuse to replace any differing existing file."""
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        if len(archive.namelist()) != len(set(archive.namelist())):
            raise ValueError("Duplicate source archive paths")
        for member in archive.infolist():
            path = (destination / member.filename).resolve()
            if not path.is_relative_to(destination):
                raise ValueError("Source archive path escapes destination")
            if member.is_dir():
                path.mkdir(parents=True, exist_ok=True)
                continue
            content = archive.read(member)
            if path.exists() and path.read_bytes() != content:
                raise ValueError(f"Existing source differs from archived bytes: {member.filename}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)


def main():
    for output in (PRIMARY_OUTPUT, RPG_OUTPUT):
        if output.exists() and any(output.iterdir()):
            raise RuntimeError(f"Full homogeneous rerun requires a fresh output: {output}")
    for required in (WRAPPER, BATCHING, PRIMARY_OLD / "executed-inputs.zip", RPG_OLD_ARCHIVE):
        if not required.is_file():
            raise FileNotFoundError(required)
    with zipfile.ZipFile(RPG_OLD_ARCHIVE) as old:
        members = [name for name in old.namelist() if Path(name).name == "executed-inputs.zip"]
        if len(members) != 1:
            raise ValueError("RPG results must contain one immutable executed-inputs.zip")
        rpg_source = old.read(members[0])
        manifests = [name for name in old.namelist() if name == "manifest.json"]
        previous_rpg = json.loads(old.read(manifests[0])) if len(manifests) == 1 else None
    extract_frozen_archive(rpg_source, RPG_ROOT)
    environment = {**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1",
                   "MKL_NUM_THREADS": "1", "NPY_DISABLE_CPU_FEATURES": DISABLED_CPU_FEATURES}
    jobs = [("primary", PRIMARY_ROOT, PRIMARY_OUTPUT, None, 34),
            ("rpg", RPG_ROOT, RPG_OUTPUT, ["qrf_agri_sparse", "qrf_agri_dense"], 2)]
    prepared = []
    for label, root, output, models, count in jobs:
        output.mkdir(parents=True, exist_ok=True)
        if label == "primary":
            shutil.copyfile(PRIMARY_OLD / "executed-inputs.zip", output / "executed-inputs.zip")
        else:
            (output / "executed-inputs.zip").write_bytes(rpg_source)
        check = subprocess.run([sys.executable, "-c", PREPARE, str(root), str(output),
                                json.dumps(models), str(count)], cwd=root, env=environment,
                               text=True, capture_output=True)
        (output / "prepare.log").write_text(check.stdout + check.stderr)
        if check.returncode:
            raise RuntimeError(f"Homogeneous source preparation failed for {label}: {check.stderr[-3000:]}")
        prepared.append((label, root, output, models, count))
    reason = ("Entire homogeneous rerun: quantile_forest max_samples_leaf=1 combines random sampling "
              "with NumPy unstable equal-value sorting, whose ordering can differ across CPU SIMD dispatch. "
              "Every one of the 36 arms is executed again on this runtime with the same dispatch override; "
              "no old fitted model, prediction or checkpoint is reused.")
    previous_primary = json.loads((PRIMARY_OLD / "manifest.json").read_text())
    launched = []
    for label, root, output, models, count in prepared:
        command = [sys.executable, "-u", str(WRAPPER), "--root", str(root), "--output", str(output),
                   "--workers", "5", "--batched-helper", str(BATCHING)]
        with (output / "parallel.log").open("a") as log:
            process = subprocess.Popen(command, cwd=root, env=environment, stdout=log,
                stderr=subprocess.STDOUT, start_new_session=True)
        previous = previous_primary if label == "primary" else previous_rpg
        execution = {"environment": "Google Colab L4 runtime, CPU execution, five single-thread crop workers",
            "date_utc": datetime.now(timezone.utc).isoformat(), "reason": reason,
            "partition_pid": process.pid, "partition_command": command,
            "partition_wrapper_sha256": digest(WRAPPER), "batching_helper_sha256": digest(BATCHING),
            "source_inputs_archive_sha256": digest(output / "executed-inputs.zip"),
            "numpy_dispatch_override": DISABLED_CPU_FEATURES,
            "thread_environment": {key: environment[key] for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")},
            "previous_result_location": str(PRIMARY_OLD if label == "primary" else RPG_OLD_ARCHIVE),
            "previous_logical_signature": previous.get("signature") if previous else None,
            "previous_results_reused": False, "checkpoints_reused": 0,
            "candidate_count": count, "expected_units": 5 * 10 * count,
            "reporting_instruction": "Combine only the two new homogeneous outputs; never mix with previous results."}
        source_path = Path(globals().get("__file__", "/content/launch_homogeneous_colab.py"))
        if source_path.is_file():
            shutil.copyfile(source_path, output / "launch_homogeneous.executed.py")
            execution["launcher_sha256"] = digest(source_path)
        (output / "execution.json").write_text(json.dumps(execution, indent=2) + "\n")
        launched.append({"run": label, "pid": process.pid, "models": count, "output": str(output)})
    print(json.dumps({"status": "homogeneous_runs_started", "numpy_dispatch_override": DISABLED_CPU_FEATURES,
                      "previous_checkpoints_reused": 0, "runs": launched}), flush=True)


if __name__ == "__main__":
    main()
