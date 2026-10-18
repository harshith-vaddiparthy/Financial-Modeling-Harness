"""Portable reports and CSV exports. All output is derived from saved results."""
import csv
import html
import json


def write_csv(path, rows):
    if not rows:
        return
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            safe = {key: ("'" + value if isinstance(value, str) and value.startswith(("=", "+", "-", "@")) else value)
                    for key, value in row.items()}
            writer.writerow(safe)


def write_reports(directory, model, results):
    for scenario, result in results.items():
        write_csv(directory / f"{scenario}-monthly.csv", result["monthly"])
        write_csv(directory / f"{scenario}-annual.csv", result["annual"])
        write_csv(directory / f"{scenario}-cohorts.csv", result["cohorts"])
    notes = [f"# {model['name']}", "", f"Currency: {model['currency']}. Monetary values: whole units.",
             f"Business model: {model['business_model']}. Synthetic: {model['synthetic']}.", "",
             "| Scenario | Total revenue | Ending cash | First cash breach | Maximum funding gap |",
             "| --- | ---: | ---: | --- | ---: |"]
    for scenario, result in results.items():
        s = result["summary"]
        notes.append(f"| {scenario} | {s['total_revenue']:,.2f} | {s['ending_cash']:,.2f} | {s['first_cash_breach'] or 'None in forecast horizon'} | {s['maximum_funding_gap']:,.2f} |")
    notes += ["", "## Method and assumptions", ""]
    notes += [f"- {warning}" for warning in next(iter(results.values()))["warnings"]]
    notes += ["", "Input and provenance: input.json. Full statements and checks: results.json.",
              "CSV exports and this report are snapshots. Change inputs and run again to refresh.",
              "Conservative/base/optimistic are named scenarios, not probability percentiles."]
    (directory / "report.md").write_text("\n".join(notes) + "\n", encoding="utf-8")
    template = (__import__("pathlib").Path(__file__).parent / "report.html").read_text()
    payload = json.dumps({"model": model, "results": results}, allow_nan=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    template = template.replace("__TITLE__", html.escape(model["name"])).replace("__PAYLOAD__", payload)
    (directory / "report.html").write_text(template, encoding="utf-8")
