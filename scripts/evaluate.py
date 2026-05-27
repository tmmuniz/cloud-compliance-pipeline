#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import yaml

VALID_FRAMEWORKS = {
    "GDPR",
    "NIST_CSF",
    "CIS",
    "ISO27001",
    "PCI_DSS",
    "SOC2",
    "MITRE",
    "LGPD",
    "BACEN",
    "OPEN_FINANCE",
}

POINTS = {
    "HIGH": 5,
    "MEDIUM": 3,
    "LOW": 1,
}


def normalize_frameworks(raw_framework: str) -> list[str]:
    selected = [item.strip().upper() for item in raw_framework.split(",") if item.strip()]

    if not selected or "ALL" in selected:
        return sorted(VALID_FRAMEWORKS)

    invalid = sorted(set(selected) - VALID_FRAMEWORKS)
    if invalid:
        raise ValueError(
            f"Invalid FRAMEWORK value(s): {', '.join(invalid)}. "
            f"Use ALL or one/more of: {', '.join(sorted(VALID_FRAMEWORKS))}."
        )

    return selected


def run_opa(plan_path: str, check: str) -> bool:
    command = [
        "opa",
        "eval",
        "--format",
        "json",
        "-i",
        plan_path,
        "-d",
        "policy/compliance.rego",
        f"data.cloud.compliance.{check}",
    ]

    completed = subprocess.run(command, capture_output=True, text=True, check=False)

    if completed.returncode != 0:
        print(f"OPA evaluation failed for check '{check}': {completed.stderr}", file=sys.stderr)
        return False

    try:
        data = json.loads(completed.stdout)
        return data["result"][0]["expressions"][0]["value"] is True
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return False


def build_related_frameworks(frameworks_map: dict) -> dict[str, list[str]]:
    related = defaultdict(set)
    for framework, items in frameworks_map.items():
        for item in items:
            related[item["control"]].add(framework)
    return {control: sorted(frameworks) for control, frameworks in related.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Terraform plan JSON against framework mappings using OPA/Rego.")
    parser.add_argument("--plan", required=True, help="Path to Terraform plan JSON file.")
    parser.add_argument("--controls", required=True, help="Path to technical controls catalog YAML file.")
    parser.add_argument("--frameworks", required=True, help="Path to framework-to-control mapping YAML file.")
    parser.add_argument("--framework", required=True, help="Framework selector: ALL or comma-separated framework names.")
    parser.add_argument("--output", required=True, help="Path to output JSON results file.")
    args = parser.parse_args()

    if not Path(args.plan).exists():
        raise FileNotFoundError(f"Terraform plan JSON not found: {args.plan}")

    selected_frameworks = normalize_frameworks(args.framework)

    with open(args.controls, "r", encoding="utf-8") as file:
        controls_catalog = yaml.safe_load(file)["controls"]

    with open(args.frameworks, "r", encoding="utf-8") as file:
        frameworks_map = yaml.safe_load(file)["frameworks"]

    related_by_control = build_related_frameworks(frameworks_map)

    results = []
    framework_summary = defaultdict(lambda: {"achieved_score": 0, "total_score": 0, "passed": 0, "failed": 0})
    severity_summary = defaultdict(lambda: {"achieved_score": 0, "total_score": 0, "passed": 0, "failed": 0})

    total_score = 0
    achieved_score = 0

    for framework in selected_frameworks:
        for item in frameworks_map.get(framework, []):
            control_id = item["control"]
            control = controls_catalog[control_id]
            severity = item["severity"].upper()
            score = int(item.get("score", POINTS[severity]))
            passed = run_opa(args.plan, control["check"])

            total_score += score
            framework_summary[framework]["total_score"] += score
            severity_summary[severity]["total_score"] += score

            if passed:
                achieved_score += score
                framework_summary[framework]["achieved_score"] += score
                framework_summary[framework]["passed"] += 1
                severity_summary[severity]["achieved_score"] += score
                severity_summary[severity]["passed"] += 1
            else:
                framework_summary[framework]["failed"] += 1
                severity_summary[severity]["failed"] += 1

            results.append({
                "id": item["id"],
                "framework": framework,
                "control": control_id,
                "related_frameworks": related_by_control.get(control_id, []),
                "severity": severity,
                "score": score,
                "requirement": item.get("requirement", control["title"]),
                "title": control["title"],
                "description": control.get("description", ""),
                "check": control["check"],
                "passed": passed,
                "status": "PASS" if passed else "FAIL",
            })

    for summary in framework_summary.values():
        summary["score_percent"] = round((summary["achieved_score"] / summary["total_score"]) * 100, 2) if summary["total_score"] else 0

    for summary in severity_summary.values():
        summary["score_percent"] = round((summary["achieved_score"] / summary["total_score"]) * 100, 2) if summary["total_score"] else 0

    output = {
        "selected_frameworks": selected_frameworks,
        "total_controls": len(results),
        "achieved_score": achieved_score,
        "total_score": total_score,
        "final_score_percent": round((achieved_score / total_score) * 100, 2) if total_score else 0,
        "framework_summary": dict(sorted(framework_summary.items())),
        "severity_summary": dict(sorted(severity_summary.items())),
        "results": sorted(results, key=lambda item: (item["framework"], item["id"])),
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as file:
        json.dump(output, file, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
