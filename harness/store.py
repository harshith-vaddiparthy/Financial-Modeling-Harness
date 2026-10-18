"""Immutable run directories, artifact hashes and independent replay verification."""
import hashlib
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .engine import ModelError, forecast, reconcile

MAX_INPUT_BYTES = 1024 * 1024


def encode(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_input(path):
    path = Path(path)
    with path.open("rb") as handle:
        raw = handle.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        raise ModelError("input exceeds 1 MiB")
    return json.loads(raw)


def engine_hash():
    return digest(Path(__file__).with_name("engine.py").read_bytes())


def run_directory(workspace, run_id):
    if not isinstance(run_id, str) or not re.fullmatch(r"[a-f0-9]{32}", run_id):
        raise ModelError("run_id: expected 32 lowercase hexadecimal characters")
    root = (Path(workspace).resolve() / "runs").resolve()
    path = root / run_id
    if path.is_symlink() or path.resolve().parent != root:
        raise ModelError("run directory must stay inside the workspace")
    return path


def save_run(model, workspace, scenario="all"):
    from .reports import write_reports
    if len(encode(model)) > MAX_INPUT_BYTES:
        raise ModelError("input exceeds 1 MiB")
    names = ["conservative", "base", "optimistic"] if scenario == "all" else [scenario]
    results = {name: forecast(model, name) for name in names}
    run_id = uuid.uuid4().hex
    root = Path(workspace).resolve() / "runs"
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(root, 0o700)
    directory = run_directory(workspace, run_id)
    directory.mkdir(mode=0o700)
    (directory / "input.json").write_bytes(encode(model))
    (directory / "results.json").write_bytes(encode(results))
    write_reports(directory, model, results)
    artifacts = {p.name: digest(p.read_bytes()) for p in sorted(directory.iterdir()) if p.is_file()}
    manifest = {"run_id": run_id, "state": "completed", "created_at": datetime.now(timezone.utc).isoformat(),
                "engine_sha256": engine_hash(), "input_sha256": artifacts["input.json"],
                "scenarios": names, "artifacts": artifacts,
                "all_checks_passed": all(r["checks"]["passed"] for r in results.values())}
    (directory / "manifest.json").write_bytes(encode(manifest))
    for file in directory.iterdir():
        os.chmod(file, 0o600)
    return {"run_id": run_id, "state": "completed", "directory": str(directory),
            "report": str(directory / "report.html"), "all_checks_passed": True,
            "summaries": {key: result["summary"] for key, result in results.items()}}


def verify_run(workspace, run_id):
    directory = run_directory(workspace, run_id)
    manifest = load_input(directory / "manifest.json")
    if manifest.get("run_id") != run_id or manifest.get("state") != "completed":
        raise ModelError("run manifest identity or state mismatch")
    if manifest.get("engine_sha256") != engine_hash():
        raise ModelError("engine changed since this run; rerun the input with the current engine")
    for name, expected in manifest["artifacts"].items():
        if Path(name).name != name or (directory / name).is_symlink():
            raise ModelError("invalid artifact path")
        if digest((directory / name).read_bytes()) != expected:
            raise ModelError(f"artifact hash mismatch: {name}")
    if manifest.get("input_sha256") != manifest["artifacts"].get("input.json"):
        raise ModelError("input hash binding mismatch")
    model = load_input(directory / "input.json")
    # Results can contain up to 60 monthly cohorts across three scenarios.
    results = json.loads((directory / "results.json").read_bytes())
    if set(results) != set(manifest["scenarios"]):
        raise ModelError("scenario manifest mismatch")
    for scenario, result in results.items():
        checks = reconcile(model, result["monthly"])
        if not checks["passed"] or encode(forecast(model, scenario)) != encode(result):
            raise ModelError(f"independent replay mismatch: {scenario}")
    return {"run_id": run_id, "verified": True, "artifact_count": len(manifest["artifacts"]),
            "scenarios": manifest["scenarios"], "method": "SHA-256 artifacts, statement identities, deterministic replay",
            "trust_boundary": "Local integrity evidence, not a signature or authenticated approval"}
