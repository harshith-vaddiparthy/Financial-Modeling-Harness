# Accounting and modeling rules

All monetary inputs use whole units of one three-letter currency. Forecast rates are decimal fractions, and growth/churn/expansion inputs are monthly except salary growth and debt interest, which are annual. Forecast horizons contain 1–60 calendar months. Opening values describe the end of the month before the forecast.

Cash, AR, inventory, PP&E, AP, debt, paid-in capital and retained earnings must reconcile at opening. Retained earnings may be negative; other opening balances are nonnegative. Every numeric input in a real model carries exact per-path provenance (`actual` or `assumption`, a source/rationale and date). Wildcard provenance is permitted only for explicitly synthetic fixtures.

SaaS customers are modeled as expected fractional cohort counts. Opening customers age for one month before month-one revenue; newly acquired customers earn a full month immediately. Each older cohort retains `(1-churn)^age` and its price expands by `(1+expansion)^age`. ARR is month-end MRR × 12. Cohort billing is monthly accrual revenue. Annual prepayment/deferred revenue and customer activation ramps are not modeled. NRR is the annualized churn/expansion factor for a starting cohort, excluding new customers.

CAC includes acquisition spend, fixed S&M and S&M payroll divided by new customers. LTV uses current per-customer gross profit divided by monthly churn, without expansion or discounting. CAC payback uses CAC divided by current per-customer gross profit. Zero churn or a nonpositive denominator produces an unavailable metric, not infinite or zero. Burn multiple divides monthly operating/investing cash burn by monthly net-new ARR and is unavailable when net-new ARR is not positive.

COGS consists of revenue × the COGS ratio plus explicitly categorized COGS payroll. S&M, R&D and G&A consist of fixed costs and payroll, with acquisition spend added to S&M. Services capacity is an explicit revenue driver and does not automatically infer billable staffing from the hiring schedule. Check its billable staff against the supplied role plan during review. No benchmark silently changes the inputs.

AR = monthly revenue × DSO / actual days in that month. Inventory and AP use monthly COGS × DIO or DPO / month days. This is an ending-balance approximation, not a detailed aging or purchasing schedule. Opening working capital is released or built toward those balances through operating cash flow.

Depreciation uses beginning net PP&E × the monthly depreciation rate, capped at available PP&E; current-month capex begins depreciating next month. Debt interest uses average beginning/ending debt × annual interest rate / 12. Intra-month funding timing is approximated. Repayment greater than available debt fails the run.

Tax is `max(0, monthly EBT) × tax_rate`. Tax refunds, loss carryforwards, deferred tax, indirect tax and statutory schedules are not inferred. Retained earnings roll forward by net income less dividends. Equity raises increase paid-in capital. Simple priced-round ownership for holders at the start of the forecast multiplies by pre-money / post-money. This is dilution relative to the original holder group, not a full founder cap table; SAFEs, fees, option pools and preferences are excluded.

CFO = net income + depreciation - change in AR - change in inventory + change in AP. CFI = negative capex. CFF = equity + debt issued - debt repaid - dividends. Cash rolls forward from CFO + CFI + CFF. The engine does not insert cash, debt or fundraising to force solvency. Negative cash is a projected funding gap and remains visible while the accounting identities still reconcile.

Runway at current burn uses cash / positive operating-plus-investing burn and is unavailable when there is no positive burn. It is separate from the first projected cash-breach date. Maximum funding gap is the largest negative projected month-end cash balance, given supplied financing; it is a baseline funding floor without a discretionary buffer.

Calendar-year income/cash-flow values sum the underlying months; stock balances use the final month. Partial years retain their month counts. Ratios are recomputed from their components. Named scenarios are not P10/P50/P90 probability estimates. Sensitivity changes one driver and recalculates the full model.
