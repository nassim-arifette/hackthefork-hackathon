"""Atomic result checkpoints; no fitted models, credentials or environment dumps."""
import hashlib
import importlib.metadata
import json
from pathlib import Path


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


class Checkpoints:
    def __init__(self, args, stage, units):
        self.root = args.output / "checkpoints"
        self.root.mkdir(parents=True, exist_ok=True)
        self.units, self.stage = units, stage
        repo = Path(__file__).resolve().parents[1]
        files = sorted((repo / "pipeline").glob("*.py")) + [repo / "data" / n for n in
            ("panel_rendements.csv", "meteo_dept.csv", "prix_ble.csv", "hypotheses.yaml")]
        if getattr(args, "reference", None):
            files.append(args.reference)
        packages = {}
        for name in ("numpy", "pandas", "scipy", "scikit-learn", "lightgbm", "quantile-forest", "catboost", "tabpfn"):
            try:
                packages[name] = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                pass
        spec = {"stage": stage, "args": {k: str(v) for k, v in vars(args).items()
                if k not in ("output", "reference")}, "packages": packages,
                "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
        self.signature = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()
        manifest = self.root / "manifest.json"
        if manifest.exists() and json.loads(manifest.read_text())["signature"] != self.signature:
            raise ValueError("Checkpoint inputs/code/options changed: choose a new --output directory")
        atomic_json(manifest, {"signature": self.signature, "spec": spec})

    def get(self, key):
        path = self.root / (key + ".json")
        if not path.exists():
            return None
        item = json.loads(path.read_text())
        if item["signature"] != self.signature:
            raise ValueError("Incompatible checkpoint: " + key)
        return item["payload"]

    def progress(self, active="", status="running"):
        done = sum((self.root / (key + ".json")).exists() for key in self.units)
        atomic_json(self.root.parent / "progress.json", {"stage": self.stage,
            "completed": done, "total": len(self.units), "active": active, "status": status})
        print(f"[{self.stage}] {done}/{len(self.units)} — {active}", flush=True)

    def save(self, key, payload):
        atomic_json(self.root / (key + ".json"), {"signature": self.signature, "payload": payload})
        self.progress(key + " sauvegardé")
