"""Dependency-free JSON-RPC stdio adapter for Hermes and other MCP hosts."""
import json
import sys

from . import __version__
from .engine import ModelError, keys, validate
from .store import MAX_INPUT_BYTES, encode, run_directory, save_run, verify_run

MODEL = {"type": "object", "description": "Full model object in the documented input contract"}
SCENARIO = {"type": "string", "enum": ["all", "conservative", "base", "optimistic"], "default": "all"}


def tool(name, description, properties, required=(), read_only=True):
    return {"name": name, "description": description,
            "inputSchema": {"type": "object", "properties": properties, "required": list(required), "additionalProperties": False},
            "annotations": {"readOnlyHint": read_only, "destructiveHint": False, "openWorldHint": False}}


TOOLS = [
    tool("finance_doctor", "Check local readiness; no model API or external finance account is needed", {}),
    tool("finance_validate", "Validate inputs, opening balance and provenance. Missing inputs remain errors", {"model": MODEL}, ["model"]),
    tool("finance_run", "Calculate linked monthly statements and named scenarios; save a private immutable run", {"model": MODEL, "scenario": SCENARIO}, ["model"], False),
    tool("finance_verify", "Verify artifact hashes, seven accounting identities and deterministic replay", {"run_id": {"type": "string"}}, ["run_id"]),
    tool("finance_get_summary", "Read saved scenario summaries after verifying the run", {"run_id": {"type": "string"}}, ["run_id"]),
    tool("finance_sensitivity", "Recalculate the full model for up to 20 driver values", {
        "model": MODEL, "driver": {"type": "string"}, "values": {"type": "array", "items": {"type": "number"}, "minItems": 1, "maxItems": 20},
        "scenario": {"type": "string", "enum": ["base", "conservative", "optimistic"], "default": "base"}}, ["model", "driver", "values"]),
]


def call(name, arguments, workspace):
    from .__main__ import doctor, sensitivity
    definition = next((t for t in TOOLS if t["name"] == name), None)
    if definition is None:
        raise ModelError(f"unknown tool: {name}")
    schema = definition["inputSchema"]
    keys(arguments, schema["required"], schema["properties"].keys(), label="arguments")
    if name == "finance_doctor":
        return doctor()
    if name == "finance_validate":
        return validate(arguments["model"])
    if name == "finance_run":
        return save_run(arguments["model"], workspace, arguments.get("scenario", "all"))
    if name == "finance_sensitivity":
        return sensitivity(arguments["model"], arguments["driver"], arguments["values"], arguments.get("scenario", "base"))
    result = verify_run(workspace, arguments["run_id"])
    if name == "finance_get_summary":
        data = json.loads((run_directory(workspace, arguments["run_id"]) / "results.json").read_bytes())
        return {"run_id": arguments["run_id"], "verified": True,
                "summaries": {key: value["summary"] for key, value in data.items()}}
    return result


def serve(workspace):
    def emit(message):
        sys.stdout.write(json.dumps(message, allow_nan=False) + "\n")
        sys.stdout.flush()
    while True:
        line = sys.stdin.buffer.readline(MAX_INPUT_BYTES + 1)
        if not line:
            return
        if len(line) > MAX_INPUT_BYTES:
            emit({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "message exceeds 1 MiB"}})
            return
        request = None
        try:
            request = json.loads(line)
            if not isinstance(request, dict) or request.get("jsonrpc") != "2.0":
                raise ValueError("expected a JSON-RPC 2.0 object")
            method, params = request.get("method"), request.get("params", {})
            if "id" not in request:
                continue
            if method == "initialize":
                requested = params.get("protocolVersion", "2024-11-05")
                versions = {"2024-11-05", "2025-03-26", "2025-06-18", "2025-11-25"}
                result = {"protocolVersion": requested if requested in versions else "2024-11-05",
                          "capabilities": {"tools": {}}, "serverInfo": {"name": "financial-modeling-harness", "version": __version__}}
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = {"tools": TOOLS}
            elif method == "tools/call":
                try:
                    result_value = call(params["name"], params.get("arguments", {}), workspace)
                    result = {"content": [{"type": "text", "text": encode(result_value).decode()}], "isError": False}
                except (ModelError, OSError, ValueError, TypeError, KeyError) as exc:
                    result = {"content": [{"type": "text", "text": json.dumps({"error": str(exc)})}], "isError": True}
            else:
                emit({"jsonrpc": "2.0", "id": request["id"], "error": {"code": -32601, "message": "Method not found"}})
                continue
            emit({"jsonrpc": "2.0", "id": request["id"], "result": result})
        except (ValueError, TypeError, KeyError) as exc:
            emit({"jsonrpc": "2.0", "id": request.get("id") if isinstance(request, dict) else None,
                  "error": {"code": -32700, "message": str(exc)}})
