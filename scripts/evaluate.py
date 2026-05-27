#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml


def run_opa(plan_path: str, rego_path: str, check: str) -> bool:
    command = [
        "opa",
        "eval",
        "--format",
        "json",
        "--input",
        plan_path,
        "--data",
        rego_path,
        f"data.cloud.compliance.{check}",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)

    if result.returncode != 0:
        print(f"OPA error for check {check}: {result.stderr}", file=sys.stderr)
        return False

    try:
        payload = json.loads(result.stdout)
        return payload["result"][0]["expressions"][0]["value"] is True
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return False


def normalize_frameworks(raw: str) -> list[str]:
    return [item.strip().upper() for item in raw.split(",") if item.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Terraform plan JSON against compliance controls.")
    parser.add_argument("--plan", required=True, help="Terraform plan JSON path.")
    parser.add_argument("--controls", required=True, help="Controls YAML path.")
    parser.add_argument("--rego", default="policy/compliance.rego", help="OPA/Rego policy path.")
    parser.add_argument("--frameworks", required=True, help="Comma-separated framework list.")
    parser.add_argument("--output", required=True, help="Output JSON file.")
    args = parser.parse_args()

    selected_frameworks = normalize_frameworks(args.frameworks)

    with open(args.controls, "r", encoding="utf-8") as file:
        controls = yaml.safe_load(file)

    templates = controls["framework_templates"]
    points = controls["severity_points"]

    unknown = [fw for fw in selected_frameworks if fw not in templates]
    if unknown:
        raise ValueError(f"Unknown frameworks: {', '.join(unknown)}")

    results = []
    total_score = 0
    achieved_score = 0

    for framework in selected_frameworks:
        for severity in ["HIGH", "MEDIUM", "LOW"]:
            controls_for_severity = templates[framework][severity.lower()]
            for index, control in enumerate(controls_for_severity, start=1):
                check = control["check"]
                title = control["title"]
                score = int(points[severity])
                passed = run_opa(args.plan, args.rego, check)

                total_score += score
                if passed:
                    achieved_score += score

                results.append(
                    {
                        "framework": framework,
                        "item": f"{framework}-{severity[0]}{index:02}",
                        "severity": severity,
                        "points": score,
                        "title": title,
                        "check": check,
                        "passed": passed,
                    }
                )

    final_score_percent = round((achieved_score / total_score) * 100, 2) if total_score else 0

    grouped_by_check = {}
    for item in results:
        key = item["check"]
        grouped_by_check.setdefault(
            key,
            {
                "check": key,
                "related_frameworks": [],
                "passed": item["passed"],
            },
        )
        if item["framework"] not in grouped_by_check[key]["related_frameworks"]:
            grouped_by_check[key]["related_frameworks"].append(item["framework"])
        grouped_by_check[key]["passed"] = grouped_by_check[key]["passed"] and item["passed"]

    output = {
        "selected_frameworks": selected_frameworks,
        "total_score": total_score,
        "achieved_score": achieved_score,
        "final_score_percent": final_score_percent,
        "results": results,
        "grouped_by_check": list(grouped_by_check.values()),
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as file:
        json.dump(output, file, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
