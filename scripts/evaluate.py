#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

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


def run_opa(plan_path: str, check: str) -> dict[str, Any]:
    """Run a single OPA/Rego check and return a simplified PASS/FAIL result.

    The HTML report intentionally exposes only PASS and FAIL to keep the output
    focused on audit results instead of internal evaluator states. Execution
    errors are logged to stderr and treated as FAIL.
    """
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
        message = completed.stderr.strip() or completed.stdout.strip() or "OPA evaluation failed without output."
        print(f"Policy evaluation error for check '{check}': {message}", file=sys.stderr)
        return {"status": "FAIL", "passed": False}

    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON returned by OPA for check '{check}': {exc}", file=sys.stderr)
        return {"status": "FAIL", "passed": False}

    result = data.get("result", [])
    if not result:
        return {"status": "FAIL", "passed": False}

    try:
        value = result[0]["expressions"][0]["value"]
    except (KeyError, IndexError, TypeError):
        return {"status": "FAIL", "passed": False}

    if value is True:
        return {"status": "PASS", "passed": True}

    return {"status": "FAIL", "passed": False}


def update_summary(summary: dict, severity: str, score: int, status: str) -> None:
    summary["total_score"] += score
    summary["total_controls"] += 1

    if status == "PASS":
        summary["achieved_score"] += score
        summary["passed"] += 1
    else:
        summary["failed"] += 1

    summary["by_severity"][severity]["total"] += 1
    summary["by_severity"][severity][status.lower()] += 1


def default_summary() -> dict:
    return {
        "achieved_score": 0,
        "total_score": 0,
        "total_controls": 0,
        "passed": 0,
        "failed": 0,
        "by_severity": defaultdict(lambda: {"total": 0, "pass": 0, "fail": 0}),
    }


def finalize_summary(summary: dict) -> dict:
    summary["score_percent"] = round((summary["achieved_score"] / summary["total_score"]) * 100, 2) if summary["total_score"] else 0
    summary["non_passed"] = summary["failed"]
    summary["by_severity"] = {key: dict(value) for key, value in sorted(summary["by_severity"].items())}
    return summary


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

    results = []
    framework_summary = defaultdict(default_summary)
    severity_summary = defaultdict(default_summary)

    total_score = 0
    achieved_score = 0

    for framework in selected_frameworks:
        for item in frameworks_map.get(framework, []):
            control_id = item["control"]
            if control_id not in controls_catalog:
                raise KeyError(f"Control '{control_id}' mapped in frameworks.yaml was not found in controls.yaml.")

            control = controls_catalog[control_id]
            severity = item["severity"].upper()
            score = int(item.get("score", POINTS[severity]))
            evaluation = run_opa(args.plan, control["check"])
            status = evaluation["status"]
            passed = evaluation["passed"]

            total_score += score
            if passed:
                achieved_score += score

            update_summary(framework_summary[framework], severity, score, status)
            update_summary(severity_summary[severity], severity, score, status)

            results.append({
                "id": item["id"],
                "framework": framework,
                "domain": item.get("domain", "General"),
                "control": control_id,
                "severity": severity,
                "score": score,
                "requirement": item.get("requirement", control["title"]),
                "title": control["title"],
                "description": control.get("description", ""),
                "check": control["check"],
                "passed": passed,
                "status": status,
            })

    output = {
        "selected_frameworks": selected_frameworks,
        "total_controls": len(results),
        "achieved_score": achieved_score,
        "total_score": total_score,
        "final_score_percent": round((achieved_score / total_score) * 100, 2) if total_score else 0,
        "framework_summary": {key: finalize_summary(value) for key, value in sorted(framework_summary.items())},
        "severity_summary": {key: finalize_summary(value) for key, value in sorted(severity_summary.items())},
        "results": results,
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as file:
        json.dump(output, file, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
