#!/usr/bin/env python3
import argparse
import html
import json
from collections import defaultdict
from pathlib import Path


STATUS_CLASSES = {
    "PASS": "pass",
    "FAIL": "fail",
    "OPA_ERROR": "error",
    "UNDEFINED": "undefined",
}


def badge(status: str) -> str:
    css_class = STATUS_CLASSES.get(status, "undefined")
    return f'<span class="badge {css_class}">{html.escape(status)}</span>'


def pct(value: float) -> str:
    return f"{value:.2f}%"


def status_priority(status: str) -> int:
    return {
        "OPA_ERROR": 0,
        "UNDEFINED": 1,
        "FAIL": 2,
        "PASS": 3,
    }.get(status, 1)


def aggregate_status(statuses: list[str]) -> str:
    if any(status == "OPA_ERROR" for status in statuses):
        return "OPA_ERROR"
    if any(status == "UNDEFINED" for status in statuses):
        return "UNDEFINED"
    if all(status == "PASS" for status in statuses):
        return "PASS"
    return "FAIL"


def count_status(results: list[dict], status: str) -> int:
    return sum(1 for item in results if item.get("status") == status)


def grouped_controls(results: list[dict]) -> list[dict]:
    grouped = {}
    for item in results:
        control_id = item["control"]
        if control_id not in grouped:
            grouped[control_id] = {
                "control": control_id,
                "title": item["title"],
                "check": item["check"],
                "frameworks": set(),
                "domains": set(),
                "statuses": [],
                "highest_severity": "LOW",
            }

        grouped[control_id]["frameworks"].add(item["framework"])
        grouped[control_id]["domains"].add(f"{item['framework']}: {item.get('domain', 'General')}")
        grouped[control_id]["statuses"].append(item.get("status", "PASS" if item.get("passed") else "FAIL"))

        if item["severity"] == "HIGH":
            grouped[control_id]["highest_severity"] = "HIGH"
        elif item["severity"] == "MEDIUM" and grouped[control_id]["highest_severity"] != "HIGH":
            grouped[control_id]["highest_severity"] = "MEDIUM"

    rows = []
    for item in grouped.values():
        item["frameworks"] = sorted(item["frameworks"])
        item["domains"] = sorted(item["domains"])
        item["status"] = aggregate_status(item["statuses"])
        item["usage_count"] = len(item["statuses"])
        rows.append(item)

    return sorted(rows, key=lambda item: (status_priority(item["status"]), item["control"]))


def domain_summary_rows(results: list[dict]) -> str:
    domains = defaultdict(lambda: {
        "passed": 0,
        "failed": 0,
        "opa_error": 0,
        "undefined": 0,
        "achieved_score": 0,
        "total_score": 0,
    })

    for item in results:
        key = (item["framework"], item.get("domain", "General"))
        status = item.get("status", "FAIL")
        score = int(item.get("score", 0))
        domains[key]["total_score"] += score

        if status == "PASS":
            domains[key]["passed"] += 1
            domains[key]["achieved_score"] += score
        elif status == "OPA_ERROR":
            domains[key]["opa_error"] += 1
        elif status == "UNDEFINED":
            domains[key]["undefined"] += 1
        else:
            domains[key]["failed"] += 1

    rows = ""
    for (framework, domain), summary in sorted(domains.items()):
        percent = (summary["achieved_score"] / summary["total_score"] * 100) if summary["total_score"] else 0
        rows += f"""
        <tr>
          <td>{html.escape(framework)}</td>
          <td>{html.escape(domain)}</td>
          <td>{summary['passed']}</td>
          <td>{summary['failed']}</td>
          <td>{summary['opa_error']}</td>
          <td>{summary['undefined']}</td>
          <td>{summary['achieved_score']}</td>
          <td>{summary['total_score']}</td>
          <td>{pct(percent)}</td>
        </tr>
        """
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Render compliance results as an HTML report.")
    parser.add_argument("--input", required=True, help="Path to results JSON file.")
    parser.add_argument("--output", required=True, help="Path to HTML report file.")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as file:
        data = json.load(file)

    opa_errors = count_status(data["results"], "OPA_ERROR")
    undefined = count_status(data["results"], "UNDEFINED")
    failed = count_status(data["results"], "FAIL")
    passed = count_status(data["results"], "PASS")

    framework_rows = ""
    for framework, summary in data["framework_summary"].items():
        framework_rows += f"""
        <tr>
          <td>{html.escape(framework)}</td>
          <td>{summary.get('passed', 0)}</td>
          <td>{summary.get('failed', 0)}</td>
          <td>{summary.get('opa_error', 0)}</td>
          <td>{summary.get('undefined', 0)}</td>
          <td>{summary['achieved_score']}</td>
          <td>{summary['total_score']}</td>
          <td>{pct(summary['score_percent'])}</td>
        </tr>
        """

    relationship_rows = ""
    for item in grouped_controls(data["results"]):
        frameworks = ", ".join(item["frameworks"])
        domains = "; ".join(item["domains"])
        relationship_rows += f"""
        <tr>
          <td><code>{html.escape(item['control'])}</code></td>
          <td>{html.escape(item['title'])}</td>
          <td>{html.escape(frameworks)}</td>
          <td>{html.escape(domains)}</td>
          <td>{item['usage_count']}</td>
          <td class="severity {html.escape(item['highest_severity'].lower())}">{html.escape(item['highest_severity'])}</td>
          <td><code>{html.escape(item['check'])}</code></td>
          <td>{badge(item['status'])}</td>
        </tr>
        """

    result_rows = ""
    for item in data["results"]:
        related = ", ".join(item.get("related_frameworks", []))
        status = item.get("status", "PASS" if item.get("passed") else "FAIL")
        message = item.get("message", "")
        result_rows += f"""
        <tr>
          <td>{html.escape(item['id'])}</td>
          <td>{html.escape(item['framework'])}</td>
          <td>{html.escape(item.get('domain', 'General'))}</td>
          <td><code>{html.escape(item['control'])}</code></td>
          <td>{html.escape(related)}</td>
          <td class="severity {html.escape(item['severity'].lower())}">{html.escape(item['severity'])}</td>
          <td>{item['score']}</td>
          <td>{html.escape(item.get('requirement', item['title']))}</td>
          <td>{html.escape(item['title'])}</td>
          <td><code>{html.escape(item['check'])}</code></td>
          <td>{badge(status)}</td>
          <td>{html.escape(message)}</td>
        </tr>
        """

    html_report = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Cloud Compliance Pipeline Report</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 32px;
      background: #f6f8fa;
      color: #24292f;
    }}
    h1, h2 {{ margin-bottom: 8px; }}
    .card {{
      background: #ffffff;
      border: 1px solid #d0d7de;
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 24px;
      box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }}
    .score {{ font-size: 32px; font-weight: 700; margin: 8px 0; }}
    .summary-grid {{ display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 12px; margin-top: 16px; }}
    .summary-box {{ background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 10px; padding: 12px; }}
    .summary-box strong {{ display: block; font-size: 22px; }}
    table {{ width: 100%; border-collapse: collapse; background: #ffffff; font-size: 14px; }}
    th {{ background: #24292f; color: #ffffff; text-align: left; position: sticky; top: 0; }}
    th, td {{ border: 1px solid #d0d7de; padding: 10px; vertical-align: top; }}
    code {{ background: #f6f8fa; padding: 2px 5px; border-radius: 4px; }}
    .badge {{ border-radius: 999px; color: white; display: inline-block; font-weight: 700; padding: 4px 10px; white-space: nowrap; }}
    .pass {{ background: #1a7f37; }}
    .fail {{ background: #cf222e; }}
    .error {{ background: #8250df; }}
    .undefined {{ background: #57606a; }}
    .severity.high {{ color: #cf222e; font-weight: 700; }}
    .severity.medium {{ color: #9a6700; font-weight: 700; }}
    .severity.low {{ color: #0969da; font-weight: 700; }}
    .meta {{ color: #57606a; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>Cloud Compliance Pipeline Report</h1>
    <p class="meta">Selected frameworks: {html.escape(', '.join(data['selected_frameworks']))}</p>
    <div class="score">Final Score: {pct(data['final_score_percent'])}</div>
    <p>{data['achieved_score']} of {data['total_score']} points achieved across {data['total_controls']} framework control items.</p>
    <div class="summary-grid">
      <div class="summary-box"><strong>{passed}</strong>PASS</div>
      <div class="summary-box"><strong>{failed}</strong>FAIL</div>
      <div class="summary-box"><strong>{opa_errors}</strong>OPA_ERROR</div>
      <div class="summary-box"><strong>{undefined}</strong>UNDEFINED</div>
    </div>
  </div>

  <div class="card">
    <h2>Score by Framework</h2>
    <table>
      <thead>
        <tr><th>Framework</th><th>Passed</th><th>Failed</th><th>OPA Errors</th><th>Undefined</th><th>Achieved Points</th><th>Total Points</th><th>Score</th></tr>
      </thead>
      <tbody>{framework_rows}</tbody>
    </table>
  </div>

  <div class="card">
    <h2>Score by Framework Domain</h2>
    <p class="meta">Domains are defined in frameworks.yaml to make each framework-specific audit easier to interpret.</p>
    <table>
      <thead>
        <tr><th>Framework</th><th>Domain</th><th>Passed</th><th>Failed</th><th>OPA Errors</th><th>Undefined</th><th>Achieved Points</th><th>Total Points</th><th>Score</th></tr>
      </thead>
      <tbody>{domain_summary_rows(data['results'])}</tbody>
    </table>
  </div>

  <div class="card">
    <h2>Control Relationships Across Frameworks</h2>
    <p class="meta">This table is generated by matching the same technical control ID from frameworks.yaml to controls.yaml.</p>
    <table>
      <thead>
        <tr><th>Technical Control</th><th>Control Title</th><th>Related Frameworks in This Run</th><th>Framework Domains</th><th>Mapped Items</th><th>Highest Severity</th><th>OPA/Rego Check</th><th>Status</th></tr>
      </thead>
      <tbody>{relationship_rows}</tbody>
    </table>
  </div>

  <div class="card">
    <h2>Detailed Audit Results</h2>
    <table>
      <thead>
        <tr><th>Item</th><th>Framework</th><th>Domain</th><th>Technical Control</th><th>All Related Frameworks</th><th>Severity</th><th>Points</th><th>Framework Requirement</th><th>Control Item</th><th>OPA/Rego Check</th><th>Status</th><th>Evaluation Message</th></tr>
      </thead>
      <tbody>{result_rows}</tbody>
    </table>
  </div>
</body>
</html>
"""

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as file:
        file.write(html_report)


if __name__ == "__main__":
    main()
