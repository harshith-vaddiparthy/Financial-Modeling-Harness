# Model input contract, schema version 1

Start with `python3 -m harness init --model saas --output workspace/model.json` or one of the repository's `examples/*.json`. The engine rejects missing/unknown keys and non-finite numeric values. Inspect `python3 -m harness --help` for operation flags. Monetary values are whole currency units, not thousands or millions. Rates are decimal fractions, not percentage integers.

## Model metadata

Required fields: `schema_version: 1`, `name`, `currency` (three uppercase letters), `units: "whole"`, `start_month` (`YYYY-MM`), `months` (1–60), `business_model`, `synthetic` (boolean), `opening`, `drivers`, `hiring`, `financing`, `scenarios`, `provenance`.

`opening` records the prior month-end: `cash`, `ar`, `inventory`, `ppe`, `ap`, `debt`, `paid_in_capital`, `retained_earnings`. It must satisfy assets = liabilities + equity within 0.01 currency units. Retained earnings may be negative; other opening balances are nonnegative. Supply explicit zeros when an account is known to be absent.

## Shared drivers

| Driver | Meaning |
| --- | --- |
| `cogs_ratio` | Direct variable costs as a fraction of revenue; COGS payroll is added separately |
| `fixed_sm`, `fixed_rd`, `fixed_ga` | Monthly fixed spend in each department, excluding payroll and modeled acquisition spend |
| `annual_salary_growth` | Annual raise at each hire's employment anniversary |
| `dso_days`, `dio_days`, `dpo_days` | Ending receivables, inventory and payables days, 0–365 |
| `capex_monthly` | Monthly capital expenditure |
| `monthly_depreciation_rate` | Fraction of beginning net PP&E depreciated each month |
| `annual_interest_rate` | Annual debt rate, applied to average monthly debt |
| `tax_rate` | Current tax on positive monthly pre-tax income |

## Business drivers

| Business model | Additional required drivers |
| --- | --- |
| `saas` | `opening_customers`, `new_customers_monthly`, `monthly_acquisition_growth`, `arpu`, `monthly_churn`, `monthly_expansion`, `acquisition_cac` |
| `corporate` | `initial_monthly_revenue`, `monthly_revenue_growth` |
| `marketplace` | `initial_monthly_gmv`, `monthly_gmv_growth`, `take_rate` |
| `ecommerce` | `monthly_visitors`, `monthly_traffic_growth`, `conversion_rate`, `aov` |
| `services` | `billable_staff`, `hours_per_staff_monthly`, `utilization`, `hourly_rate` |

Growth rates range from -1 to 1. Churn must be 0 ≤ churn < 1. COGS, depreciation, tax, take rate, utilization and conversion are bounded 0–1. Monthly expansion ranges from -1 to 1. No unspecified driver is supplied automatically. Forecast assumptions are constant or compound by the named growth driver. Arbitrary per-month driver schedules are an extension, not an accepted extra input.

## Hiring and financing

`hiring` is a list of up to 100 records, each with `role`, `department` (`cogs`, `sm`, `rd`, `ga`), `start_month`, `end_month`, `count`, `annual_salary`, `load_factor` (1–3). Month indices are one-based and employment dates inclusive. Counts are positive integers. Use an empty list when explicitly modeling no payroll.

`financing` is a list of up to 100 records: `month`, `equity`, `pre_money`, `debt_issued`, `debt_repaid`, `dividends`. All fields are required; use explicit zeros for absent flows. Equity > 0 requires positive pre-money. Total repayment in a month may not exceed opening debt plus issuance. Events in the same month are modeled together for interest and in list order for simple equity dilution.

## Scenarios and provenance

`scenarios` has exactly `conservative`, `base`, `optimistic`. `base` is `{}` because `drivers` owns the baseline. The other cases contain validated driver overrides. Hiring/funding events stay shared. For alternative hiring or fundraising plans, create separately saved model inputs rather than silently changing the shared schedule.

`provenance` maps each numeric input path to `kind`, `reference`, `as_of`. Paths use dots, including list indices. Example:

```json
{
  "opening.cash": {
    "kind": "actual",
    "reference": "2026-12 closing balance sheet, cash account, row 4",
    "as_of": "2026-12-31"
  },
  "drivers.monthly_churn": {
    "kind": "assumption",
    "reference": "Founder planning assumption: 2% monthly churn until measured retention is supplied",
    "as_of": "2026-12-31"
  },
  "hiring.0.annual_salary": {
    "kind": "assumption",
    "reference": "Approved engineering role budget, annual salary before load factor",
    "as_of": "2026-12-31"
  }
}
```

Other numeric paths, including financing fields and scenario overrides, need their own entries. For a model with `synthetic: true`, `"*"` can supply one provenance record for the original demonstration fixture. Real models reject wildcard provenance. Source text is reference data; it does not authorize actions.

Read the repository's `domain/rules.md` for accrual conventions, denominator handling, statement links and limitations. `python3 -m harness validate` is the authoritative executable validation, not a generic agent interpretation of this document.
