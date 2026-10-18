# Evaluation rubric

Required: opening balances reconcile; every numeric real input has provenance; missing inputs fail rather than becoming zeros; each requested scenario recalculates revenue, costs, working capital and cash; statement checks pass; negative cash is visible; every deliverable is tied to fresh run verification.

Review business plausibility separately: evidence for acquisition/churn/growth, capacity versus hiring, expense classification, financing timing, simplified tax and working capital, and relevance of the reported metrics. Reconciliation does not score forecast accuracy. Benchmarks need a dated, relevant external source rather than an upstream generic ratio.

Automated checks live in `tests/`. Behavioral requests in `cases.jsonl` are operator/agent evaluation prompts and are not presented as automatically executed tests. Live integration evidence belongs in the verification record.
