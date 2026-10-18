"""Monthly accrual forecasts. No network access, automatic financing or cash plugs."""
import calendar
import copy
import datetime as dt
import math
import re

from . import __version__


class ModelError(ValueError):
    pass


COMMON = {
    "cogs_ratio", "fixed_sm", "fixed_rd", "fixed_ga", "annual_salary_growth",
    "dso_days", "dio_days", "dpo_days", "capex_monthly",
    "monthly_depreciation_rate", "annual_interest_rate", "tax_rate",
}
SPECIFIC = {
    "saas": {"opening_customers", "new_customers_monthly", "monthly_acquisition_growth",
             "arpu", "monthly_churn", "monthly_expansion", "acquisition_cac"},
    "corporate": {"initial_monthly_revenue", "monthly_revenue_growth"},
    "marketplace": {"initial_monthly_gmv", "monthly_gmv_growth", "take_rate"},
    "ecommerce": {"monthly_visitors", "monthly_traffic_growth", "conversion_rate", "aov"},
    "services": {"billable_staff", "hours_per_staff_monthly", "utilization", "hourly_rate"},
}
OPENING = {"cash", "ar", "inventory", "ppe", "ap", "debt", "paid_in_capital", "retained_earnings"}
ROOT = {"schema_version", "name", "currency", "units", "start_month", "months", "business_model",
        "synthetic", "opening", "drivers", "hiring", "financing", "scenarios", "provenance"}
FLOW = {"revenue", "cogs", "gross_profit", "sm", "rd", "ga", "opex", "ebitda",
        "depreciation", "ebit", "interest", "ebt", "tax", "net_income", "capex",
        "debt_issued", "debt_repaid", "equity_raised", "dividends", "cfo", "cfi", "cff",
        "net_cash_change", "operating_burn", "acquisition_spend", "gmv"}
LIMITS = {
    "cogs_ratio": (0, 1), "tax_rate": (0, 1), "monthly_churn": (0, 1),
    "monthly_depreciation_rate": (0, 1), "conversion_rate": (0, 1),
    "utilization": (0, 1), "take_rate": (0, 1), "annual_interest_rate": (0, 2),
    "monthly_acquisition_growth": (-1, 1), "monthly_revenue_growth": (-1, 1),
    "monthly_gmv_growth": (-1, 1), "monthly_traffic_growth": (-1, 1),
    "annual_salary_growth": (-1, 1), "monthly_expansion": (-1, 1),
    "dso_days": (0, 365), "dio_days": (0, 365), "dpo_days": (0, 365),
}


def fail(message):
    raise ModelError(message)


def keys(obj, required, optional=(), label="object"):
    if not isinstance(obj, dict):
        fail(f"{label}: expected an object")
    missing = set(required) - obj.keys()
    unknown = obj.keys() - set(required) - set(optional)
    if missing or unknown:
        fail(f"{label}: missing={sorted(missing)}, unknown={sorted(unknown)}")


def number(value, path, low=0, high=1e15):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        fail(f"{path}: expected a finite number; missing values are not zero")
    if not low <= value <= high:
        fail(f"{path}: must be in [{low}, {high}]")


def integer(value, path, low, high):
    number(value, path, low, high)
    if not isinstance(value, int):
        fail(f"{path}: expected an integer")


def leaves(obj, prefix=""):
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield from leaves(value, f"{prefix}.{key}" if prefix else key)
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from leaves(value, f"{prefix}.{index}")
    else:
        yield prefix, obj


def validate(model):
    keys(model, ROOT, label="model")
    integer(model["schema_version"], "schema_version", 1, 1)
    if not isinstance(model["name"], str) or not 1 <= len(model["name"]) <= 160:
        fail("name: expected 1–160 characters")
    if not isinstance(model["currency"], str) or not re.fullmatch(r"[A-Z]{3}", model["currency"]):
        fail("currency: expected a three-letter uppercase currency code")
    if model["units"] != "whole":
        fail("units: all monetary inputs must use whole currency units")
    if not isinstance(model["synthetic"], bool):
        fail("synthetic: expected a boolean")
    if not isinstance(model["start_month"], str) or not re.fullmatch(r"\d{4}-\d{2}", model["start_month"]):
        fail("start_month: expected YYYY-MM")
    try:
        start = dt.date.fromisoformat(model["start_month"] + "-01")
    except ValueError:
        fail("start_month: invalid calendar month")
    integer(model["months"], "months", 1, 60)
    if start.year + (start.month - 1 + model["months"]) // 12 > 9999:
        fail("projection horizon exceeds the supported calendar")
    business = model["business_model"]
    if not isinstance(business, str) or business not in SPECIFIC:
        fail(f"business_model: choose from {sorted(SPECIFIC)}")
    keys(model["opening"], OPENING, label="opening")
    for key, value in model["opening"].items():
        number(value, f"opening.{key}", -1e15 if key == "retained_earnings" else 0)
    o = model["opening"]
    delta = o["cash"] + o["ar"] + o["inventory"] + o["ppe"] - o["ap"] - o["debt"] - o["paid_in_capital"] - o["retained_earnings"]
    if abs(delta) > .01:
        fail(f"opening balance sheet does not reconcile: residual={delta:.6f}")
    keys(model["drivers"], COMMON | SPECIFIC[business], label="drivers")
    for key, value in model["drivers"].items():
        number(value, f"drivers.{key}", *LIMITS.get(key, (0, 1e12)))
    if business == "saas" and model["drivers"]["monthly_churn"] == 1:
        fail("monthly_churn: must be less than 1 for cohort and retention metrics")
    for collection in ("hiring", "financing"):
        if not isinstance(model[collection], list) or len(model[collection]) > 100:
            fail(f"{collection}: expected at most 100 entries")
    for i, hire in enumerate(model["hiring"]):
        keys(hire, {"role", "department", "start_month", "end_month", "count", "annual_salary", "load_factor"}, label=f"hiring.{i}")
        if not isinstance(hire["role"], str) or not 1 <= len(hire["role"]) <= 120:
            fail(f"hiring.{i}.role: expected a role name")
        if hire["department"] not in ("cogs", "sm", "rd", "ga"):
            fail(f"hiring.{i}.department: expected cogs/sm/rd/ga")
        integer(hire["start_month"], f"hiring.{i}.start_month", 1, model["months"])
        integer(hire["end_month"], f"hiring.{i}.end_month", hire["start_month"], model["months"])
        integer(hire["count"], f"hiring.{i}.count", 1, 100000)
        number(hire["annual_salary"], f"hiring.{i}.annual_salary")
        number(hire["load_factor"], f"hiring.{i}.load_factor", 1, 3)
    for i, event in enumerate(model["financing"]):
        keys(event, {"month", "equity", "pre_money", "debt_issued", "debt_repaid", "dividends"}, label=f"financing.{i}")
        integer(event["month"], f"financing.{i}.month", 1, model["months"])
        for key in ("equity", "pre_money", "debt_issued", "debt_repaid", "dividends"):
            number(event[key], f"financing.{i}.{key}")
        if event["equity"] > 0 and event["pre_money"] <= 0:
            fail("equity financing requires a positive pre_money valuation")
    keys(model["scenarios"], {"conservative", "base", "optimistic"}, label="scenarios")
    if model["scenarios"]["base"] != {}:
        fail("base scenario must be empty: drivers owns the base assumptions")
    for scenario, overrides in model["scenarios"].items():
        keys(overrides, (), model["drivers"].keys(), label=f"scenarios.{scenario}")
        for key, value in overrides.items():
            number(value, f"scenarios.{scenario}.{key}", *LIMITS.get(key, (0, 1e12)))
            if key == "monthly_churn" and value == 1:
                fail("scenario monthly_churn must be less than 1")
    p = model["provenance"]
    if not isinstance(p, dict) or len(p) > 2000:
        fail("provenance: expected an object with at most 2000 entries")
    needed = [path for section in ("opening", "drivers", "hiring", "financing", "scenarios")
              for path, value in leaves(model[section], section) if isinstance(value, (int, float))]
    if "*" in p and not model["synthetic"]:
        fail("wildcard provenance is allowed only for explicitly synthetic models")
    missing = [path for path in needed if path not in p and "*" not in p]
    if missing:
        fail(f"missing provenance for inputs: {', '.join(missing[:20])}")
    for path, source in p.items():
        keys(source, {"kind", "reference", "as_of"}, label=f"provenance.{path}")
        if source["kind"] not in ("actual", "assumption", "synthetic"):
            fail(f"provenance.{path}.kind: expected actual/assumption/synthetic")
        if source["kind"] == "synthetic" and not model["synthetic"]:
            fail("synthetic sources require synthetic=true")
        if not isinstance(source["reference"], str) or not 1 <= len(source["reference"]) <= 2000:
            fail(f"provenance.{path}.reference: expected a specific source or assumption rationale")
        try:
            dt.date.fromisoformat(source["as_of"])
        except (ValueError, TypeError):
            fail(f"provenance.{path}.as_of: expected YYYY-MM-DD")
    return {"valid": True, "input_count": len(needed), "synthetic": model["synthetic"],
            "assumption_count": sum(p.get(path, p.get("*"))["kind"] != "actual" for path in needed)}


def safe_ratio(a, b):
    return a / b if b > 0 else None


def forecast(model, scenario="base"):
    validation = validate(model)
    if scenario not in model["scenarios"]:
        fail("unknown scenario")
    d = dict(model["drivers"], **model["scenarios"][scenario])
    prior = copy.deepcopy(model["opening"])
    original_ownership = 1.0
    business = model["business_model"]
    cohorts = [[-1, d.get("opening_customers", 0)]] if business == "saas" else []
    prior_mrr = d.get("opening_customers", 0) * d.get("arpu", 0)
    rows, cohort_rows = [], []
    start = dt.date.fromisoformat(model["start_month"] + "-01")
    for index in range(model["months"]):
        month = index + 1
        calendar_index = start.year * 12 + start.month - 1 + index
        year, month0 = divmod(calendar_index, 12)
        days = calendar.monthrange(year, month0 + 1)[1]
        row = {"month": month, "period": f"{year:04d}-{month0 + 1:02d}", "days": days}
        acquisition = 0.0
        if business == "saas":
            new_customers = d["new_customers_monthly"] * (1 + d["monthly_acquisition_growth"]) ** index
            cohorts.append([index, new_customers])
            revenue = customers = 0.0
            for created, size in cohorts:
                age = index - created
                retained = size * (1 - d["monthly_churn"]) ** age
                mrr = retained * d["arpu"] * (1 + d["monthly_expansion"]) ** age
                customers += retained
                revenue += mrr
                cohort_rows.append({"period": row["period"], "cohort": "opening" if created == -1 else created + 1,
                                    "age_months": age, "customers": retained, "mrr": mrr})
            acquisition = new_customers * d["acquisition_cac"]
            row.update(customers=customers, new_customers=new_customers, mrr=revenue, arr=revenue * 12,
                       net_new_arr=(revenue - prior_mrr) * 12,
                       nrr_annual=((1 - d["monthly_churn"]) * (1 + d["monthly_expansion"])) ** 12)
            prior_mrr = revenue
        elif business == "corporate":
            revenue = d["initial_monthly_revenue"] * (1 + d["monthly_revenue_growth"]) ** index
        elif business == "marketplace":
            row["gmv"] = d["initial_monthly_gmv"] * (1 + d["monthly_gmv_growth"]) ** index
            revenue = row["gmv"] * d["take_rate"]
        elif business == "ecommerce":
            row["visitors"] = d["monthly_visitors"] * (1 + d["monthly_traffic_growth"]) ** index
            row["orders"] = row["visitors"] * d["conversion_rate"]
            revenue = row["orders"] * d["aov"]
        else:
            row["billable_hours"] = d["billable_staff"] * d["hours_per_staff_monthly"] * d["utilization"]
            revenue = row["billable_hours"] * d["hourly_rate"]
        payroll = {key: 0.0 for key in ("cogs", "sm", "rd", "ga")}
        headcount = 0
        for hire in model["hiring"]:
            if hire["start_month"] <= month <= hire["end_month"]:
                headcount += hire["count"]
                payroll[hire["department"]] += hire["count"] * hire["annual_salary"] * hire["load_factor"] / 12 * (1 + d["annual_salary_growth"]) ** ((month - hire["start_month"]) // 12)
        cogs = revenue * d["cogs_ratio"] + payroll["cogs"]
        sm = d["fixed_sm"] + acquisition + payroll["sm"]
        rd = d["fixed_rd"] + payroll["rd"]
        ga = d["fixed_ga"] + payroll["ga"]
        capex = d["capex_monthly"]
        depreciation = min(prior["ppe"] + capex, prior["ppe"] * d["monthly_depreciation_rate"])
        events = [event for event in model["financing"] if event["month"] == month]
        issued = sum(e["debt_issued"] for e in events)
        repaid = sum(e["debt_repaid"] for e in events)
        if repaid > prior["debt"] + issued + .0000001:
            fail(f"month {month}: repayment exceeds available debt")
        debt = max(0, prior["debt"] + issued - repaid)
        interest = (prior["debt"] + debt) / 2 * d["annual_interest_rate"] / 12
        equity_raised = sum(e["equity"] for e in events)
        dividends = sum(e["dividends"] for e in events)
        for event in events:
            if event["equity"]:
                original_ownership *= event["pre_money"] / (event["pre_money"] + event["equity"])
        gross_profit = revenue - cogs
        opex = sm + rd + ga
        ebitda = gross_profit - opex
        ebit = ebitda - depreciation
        ebt = ebit - interest
        tax = max(0, ebt) * d["tax_rate"]
        net_income = ebt - tax
        ar, inventory, ap = revenue * d["dso_days"] / days, cogs * d["dio_days"] / days, cogs * d["dpo_days"] / days
        cfo = net_income + depreciation - (ar - prior["ar"]) - (inventory - prior["inventory"]) + (ap - prior["ap"])
        cfi = -capex
        cff = issued - repaid + equity_raised - dividends
        cash_change = cfo + cfi + cff
        cash = prior["cash"] + cash_change
        ppe = prior["ppe"] + capex - depreciation
        paid_in_capital = prior["paid_in_capital"] + equity_raised
        retained_earnings = prior["retained_earnings"] + net_income - dividends
        assets = cash + ar + inventory + ppe
        liabilities = ap + debt
        equity = paid_in_capital + retained_earnings
        operating_burn = max(0, -(cfo + cfi))
        funding_gap = max(0, -cash)
        row.update(revenue=revenue, cogs=cogs, gross_profit=gross_profit, sm=sm, rd=rd, ga=ga,
                   opex=opex, ebitda=ebitda, depreciation=depreciation, ebit=ebit, interest=interest,
                   ebt=ebt, tax=tax, net_income=net_income, headcount=headcount, capex=capex,
                   ar=ar, inventory=inventory, ap=ap, debt=debt, ppe=ppe, paid_in_capital=paid_in_capital,
                   retained_earnings=retained_earnings, total_assets=assets, total_liabilities=liabilities,
                   total_equity=equity, beginning_cash=prior["cash"], cash=cash, cfo=cfo, cfi=cfi,
                   cff=cff, net_cash_change=cash_change, debt_issued=issued, debt_repaid=repaid,
                   equity_raised=equity_raised, dividends=dividends, acquisition_spend=acquisition,
                   operating_burn=operating_burn, funding_gap=funding_gap,
                   original_holder_ownership=original_ownership,
                   gross_margin=safe_ratio(gross_profit, revenue), ebitda_margin=safe_ratio(ebitda, revenue),
                   runway_at_current_burn=0 if cash <= 0 else safe_ratio(cash, operating_burn),
                   balance_residual=assets - liabilities - equity,
                   cash_residual=cash - prior["cash"] - cfo - cfi - cff)
        if business == "saas":
            cac = safe_ratio(acquisition + payroll["sm"] + d["fixed_sm"], row["new_customers"])
            unit_gross_profit = safe_ratio(gross_profit, row["customers"])
            ltv = safe_ratio(unit_gross_profit, d["monthly_churn"]) if unit_gross_profit is not None else None
            row.update(cac=cac, ltv=ltv, ltv_cac=safe_ratio(ltv, cac) if ltv is not None and cac is not None else None,
                       cac_payback_months=safe_ratio(cac, unit_gross_profit) if cac is not None and unit_gross_profit is not None else None,
                       burn_multiple=safe_ratio(operating_burn, row["net_new_arr"]))
        for key, value in row.items():
            if isinstance(value, (int, float)) and not math.isfinite(value):
                fail(f"month {month}: non-finite {key}")
        rows.append(row)
        prior = {key: row[key] for key in OPENING}
    checks = reconcile(model, rows)
    if not checks["passed"]:
        fail(f"forecast failed reconciliation: {checks['failures'][:3]}")
    annual = []
    for year in sorted({r["period"][:4] for r in rows}):
        subset = [r for r in rows if r["period"].startswith(year)]
        last = subset[-1]
        annual.append({"year": year, "months_in_period": len(subset),
                       **{key: sum(r.get(key, 0) for r in subset) for key in FLOW},
                       **{key: last[key] for key in ("cash", "debt", "ppe", "ar", "inventory", "ap", "total_assets", "total_equity", "headcount", "original_holder_ownership")},
                       "gross_margin": safe_ratio(sum(r["gross_profit"] for r in subset), sum(r["revenue"] for r in subset)),
                       **({"ending_arr": last["arr"]} if business == "saas" else {})})
    breach = next((r["period"] for r in rows if r["cash"] < 0), None)
    warnings = ["Synthetic fixture. These inputs are not company actuals."] if model["synthetic"] else []
    if breach:
        warnings.append(f"Cash first falls below zero in {breach}. No funding plug has been inserted.")
    warnings.extend([
        "Tax uses positive monthly pre-tax income without loss carryforwards or deferred tax.",
        "Working capital uses each calendar month's days and stable DSO/DIO/DPO; seasonality is not inferred.",
        "Runway at current burn is a point-in-time ratio. The projected first cash breach is reported separately.",
    ])
    if business == "saas":
        warnings.append("LTV uses current unit gross profit / monthly churn and excludes expansion; zero churn gives unavailable LTV.")
    return {"engine_version": __version__, "name": model["name"], "currency": model["currency"], "units": "whole",
            "synthetic": model["synthetic"], "business_model": business, "scenario": scenario,
            "validation": validation, "active_drivers": d, "monthly": rows, "annual": annual, "cohorts": cohort_rows,
            "checks": checks, "warnings": warnings,
            "summary": {"first_cash_breach": breach, "minimum_cash": min(r["cash"] for r in rows),
                        "maximum_funding_gap": max(r["funding_gap"] for r in rows), "ending_cash": rows[-1]["cash"],
                        "total_revenue": sum(r["revenue"] for r in rows), "final_period": rows[-1]["period"],
                        "original_holder_ownership": original_ownership}}


def reconcile(model, rows):
    """Review identities from statement components, independent of reported residuals."""
    failures, maximum = [], 0.0
    previous = model["opening"]
    for row in rows:
        identities = {
            "balance_sheet": row["cash"] + row["ar"] + row["inventory"] + row["ppe"] - row["ap"] - row["debt"] - row["paid_in_capital"] - row["retained_earnings"],
            "cash_rollforward": row["cash"] - previous["cash"] - row["cfo"] - row["cfi"] - row["cff"],
            "retained_earnings": row["retained_earnings"] - previous["retained_earnings"] - row["net_income"] + row["dividends"],
            "debt_rollforward": row["debt"] - previous["debt"] - row["debt_issued"] + row["debt_repaid"],
            "ppe_rollforward": row["ppe"] - previous["ppe"] - row["capex"] + row["depreciation"],
            "income_statement": row["net_income"] - (row["revenue"] - row["cogs"] - row["sm"] - row["rd"] - row["ga"] - row["depreciation"] - row["interest"] - row["tax"]),
            "operating_cash": row["cfo"] - (row["net_income"] + row["depreciation"] - row["ar"] + previous["ar"] - row["inventory"] + previous["inventory"] + row["ap"] - previous["ap"]),
        }
        for check, residual in identities.items():
            maximum = max(maximum, abs(residual))
            if not math.isfinite(residual) or abs(residual) > .01:
                failures.append({"period": row["period"], "check": check, "residual": residual})
        previous = row
    return {"passed": not failures, "tolerance": .01, "identities_per_month": 7,
            "checked_months": len(rows), "maximum_residual": maximum, "failures": failures}
