# Verification record

Build date: 2026-10-18. Current automated checks are `python3 -m unittest discover -s tests -v` and `python3 scripts/check_bundle.py`. Run-specific evidence stays private in `workspace/`; synthetic demonstrations are not company forecasts.

The standalone engine and stdio lifecycle passed the final 26-test suite, covering all five models and three scenarios, independent financial arithmetic, seven monthly statement identities, cash deficits, dates, payroll, debt, exact real-input provenance, denominator handling, replay and artifact tampering. The suite also passed on Jarvis Linux. The bundle check verifies all five synthetic fixtures, owned document references and five pinned upstream files.

## Published repository and CI

Public standalone repository: [Financial-Modeling-Harness](https://github.com/harshith-vaddiparthy/Financial-Modeling-Harness), with GitHub template mode enabled. Initial published revision: `57e4ab03eded9dbb829210fc8711d517e59b06fe`. [CI run 39149109959](https://github.com/harshith-vaddiparthy/Financial-Modeling-Harness/actions/runs/39149109959) completed successfully across Python 3.10, 3.12 and 3.13.

The parent [Vertical Harness financial example](https://github.com/harshith-vaddiparthy/Vertical-Harness/tree/main/examples/financial-modeling) was published in parent commit `0ace208`, with links in the root README and examples table. The standalone README links back to its parent and both sibling examples.

## Skill and Hermes

Skill Creator validation passed. Skill Sync reported the four-file `financial-modeling-harness` bundle verified across MacBook, Jarvis Brain and Mac mini, with no conflicts, offline replicas or pending writes. Hermes's native `skills_list` discovered the skill through the Brain's existing external skill directory.

The additive `financial-modeling-harness` MCP server was registered in the existing root Hermes profile. `hermes mcp test` connected through stdio and discovered all six tools. No inference provider, model credential, or gateway configuration was changed. The stale CLI symlink was bypassed using the installed Python module, as described in the Hermes reference.

A fresh, bounded Hermes CLI turn using the existing `gpt-6.1-sol` provider successfully invoked `finance_validate`, `finance_run`, `finance_verify` and `finance_sensitivity` against the original synthetic SaaS fixture. Saved run: `980d7f16d10c4321938beedfcd63da4f`. All three 36-month scenarios passed their statement checks; fresh verification checked 13 artifact hashes and deterministic replay. Ending cash was 482,967.40 conservative, 1,020,879.19 base and 1,522,823.35 optimistic USD. Sensitivity independently recalculated churn at 1%, 2% and 3% monthly.

This establishes the native skill and model-backed Hermes CLI integration. Existing long-lived gateway/dashboard sessions were not restarted or individually exercised; start a fresh session to load the server. The tool-server/skill configuration is present in the existing root profile.

## Report inspection

Ego Lite on the identity-verified Kondapur Mac mini rendered the synthetic report, exercised the scenario selector and confirmed three cash curves. Base and conservative values matched the independently saved results. The report made no external resource requests. A 390 × 844 mobile viewport had no horizontal page overflow. Desktop and mobile screenshots were visually inspected; [the public preview](../docs/report-preview.png) contains synthetic data only. The browser task space was closed after QA.

## Limits of this evidence

Fixtures establish calculation and integration behavior, not the accuracy of a company's forecast. JSON/CSV/HTML reports are snapshots; editable Excel export is not implemented. Bank/market-data services, external financial transactions, multicurrency, deferred revenue, tax-loss schedules, SAFEs/options and full cap tables were not implemented or tested. The simplified accounting methods are documented in the domain rules.
