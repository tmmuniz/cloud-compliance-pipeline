#!/usr/bin/env python3
import argparse
import html
import json
from pathlib import Path


def badge(status: str) -> str:
    css_class = "pass" if status == "PASS" else "fail"
    return f'<span class="badge {css_class}">{status}</span>'


def pct(value: float) -> str:
    return f"{value:.2f}%"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render compliance results as an HTML report.")
    parser.add_argument("--input", required=True, help="Path to results JSON file.")
    parser.add_argument("--output", required=True, help="Path to HTML report file.")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as file:
        data = json.load(file)

    framework_rows = ""
    for framework, summary in data["framework_summary"].items():
        framework_rows += f"""
        <tr>
          <td>{html.escape(framework)}</td>
          <td>{summary['passed']}</td>
          <td>{summary['failed']}</td>
          <td>{summary['achieved_score']}</td>
          <td>{summary['total_score']}</td>
          <td>{pct(summary['score_percent'])}</td>
        </tr>
        """

    result_rows = ""
    for item in data["results"]:
        related = ", ".join(item.get("related_frameworks", []))
        result_rows += f"""
        <tr>
          <td>{html.escape(item['id'])}</td>
          <td>{html.escape(item['framework'])}</td>
          <td>{html.escape(related)}</td>
          <td class="severity {html.escape(item['severity'].lower())}">{html.escape(item['severity'])}</td>
          <td>{item['score']}</td>
          <td>{html.escape(item['title'])}</td>
          <td><code>{html.escape(item['check'])}</code></td>
          <td>{badge(item['status'])}</td>
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
    .score {{
      font-size: 32px;
      font-weight: 700;
      margin: 8px 0;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: #ffffff;
      font-size: 14px;
    }}
    th {{
      background: #24292f;
      color: #ffffff;
      text-align: left;
      position: sticky;
      top: 0;
    }}
    th, td {{
      border: 1px solid #d0d7de;
      padding: 10px;
      vertical-align: top;
    }}
    code {{
      background: #f6f8fa;
      padding: 2px 5px;
      border-radius: 4px;
    }}
    .badge {{
      border-radius: 999px;
      color: white;
      display: inline-block;
      font-weight: 700;
      padding: 4px 10px;
    }}
    .pass {{ background: #1a7f37; }}
    .fail {{ background: #cf222e; }}
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
    <p>{data['achieved_score']} of {data['total_score']} points achieved across {data['total_controls']} controls.</p>
  </div>

  <div class="card">
    <h2>Score by Framework</h2>
    <table>
      <thead>
        <tr>
          <th>Framework</th>
          <th>Passed</th>
          <th>Failed</th>
          <th>Achieved Points</th>
          <th>Total Points</th>
          <th>Score</th>
        </tr>
      </thead>
      <tbody>{framework_rows}</tbody>
    </table>
  </div>

  <div class="card">
    <h2>Detailed Audit Results</h2>
    <table>
      <thead>
        <tr>
          <th>Item</th>
          <th>Framework</th>
          <th>Related Frameworks</th>
          <th>Severity</th>
          <th>Points</th>
          <th>Control Item</th>
          <th>OPA/Rego Check</th>
          <th>Status</th>
        </tr>
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
