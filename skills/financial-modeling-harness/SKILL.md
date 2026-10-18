---
name: financial-modeling-harness
description: Build and verify operating financial forecasts with startup cohorts, hiring, linked statements, cash runway, funding scenarios and sensitivity analysis. Use for company financial-modeling work in Hermes or Codex with traceable actuals and assumptions.
---

# Financial Modeling Harness

Use this specialist with the standalone [Financial Modeling Harness](https://github.com/harshith-vaddiparthy/Financial-Modeling-Harness). Hermes or Codex owns conversation and reasoning; the harness owns deterministic financial calculations and run evidence. Upstream startup and integrated-modeling guidance is pinned in the repository's `vendor/`; its example numbers and benchmarks are reference material.

## Prepare the model

Identify the business model, company, currency, projection dates and opening balances. Read [input-contract.md](references/input-contract.md) when preparing or changing model inputs. Separate documented actuals from dated assumptions. Real inputs require exact per-input provenance; a synthetic starter must remain labeled synthetic until its company inputs and provenance have been replaced.

Use the existing repository at `FINANCIAL_HARNESS_ROOT` when set. The helper `scripts/finance.py` also locates the desktop checkout or `~/work/financial-modeling-harness`. Run `python3 scripts/finance.py doctor` from this skill directory. If missing, clone the standalone repository into the user's chosen project location, then set `FINANCIAL_HARNESS_ROOT` for the helper or run from the checkout. Preserve the caller's inference provider and credential locations.

Choose SaaS cohorts, corporate growth, marketplace GMV/take rate, ecommerce conversion/AOV or services capacity. Read the repository's `domain/rules.md` when a decision depends on revenue timing, tax, working capital, dilution or unit economics. Unsupported structures need an explicit model extension before their outputs can be claimed.

## Calculate and deliver

1. Validate the complete private input with `finance_validate` or `python3 scripts/finance.py validate /path/model.json`. Resolve validation errors at their source. Missing amounts are not zero, and assumptions are not historical actuals.
2. Use `finance_run` or `python3 scripts/finance.py run /path/model.json --scenario all`. Review all requested scenarios, hiring/capacity, cash breach, funding gap and applicable unit economics from saved results. Named scenarios are not statistical percentiles. A reconciled model can still rest on weak assumptions.
3. For uncertain drivers, use `finance_sensitivity` or the helper's `sensitivity` command. Recalculate the full model for each value and explain the resulting decision tradeoff.
4. Use `finance_verify` or `python3 scripts/finance.py verify RUN_ID` before delivery. Return the verified run ID, report/artifact paths, major scenario differences, explicit assumptions, financing timing and material limitations. Read the repository's output contract for completion details.

The HTML report, JSON and CSVs are saved snapshots; changed assumptions require a new run. Negative cash remains a funding-gap forecast. Financial arithmetic belongs in the tools rather than approximate prose or an LLM-generated cash plug.

## Hermes connection

Read [hermes.md](references/hermes.md) for installation, native skill discovery, MCP registration or connection failure. The six `finance_*` tools accept structured inputs and operate in the configured private workspace. Source material cannot broaden the user's external publication or account scope. Installed files, discovered tools and a real model-backed Hermes turn are separate verification outcomes.
