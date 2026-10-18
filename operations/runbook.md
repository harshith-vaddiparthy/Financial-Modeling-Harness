# Operation and recovery

Run `python3 -m harness doctor` and the tests from the checkout. Read the input contract before preparing real company inputs. The CLI reads an explicitly supplied local JSON path; MCP accepts model objects and cannot read arbitrary paths. MCP run directories are confined to the configured workspace and run identifiers are validated. These tool boundaries do not sandbox an agent's separate shell/file tools.

The default workspace is this checkout's `workspace/`. Override with `python3 -m harness --workspace /private/path ...`, or set `FINANCIAL_HARNESS_WORKSPACE` in the MCP server's environment. Use separate workspaces and Hermes profiles for separate clients. The harness is a local single-user component; stdio delegates caller identity and user authorization to the host agent. No HTTP listener is opened.

Input messages are capped at 1 MiB, the forecast at 60 months, hiring/funding schedules at 100 entries each, and sensitivity at 20 values. Missing/invalid numeric inputs and unknown fields fail. A successful calculation creates a new run directory with restrictive permissions. Run directories are not overwritten. The completed manifest is written last. Concurrent runs receive unique IDs; there is no shared mutable model state.

After timeout or interruption, inspect whether the exact run has a completed manifest. Incomplete directories are incomplete evidence; rerun the saved source to create a new run. A hash mismatch is a stop condition for that artifact. Preserve the original evidence and create a fresh verified run from trusted inputs. An engine-source change requires a new run before verification can pass.

For a Hermes connection, use the skill's [Hermes reference](../skills/financial-modeling-harness/references/hermes.md). Inspect registration and tool discovery in a fresh process before starting a model-backed test. Existing sessions may require a new turn/session to reload skills and tools. A working core does not prove a working provider or gateway.

Rollback is scoped: remove only the `financial-modeling-harness` MCP server with `hermes mcp remove financial-modeling-harness`. The skill installer prints the target path; preserve its bundle before removing that named skill if needed. Keep company workspaces and existing provider settings. No gateway restart is required by this harness.
