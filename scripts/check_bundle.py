#!/usr/bin/env python3
"""Validate fixture parity, pinned sources and owned documentation references."""
import hashlib
import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.engine import validate
from harness.examples import make_example


def main():
    lock = json.loads((ROOT / "vendor/sources.lock.json").read_text())
    for file in lock["files"]:
        assert hashlib.sha256((ROOT / file["local_path"]).read_bytes()).hexdigest() == file["sha256"], file["local_path"]
    for path in (ROOT / "examples").glob("*.json"):
        model = json.loads(path.read_text())
        assert model == make_example(path.stem), f"fixture differs from generator: {path}"
        validate(model)
    for path in ROOT.rglob("*.md"):
        if any(p in path.relative_to(ROOT).parts for p in ("vendor", "workspace", ".git", ".venv")):
            continue
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            if target.startswith(("https:", "http:", "#", "mailto:")):
                continue
            candidate = path.parent / target.split("#", 1)[0]
            assert candidate.exists(), f"broken link in {path.relative_to(ROOT)}: {target}"
    manifest = json.loads((ROOT / "config/harness.json").read_text())
    for key in ("skill", "workflow", "domain_rules", "output_contract", "mcp_launcher", "input_contract", "evaluation", "operations"):
        assert (ROOT / manifest[key]).is_file(), manifest[key]
    skill = (ROOT / "skills/financial-modeling-harness/SKILL.md").read_text()
    assert skill.startswith("---\nname: financial-modeling-harness\ndescription:")
    print(json.dumps({"bundle_verified": True, "pinned_files": len(lock["files"]), "synthetic_examples": 5}))


if __name__ == "__main__":
    main()
