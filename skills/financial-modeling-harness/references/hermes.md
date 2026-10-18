# Hermes integration

Hermes is the reasoning/runtime layer. The financial harness is an additive native skill and stdio tool server. Keep the existing Hermes profile, provider, credentials and gateway intact.

## Install and discover the skill

The reusable bundle is `skills/financial-modeling-harness/`. On a generic Hermes host:

```bash
python3 scripts/install_skill.py --target hermes
```

This copies the complete bundle into `~/.hermes/skills/financial-modeling-harness`, refuses conflicting existing content, and prints the installed path. For Codex, use `--target codex`. Follow the host's personal Skill Sync policy when it exists; this local helper does not synchronize machines.

Harshith's Jarvis Brain already configures `skills.external_dirs` to include `/home/harshith/.codex/skills`. Install/synchronize the accepted bundle there and verify it through Hermes discovery instead of making a duplicate native copy. Skill parity does not establish that a checkout or tool runtime is installed on every host. The helper locates `~/work/financial-modeling-harness` or a desktop checkout, or uses `FINANCIAL_HARNESS_ROOT`.

## Register the MCP server

From the financial harness checkout, get the absolute path to `scripts/mcp-server.sh`. It resolves its own root, changes into the checkout and runs the dependency-free Python stdio adapter:

```bash
hermes mcp add financial-modeling-harness \
  --command /absolute/path/Financial-Modeling-Harness/scripts/mcp-server.sh
hermes mcp test financial-modeling-harness
```

Optional registration environment: `FINANCIAL_HARNESS_WORKSPACE=/private/client/workspace` and `FINANCIAL_HARNESS_PYTHON=/absolute/path/python3`. `--env KEY=VALUE` is supported by the inspected Hermes CLI; verify your version's `mcp add --help` before using it. No model API credential is passed to the server.

On the inspected Jarvis installation, the old `~/.local/bin/hermes` symlink has a missing target. The installed runtime works through:

```bash
cd /home/harshith/.hermes/hermes-agent
.venv/bin/python -m hermes_cli.main mcp test financial-modeling-harness
```

Use that verified module route for registration/chat on this host. A broken CLI symlink does not require changing the working gateway or inference providers.

The server tools are `finance_doctor`, `finance_validate`, `finance_run`, `finance_verify`, `finance_get_summary`, and `finance_sensitivity`. MCP accepts a complete model object, not a user-supplied file path. `finance_run` returns the run ID, report path and summaries. Read the resulting private artifacts through the caller's already authorized file tools when full statements are needed. The server does not expose shell commands, arbitrary file reads, network fetches or bank operations.

## Verify a real Hermes turn

Start a fresh session with the skill preloaded:

```bash
hermes chat --skills financial-modeling-harness --in /absolute/path/Financial-Modeling-Harness
```

Request: “Use the synthetic SaaS example, validate it, run all three cases with the finance tools, verify the returned run and report the scenario cash differences. Keep the example synthetic.” Verify actual tool calls and read the saved run. Distinguish successful installation/discovery, successful MCP test, and successful model-backed execution.

For isolated smoke tests, limit the agent's toolsets to the named finance MCP server plus an already authorized input-reading tool, and use a bounded turn/runtime budget. This is a test setting, not a change to the user's global tool access. Existing gateway sessions may load new configuration lazily; verify their own next session before claiming a gateway-specific integration.

## Recover or remove

If the checkout moves, register the new absolute launcher path after inspecting the existing server record. A transport failure remains unconnected until `mcp test` passes. A provider failure leaves the model-backed turn unverified even if the core works. Roll back only the named MCP server with `hermes mcp remove financial-modeling-harness`; preserve company inputs and host credentials.
