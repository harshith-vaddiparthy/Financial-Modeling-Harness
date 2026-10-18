# Third-party sources

This harness incorporates two MIT-licensed skill documents as unchanged reference material. Calculation/runtime code and synthetic fixtures were authored for this repository.

| Source | Pinned commit | Local reference and license |
| --- | --- | --- |
| [wshobson/agents](https://github.com/wshobson/agents), startup-financial-modeling | `0874a27b17a22e2b7c2e2bcd725768e0803cad06` | [Skill](vendor/wshobson/startup-financial-modeling/SKILL.md), [details](vendor/wshobson/startup-financial-modeling/references/details.md), [MIT license](vendor/wshobson/LICENSE) |
| [claude-office-skills/skills](https://github.com/claude-office-skills/skills), financial-modeling | `9c4c7d5cd2813a8936bf2c9fdb174ea883b85a11` | [Skill](vendor/claude-office-skills/financial-modeling/SKILL.md), [MIT license](vendor/claude-office-skills/LICENSE) |

The registry pages supplied for this work are [startup-financial-modeling](https://www.skills.sh/wshobson/agents/startup-financial-modeling) and [financial-modeling](https://www.skills.sh/claude-office-skills/skills/financial-modeling). Complete source files were retrieved from GitHub at the commits above on 2026-10-18; SHA-256 values are recorded in [sources.lock.json](vendor/sources.lock.json).

The runtime adapts the concepts rather than executing upstream prompts or installing their suggested providers and Office MCP tools. The startup reference has an inconsistent Year 1 ARR/MRR example and describes scenarios as probability percentiles without a calibrated distribution. The integrated-modeling reference balances cash as a plug. This harness calculates ARR directly from MRR, names its scenarios without percentile claims and rolls cash forward from the cash-flow statement. Generic benchmark ratios remain illustrative until independently sourced for the company and date.
