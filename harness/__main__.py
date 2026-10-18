import argparse
import copy
import json
import sys
from pathlib import Path

from . import __version__
from .engine import ModelError, forecast, number, validate
from .store import encode, load_input, save_run, verify_run

ROOT = Path(__file__).resolve().parent.parent


def doctor():
    return {"ready": sys.version_info >= (3, 10), "engine_version": __version__,
            "python": sys.version.split()[0], "model_api_required": False,
            "supported_business_models": ["saas", "corporate", "marketplace", "ecommerce", "services"],
            "tools": ["validate", "run", "verify", "sensitivity", "mcp"],
            "network_access": False}


def sensitivity(model, driver, values, scenario="base"):
    validate(model)
    if driver not in model["drivers"]:
        raise ModelError("sensitivity driver must be an existing financial driver")
    if not isinstance(values, list) or not 1 <= len(values) <= 20:
        raise ModelError("sensitivity requires 1–20 numeric values")
    rows = []
    for value in values:
        number(value, "sensitivity value", -1e12, 1e12)
        candidate = copy.deepcopy(model)
        candidate["drivers"][driver] = value
        candidate["scenarios"][scenario].pop(driver, None)
        # Explicitly tag the varied input as an analyst test, preserving the original file.
        prior_source = candidate["provenance"].get(f"drivers.{driver}", candidate["provenance"].get("*"))
        candidate["provenance"][f"drivers.{driver}"] = {
            "kind": "assumption", "reference": f"Sensitivity test at {value}; baseline: {prior_source['reference']}",
            "as_of": prior_source["as_of"]}
        result = forecast(candidate, scenario)
        rows.append({"value": value, **result["summary"], "checks_passed": result["checks"]["passed"]})
    return {"driver": driver, "scenario": scenario, "results": rows,
            "method": "Independent full model recalculation for each input value"}


def main():
    parser = argparse.ArgumentParser(description="Financial Modeling Harness — deterministic projections with auditable runs")
    parser.add_argument("--workspace", type=Path, default=ROOT / "workspace")
    subs = parser.add_subparsers(dest="command", required=True)
    subs.add_parser("doctor")
    init = subs.add_parser("init", help="Create an explicitly synthetic starter; refuses to overwrite")
    init.add_argument("--model", choices=["saas", "corporate", "marketplace", "ecommerce", "services"], default="saas")
    init.add_argument("--output", type=Path, required=True)
    check = subs.add_parser("validate")
    check.add_argument("input", type=Path)
    run = subs.add_parser("run")
    run.add_argument("input", type=Path)
    run.add_argument("--scenario", choices=["all", "conservative", "base", "optimistic"], default="all")
    verify = subs.add_parser("verify")
    verify.add_argument("run_id")
    sen = subs.add_parser("sensitivity")
    sen.add_argument("input", type=Path)
    sen.add_argument("--driver", required=True)
    sen.add_argument("--values", required=True, help="JSON list of numeric values")
    sen.add_argument("--scenario", choices=["base", "conservative", "optimistic"], default="base")
    subs.add_parser("mcp", help="Run a stdio MCP server; stdout is protocol only")
    args = parser.parse_args()
    try:
        if args.command == "mcp":
            from .mcp import serve
            serve(args.workspace)
            return
        if args.command == "doctor":
            result = doctor()
        elif args.command == "init":
            from .examples import make_example
            source = make_example(args.model)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("xb") as handle:
                handle.write(encode(source))
            result = {"created": str(args.output.resolve()), "synthetic": True}
        elif args.command == "validate":
            result = validate(load_input(args.input))
        elif args.command == "run":
            result = save_run(load_input(args.input), args.workspace, args.scenario)
        elif args.command == "verify":
            result = verify_run(args.workspace, args.run_id)
        else:
            result = sensitivity(load_input(args.input), args.driver, json.loads(args.values), args.scenario)
        print(encode(result).decode(), end="")
    except (ModelError, OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"error": str(exc)}, allow_nan=False), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
