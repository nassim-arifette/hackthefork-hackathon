"""Package only the two completed homogeneous runs into Drive-sized ZIP parts.

Each part is independently extractable into its run directory. The index lists
every member and checksums; no member is split. Import ``archive_runs`` to use
small local fixtures. The default entry point takes no arguments and also runs
as notebook code (it does not rely on __file__ or inspect notebook sys.argv).
"""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile


MIB = 1024 * 1024
BIN_LIMIT = 80 * MIB
PART_LIMIT = 90 * MIB
RUNS = {
    "primary": Path("/content/hackthefork-homogeneous-results"),
    "rpg": Path("/content/hackthefork-rpg-homogeneous-results"),
}
OUTPUT = Path("/content/advanced-bundles")


def hash_stream(stream):
    digest = hashlib.sha256()
    while chunk := stream.read(1024 * 1024):
        digest.update(chunk)
    return digest.hexdigest()


def hash_file(path):
    with Path(path).open("rb") as stream:
        return hash_stream(stream)


def source_files(root):
    root = Path(root).resolve()
    files = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Symlink is not an immutable archive input: {path}")
        if path.is_file():
            files[path.relative_to(root).as_posix()] = path
    return files


def pack_run(label, root, output, bin_limit=BIN_LIMIT, part_limit=PART_LIMIT):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.is_relative_to(root):
        raise ValueError("Archive destination must be outside the input run")
    if json.loads((root / "progress.json").read_text()).get("status") != "completed":
        raise ValueError(f"Run is not completed: {label}")
    files = source_files(root)
    if "executed-inputs.zip" not in files:
        raise ValueError(f"Missing full source archive for {label}")
    output.mkdir(parents=True, exist_ok=True)
    temporary = output / f"{label}-full.tmp.zip"
    records = {}
    # First pass creates an immutable compressed snapshot and source checksums.
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
        for name, path in files.items():
            digest = hashlib.sha256()
            size = 0
            info = zipfile.ZipInfo.from_file(path, arcname=name)
            info.compress_type = zipfile.ZIP_DEFLATED
            with path.open("rb") as src, archive.open(info, "w", force_zip64=True) as dst:
                while chunk := src.read(1024 * 1024):
                    dst.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
            records[name] = {"size": size, "sha256": digest.hexdigest()}
    parts, seen = [], set()
    with zipfile.ZipFile(temporary) as full:
        bins = []
        for member in sorted(full.infolist(), key=lambda item: (-item.compress_size, item.filename)):
            if member.compress_size > bin_limit:
                raise ValueError(f"One member exceeds the unsplittable bin limit: {label}/{member.filename}")
            fitting = next((bucket for bucket in bins if bucket["size"] + member.compress_size <= bin_limit), None)
            if fitting is None:
                fitting = {"size": 0, "members": []}
                bins.append(fitting)
            fitting["members"].append(member.filename)
            fitting["size"] += member.compress_size
        for number, bucket in enumerate(bins, 1):
            path = output / f"{label}-part-{number:02d}-of-{len(bins):02d}.zip"
            staging = path.with_suffix(".zip.tmp")
            with zipfile.ZipFile(staging, "w", zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as part:
                for name in sorted(bucket["members"]):
                    with full.open(name) as src, part.open(name, "w", force_zip64=True) as dst:
                        shutil.copyfileobj(src, dst, length=1024 * 1024)
            if staging.stat().st_size >= part_limit:
                raise ValueError(f"ZIP overhead exceeds the strict part limit: {staging}")
            with zipfile.ZipFile(staging) as part:
                names = part.namelist()
                if len(names) != len(set(names)) or seen.intersection(names):
                    raise ValueError("Duplicate archive member across ZIP parts")
                for name in names:
                    info = part.getinfo(name)
                    with part.open(name) as stream:
                        digest = hash_stream(stream)
                    if info.file_size != records[name]["size"] or digest != records[name]["sha256"]:
                        raise ValueError(f"Member differs from source snapshot: {label}/{name}")
                seen.update(names)
            staging.replace(path)
            parts.append({"name": path.name, "path": str(path), "size": path.stat().st_size,
                          "sha256": hash_file(path), "members": sorted(bucket["members"]),
                          "extract_to": label})
            print(json.dumps({"status": "part_verified", "name": path.name,
                              "size": path.stat().st_size, "members": len(bucket["members"])}), flush=True)
    if seen != set(records):
        raise ValueError(f"Missing or extra members in {label} archive parts")
    # Completed runs must remain immutable throughout both compression passes.
    current = source_files(root)
    if set(current) != set(records):
        raise ValueError(f"Run file list changed while archiving: {label}")
    for name, path in current.items():
        if path.stat().st_size != records[name]["size"] or hash_file(path) != records[name]["sha256"]:
            raise ValueError(f"Run changed while archiving: {label}/{name}")
    run_record = {"source_root": str(root), "member_count": len(records),
                  "source_inputs_archive_sha256": records["executed-inputs.zip"]["sha256"],
                  "members": records, "temporary_full_zip": str(temporary),
                  "temporary_full_zip_sha256": hash_file(temporary)}
    return parts, run_record


def archive_runs(runs, output, bin_limit=BIN_LIMIT, part_limit=PART_LIMIT):
    if not 0 < bin_limit < part_limit:
        raise ValueError("Require positive bin_limit strictly below part_limit")
    for label, root in runs.items():
        if json.loads((Path(root) / "progress.json").read_text()).get("status") != "completed":
            raise ValueError(f"Run is not completed: {label}")
    output = Path(output).resolve()
    parts, sources = [], {}
    for label, root in runs.items():
        current, source = pack_run(label, root, output, bin_limit, part_limit)
        parts.extend(current)
        sources[label] = source
    index = {"kind": "homogeneous_results_zip_parts", "version": 1,
             "bin_limit_bytes": bin_limit, "strict_part_limit_bytes": part_limit,
             "part_count": len(parts), "total_member_count": sum(v["member_count"] for v in sources.values()),
             "parts": parts, "runs": sources,
             "extraction": "Extract each listed ZIP into the directory named by extract_to; members are relative to that run root.",
             "verification": "Every source file occurs exactly once per run; all ZIP members match source SHA-256 and final source recheck."}
    destination = output / "index.json"
    staging = destination.with_suffix(".json.tmp")
    staging.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n")
    staging.replace(destination)
    print(json.dumps({"status": "all_parts_verified", "index": str(destination),
                      "parts": len(parts), "members": index["total_member_count"]}), flush=True)
    return index


if __name__ == "__main__":
    archive_runs(RUNS, OUTPUT)
