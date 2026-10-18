#!/usr/bin/env python3
"""Locate the standalone checkout and dispatch its CLI without shell interpolation."""
import os
import subprocess
import sys
from pathlib import Path


def main():
    explicit = os.environ.get("FINANCIAL_HARNESS_ROOT")
    candidates = [Path(explicit).expanduser()] if explicit else [
        *Path(__file__).resolve().parents,
        Path.home() / "Desktop/Financial Modeling Harness",
        Path.home() / "work/financial-modeling-harness",
    ]
    root = next((p for p in candidates if (p / "harness/__main__.py").is_file()), None)
    if root is None:
        sys.stderr.write("Financial harness checkout missing. Clone https://github.com/harshith-vaddiparthy/Financial-Modeling-Harness and set FINANCIAL_HARNESS_ROOT.\n")
        return 2
    args = sys.argv[1:]
    workspace = os.environ.get("FINANCIAL_HARNESS_WORKSPACE")
    command = [os.environ.get("FINANCIAL_HARNESS_PYTHON", sys.executable), "-m", "harness"]
    if workspace:
        command += ["--workspace", workspace]
    # Resolve user input/output paths against the caller's directory before changing cwd.
    if args and args[0] in ("validate", "run", "sensitivity") and len(args) > 1 and not args[1].startswith("-"):
        args[1] = str(Path(args[1]).expanduser().resolve())
    if "--output" in args:
        index = args.index("--output") + 1
        if index < len(args):
            args[index] = str(Path(args[index]).expanduser().resolve())
    return subprocess.run(command + args, cwd=root).returncode


if __name__ == "__main__":
    sys.exit(main())
