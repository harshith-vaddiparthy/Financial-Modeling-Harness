#!/usr/bin/env python3
"""Create and verify a sample (or explicitly supplied JSON) and open its report."""
import json
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.examples import make_example
from harness.store import load_input, save_run, verify_run

model = load_input(sys.argv[1]) if len(sys.argv) > 1 else make_example()
run = save_run(model, ROOT / "workspace")
verify_run(ROOT / "workspace", run["run_id"])
print(json.dumps(run, indent=2))
webbrowser.open(Path(run["report"]).as_uri())
