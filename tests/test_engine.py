import copy
import unittest

from harness.engine import ModelError, forecast, reconcile, validate, leaves
from harness.examples import make_example
from harness.__main__ import sensitivity


class FinancialModelTests(unittest.TestCase):
    def test_all_models_and_scenarios_reconcile(self):
        for kind in ("saas", "corporate", "marketplace", "ecommerce", "services"):
            for scenario in ("conservative", "base", "optimistic"):
                with self.subTest(kind=kind, scenario=scenario):
                    result = forecast(make_example(kind), scenario)
                    self.assertTrue(result["checks"]["passed"])
                    self.assertEqual(len(result["monthly"]), 36)
                    self.assertAlmostEqual(result["summary"]["original_holder_ownership"], 5 / 6)

    def test_independently_calculated_corporate_month(self):
        m = make_example("corporate")
        m["hiring"], m["financing"] = [], []
        m["drivers"].update(initial_monthly_revenue=31000, cogs_ratio=.2, fixed_sm=1000,
                            fixed_rd=2000, fixed_ga=3000, dso_days=31, dio_days=0, dpo_days=31,
                            capex_monthly=1000, monthly_depreciation_rate=.1, annual_interest_rate=.12, tax_rate=.25)
        r = forecast(m)["monthly"][0]
        # Jan has 31 days. Opening debt 25k, PP&E 20k, AR 10k, AP 5k.
        self.assertEqual(r["revenue"], 31000)
        self.assertEqual(r["cogs"], 6200)
        self.assertEqual(r["depreciation"], 2000)
        self.assertEqual(r["interest"], 250)
        self.assertEqual(r["net_income"], 12412.5)
        self.assertEqual(r["cfo"], -5387.5)
        self.assertEqual(r["cash"], 293612.5)

    def test_cohort_retention_and_expansion(self):
        m = make_example()
        m["drivers"].update(opening_customers=100, new_customers_monthly=10, monthly_acquisition_growth=0,
                            arpu=100, monthly_churn=.1, monthly_expansion=.02)
        r = forecast(m)
        self.assertAlmostEqual(r["monthly"][0]["customers"], 100)
        self.assertAlmostEqual(r["monthly"][0]["revenue"], 90 * 102 + 10 * 100)
        self.assertAlmostEqual(r["monthly"][1]["customers"], 81 + 9 + 10)
        self.assertAlmostEqual(r["monthly"][1]["revenue"], 81 * 104.04 + 9 * 102 + 10 * 100)
        self.assertAlmostEqual(sum(x["mrr"] for x in r["cohorts"] if x["period"] == "2027-01"), r["monthly"][0]["mrr"])
        self.assertEqual(r["monthly"][0]["arr"], r["monthly"][0]["mrr"] * 12)

    def test_opening_balance_mismatch_rejected(self):
        m = make_example()
        m["opening"]["cash"] += 100
        with self.assertRaisesRegex(ModelError, "opening balance sheet"):
            forecast(m)

    def test_negative_cash_is_not_plugged(self):
        m = make_example("corporate")
        m["opening"] = {key: 0 for key in m["opening"]}
        m["drivers"]["initial_monthly_revenue"] = 0
        m["financing"] = []
        r = forecast(m)
        self.assertEqual(r["summary"]["first_cash_breach"], "2027-01")
        self.assertLess(r["monthly"][0]["cash"], 0)
        self.assertGreater(r["summary"]["maximum_funding_gap"], 0)
        self.assertTrue(r["checks"]["passed"])

    def test_zero_churn_has_unavailable_ltv(self):
        m = make_example()
        m["drivers"]["monthly_churn"] = 0
        r = forecast(m)["monthly"][0]
        self.assertIsNone(r["ltv"])
        self.assertIsNone(r["ltv_cac"])

    def test_no_new_customers_has_unavailable_cac(self):
        m = make_example()
        m["drivers"]["new_customers_monthly"] = 0
        self.assertIsNone(forecast(m)["monthly"][0]["cac"])

    def test_monthly_debt_average_and_repayment_cap(self):
        m = make_example()
        m["financing"] = [{"month": 1, "equity": 0, "pre_money": 0, "debt_issued": 15000, "debt_repaid": 10000, "dividends": 0}]
        r = forecast(m)["monthly"][0]
        self.assertEqual(r["debt"], 30000)
        self.assertAlmostEqual(r["interest"], 27500 * .08 / 12)
        m["financing"][0]["debt_repaid"] = 50000
        with self.assertRaisesRegex(ModelError, "repayment exceeds"):
            forecast(m)

    def test_hiring_dates_and_annual_raise(self):
        m = make_example("corporate")
        m["drivers"].update(fixed_rd=0, annual_salary_growth=.1)
        m["hiring"] = [dict(role="Engineer", department="rd", start_month=2, end_month=15, count=1, annual_salary=120000, load_factor=1.2)]
        r = forecast(m)["monthly"]
        self.assertEqual(r[0]["headcount"], 0)
        self.assertEqual(r[1]["rd"], 12000)
        self.assertEqual(r[12]["rd"], 12000)
        self.assertAlmostEqual(r[13]["rd"], 13200)
        self.assertEqual(r[15]["rd"], 0)

    def test_retained_earnings_with_dividend(self):
        m = make_example("corporate")
        m["financing"] = [dict(month=1, equity=0, pre_money=0, debt_issued=0, debt_repaid=0, dividends=1000)]
        r = forecast(m)["monthly"][0]
        self.assertAlmostEqual(r["retained_earnings"], r["net_income"] - 1000)
        self.assertEqual(r["cff"], -1000)

    def test_partial_calendar_years_and_leap_month(self):
        m = make_example("corporate")
        m["start_month"] = "2028-02"
        r = forecast(m)
        self.assertEqual(r["monthly"][0]["days"], 29)
        self.assertEqual(r["annual"][0]["months_in_period"], 11)
        self.assertEqual(r["annual"][-1]["months_in_period"], 1)
        self.assertEqual(r["annual"][0]["cash"], r["monthly"][10]["cash"])
        self.assertAlmostEqual(r["annual"][0]["revenue"], sum(x["revenue"] for x in r["monthly"][:11]))

    def test_missing_null_bool_unknown_nonfinite_and_bad_rate(self):
        for value in (None, True, float("nan"), float("inf"), -.1, 1.1):
            m = make_example()
            m["drivers"]["cogs_ratio"] = value
            with self.subTest(value=value), self.assertRaises(ModelError):
                forecast(m)
        m = make_example()
        del m["drivers"]["arpu"]
        with self.assertRaises(ModelError):
            forecast(m)
        m = make_example()
        m["drivers"]["random_growth"] = .2
        with self.assertRaises(ModelError):
            forecast(m)

    def test_real_models_need_exact_provenance(self):
        m = make_example()
        m["synthetic"] = False
        with self.assertRaisesRegex(ModelError, "wildcard"):
            validate(m)
        m["provenance"] = {}
        with self.assertRaisesRegex(ModelError, "missing provenance"):
            validate(m)

    def test_complete_real_model_with_explicit_assumptions(self):
        m = make_example()
        m["synthetic"] = False
        m["provenance"] = {}
        for section in ("opening", "drivers", "hiring", "financing", "scenarios"):
            for path, value in leaves(m[section], section):
                if isinstance(value, (int, float)):
                    m["provenance"][path] = {"kind": "assumption", "reference": "Explicit analyst assumption for this test", "as_of": "2026-10-18"}
        self.assertTrue(validate(m)["valid"])
        self.assertTrue(forecast(m)["checks"]["passed"])

    def test_independent_reconciliation_detects_corrupted_components(self):
        m = make_example()
        r = forecast(m)
        r["monthly"][0]["cash"] += 1
        self.assertFalse(reconcile(m, r["monthly"])["passed"])

    def test_sensitivity_full_recalculation_and_no_input_mutation(self):
        m = make_example()
        before = copy.deepcopy(m)
        r = sensitivity(m, "monthly_churn", [.01, .02, .03])
        self.assertGreater(r["results"][0]["total_revenue"], r["results"][2]["total_revenue"])
        self.assertEqual(m, before)

    def test_scenarios_recalculate_cost_and_cash(self):
        m = make_example()
        base = forecast(m, "base")
        low = forecast(m, "conservative")
        self.assertNotEqual(base["monthly"][0]["cogs"], low["monthly"][0]["cogs"])
        self.assertNotEqual(base["monthly"][0]["ar"], low["monthly"][0]["ar"])
        self.assertGreater(base["summary"]["total_revenue"], low["summary"]["total_revenue"])

    def test_loss_month_does_not_create_tax_refund(self):
        m = make_example()
        m["drivers"]["fixed_ga"] = 1000000
        row = forecast(m)["monthly"][0]
        self.assertLess(row["ebt"], 0)
        self.assertEqual(row["tax"], 0)


if __name__ == "__main__":
    unittest.main()
