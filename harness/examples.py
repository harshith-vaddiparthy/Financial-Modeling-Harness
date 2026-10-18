"""Original synthetic fixtures. No borrowed company financials."""
from .engine import COMMON


def make_example(business="saas"):
    drivers = dict(cogs_ratio=.2, fixed_sm=1500, fixed_rd=800, fixed_ga=2500,
                   annual_salary_growth=.05, dso_days=15, dio_days=0, dpo_days=15,
                   capex_monthly=500, monthly_depreciation_rate=.02, annual_interest_rate=.08, tax_rate=.25)
    variants = {
        "saas": dict(opening_customers=100, new_customers_monthly=12, monthly_acquisition_growth=.025,
                     arpu=250, monthly_churn=.02, monthly_expansion=.005, acquisition_cac=700),
        "corporate": dict(initial_monthly_revenue=60000, monthly_revenue_growth=.01),
        "marketplace": dict(initial_monthly_gmv=350000, monthly_gmv_growth=.02, take_rate=.15),
        "ecommerce": dict(monthly_visitors=50000, monthly_traffic_growth=.015, conversion_rate=.025, aov=60),
        "services": dict(billable_staff=4, hours_per_staff_monthly=160, utilization=.7, hourly_rate=110),
    }
    drivers.update(variants[business])
    if business == "ecommerce":
        drivers.update(cogs_ratio=.55, dio_days=30, dpo_days=25)
    scenario_driver = {"saas": "new_customers_monthly", "corporate": "monthly_revenue_growth",
                       "marketplace": "monthly_gmv_growth", "ecommerce": "conversion_rate", "services": "utilization"}[business]
    base = drivers[scenario_driver]
    conservative, optimistic = {scenario_driver: base * .7}, {scenario_driver: base * 1.3}
    if business == "saas":
        conservative.update(monthly_churn=.03, acquisition_cac=850)
        optimistic.update(monthly_churn=.015, acquisition_cac=600)
    return {
        "schema_version": 1, "name": f"Example {business.title()} Company", "currency": "USD", "units": "whole",
        "start_month": "2027-01", "months": 36, "business_model": business, "synthetic": True,
        "opening": dict(cash=300000, ar=10000, inventory=0, ppe=20000, ap=5000, debt=25000, paid_in_capital=300000, retained_earnings=0),
        "drivers": drivers,
        "hiring": [
            dict(role="Engineer", department="rd", start_month=1, end_month=36, count=2, annual_salary=100000, load_factor=1.3),
            dict(role="Operations", department="ga", start_month=1, end_month=36, count=1, annual_salary=60000, load_factor=1.25),
            dict(role="Account executive", department="sm", start_month=7, end_month=36, count=1, annual_salary=70000, load_factor=1.3),
        ],
        "financing": [dict(month=12, equity=500000, pre_money=2500000, debt_issued=0, debt_repaid=25000, dividends=0)],
        "scenarios": {"conservative": conservative, "base": {}, "optimistic": optimistic},
        "provenance": {"*": {"kind": "synthetic", "reference": "Original demonstration fixture; not company actuals or market benchmarks", "as_of": "2026-10-18"}},
    }
