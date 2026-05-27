#!/usr/bin/env python3
import argparse
import html
import json
from pathlib import Path


def badge(value: bool) -> str:
    css = "pass" if value else "fail"
    text = "PASS" if value else "FAIL"
    return f'<span class="{css}">{text}</span>'


def main() -> None:
    parser = argparse.ArgumentParser(description="Render compliance results as HTML.")
    parser.add_argument("--input", required=True, help="Input JSON results file.")
    parser.add_argument("--output", required=True, help="Output HTML report file.")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as file:
        data = json.load(file)

    detail_rows = []
    for item in data["results"]:
        detail_rows.append(
            "<tr>"
            f"<td>{html.escape(item['item'])}</td>"
            f"<td>{html.escape(item['framework'])}</td>"
            f"<td>{html.escape(item['severity'])}</td>"
            f"<td>{item['points']}</td>"
            f"<td>{html.escape(item['title'])}</td>"
            f"<td><code>{html.escape(item['check'])}</code></td>"
            f"<td>{badge(item['passed'])}</td>"
            "</tr>"
        )

    grouped_rows = []
    for item in data["grouped_by_check"]:
        frameworks = ", ".join(item["related_frameworks"])
        grouped_rows.append(
            "<tr>"
            f"<td><code>{html.escape(item['check'])}</code></td>"
            f"<td>{html.escape(frameworks)}</td>"
            f"<td>{badge(item['passed'])}</td>"
            "</tr>"
        )

    html_output = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Cloud Compliance Pipeline Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 40px; color: #222; }}
    h1, h2 {{ color: #111; }}
    .summary {{ display: flex; gap: 16px; margin: 24px 0; flex-wrap: wrap; }}
    .card {{ border: 1px solid #ddd; border-radius: 10px; padding: 16px; min-width: 220px; background: #fafafa; }}
    .value {{ font-size: 28px; font-weight: bold; margin-top: 8px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 20px 0 40px; }}
    th, td {{ border: 1px solid #ddd; padding: 10px; vertical-align: top; }}
    th {{ background: #202020; color: #fff; text-align: left; }}
    tr:nth-child(even) {{ background: #f8f8f8; }}
    code {{ background: #eee; padding: 2px 5px; border-radius: 4px; }}
    .pass {{ color: #087f23; font-weight: bold; }}
    .fail {{ color: #b00020; font-weight: bold; }}
    .meta {{ color: #555; }}
  </style>
</head>
<body>
  <h1>Cloud Compliance Pipeline Report</h1>
  <p class="meta">Frameworks selected: {html.escape(', '.join(data['selected_frameworks']))}</p>

  <section class="summary">
    <div class="card">
      <div>Final score</div>
      <div class="value">{data['final_score_percent']}%</div>
    </div>
    <div class="card">
      <div>Achieved points</div>
      <div class="value">{data['achieved_score']}</div>
    </div>
    <div class="card">
      <div>Total possible points</div>
      <div class="value">{data['total_score']}</div>
    </div>
  </section>

  <h2>Control Summary by Reusable Check</h2>
  <table>
    <thead>
      <tr>
        <th>Reusable Item</th>
        <th>Related Frameworks</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
      {''.join(grouped_rows)}
    </tbody>
  </table>

  <h2>Detailed Audit Results</h2>
  <table>
    <thead>
      <tr>
        <th>Item</th>
        <th>Framework</th>
        <th>Severity</th>
        <th>Points</th>
        <th>Description</th>
        <th>Reusable Check</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
      {''.join(detail_rows)}
    </tbody>
  </table>
</body>
</html>
"""

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as file:
        file.write(html_output)


if __name__ == "__main__":
    main()
