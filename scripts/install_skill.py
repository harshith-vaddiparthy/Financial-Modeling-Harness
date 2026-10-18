#!/usr/bin/env python3
"""Add a complete skill bundle; never overwrite conflicting installed content."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path


def fingerprint(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=["hermes", "codex"], required=True)
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1] / "skills/financial-modeling-harness"
    base = Path.home() / (".hermes/skills" if args.target == "hermes" else ".codex/skills")
    target = base / source.name
    if target.exists() or target.is_symlink():
        if target.is_dir() and fingerprint(target) == fingerprint(source):
            print(json.dumps({"status": "unchanged", "path": str(target)}))
            return
        parser.error(f"conflicting skill exists at {target}; preserve and reconcile it through the host's skill policy")
    base.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if fingerprint(target) != fingerprint(source):
        raise RuntimeError("installed skill fingerprint mismatch")
    print(json.dumps({"status": "installed", "path": str(target), "files": len(fingerprint(target))}))


if __name__ == "__main__":
    main()
