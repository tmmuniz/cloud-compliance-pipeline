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

NON_COMPLIANT_STATUSES = {"FAIL", "UNDEFINED", "OPA_ERROR"}


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
    """Run a single OPA/Rego check and return a structured result.

    PASS means the Rego rule explicitly evaluated to true.
    FAIL means the rule was evaluated but did not return true, usually because the
    Terraform plan does not satisfy the control.
    OPA_ERROR means OPA could not parse/evaluate the policy or input.
    UNDEFINED means OPA returned a value, but it was not a boolean.
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
        print(f"OPA evaluation error for check '{check}': {message}", file=sys.stderr)
        return {
            "status": "OPA_ERROR",
            "passed": False,
            "message": message,
            "opa_returncode": completed.returncode,
        }

    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return {
            "status": "OPA_ERROR",
            "passed": False,
            "message": f"Invalid JSON returned by OPA: {exc}",
            "opa_returncode": completed.returncode,
        }

    result = data.get("result", [])

    # For boolean-style Rego rules, an empty result means the rule was undefined.
    # In a compliance context this means the control did not pass, not that OPA failed.
    if not result:
        return {
            "status": "FAIL",
            "passed": False,
            "message": "Rule did not evaluate to true for this Terraform plan.",
            "opa_returncode": completed.returncode,
        }

    try:
        value = result[0]["expressions"][0]["value"]
    except (KeyError, IndexError, TypeError):
        return {
            "status": "UNDEFINED",
            "passed": False,
            "message": "OPA result did not include a boolean expression value.",
            "opa_returncode": completed.returncode,
        }

    if value is True:
        return {
            "status": "PASS",
            "passed": True,
            "message": "Rule evaluated to true.",
            "opa_returncode": completed.returncode,
        }

    if value is False:
        return {
            "status": "FAIL",
            "passed": False,
            "message": "Rule evaluated to false.",
            "opa_returncode": completed.returncode,
        }

    return {
        "status": "UNDEFINED",
        "passed": False,
        "message": f"OPA returned a non-boolean value: {value!r}",
        "opa_returncode": completed.returncode,
    }


def build_related_frameworks(frameworks_map: dict) -> dict[str, list[str]]:
    related = defaultdict(set)
    for framework, items in frameworks_map.items():
        for item in items:
            related[item["control"]].add(framework)
    return {control: sorted(frameworks) for control, frameworks in related.items()}


def update_summary(summary: dict, severity: str, score: int, status: str) -> None:
    summary["total_score"] += score
    summary["total_controls"] += 1

    if status == "PASS":
        summary["achieved_score"] += score
        summary["passed"] += 1
    elif status == "OPA_ERROR":
        summary["opa_error"] += 1
    elif status == "UNDEFINED":
        summary["undefined"] += 1
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
        "opa_error": 0,
        "undefined": 0,
        "by_severity": defaultdict(lambda: {"total": 0, "pass": 0, "fail": 0, "opa_error": 0, "undefined": 0}),
    }


def finalize_summary(summary: dict) -> dict:
    summary["score_percent"] = round((summary["achieved_score"] / summary["total_score"]) * 100, 2) if summary["total_score"] else 0
    summary["non_passed"] = summary["failed"] + summary["opa_error"] + summary["undefined"]
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

    related_by_control = build_related_frameworks(frameworks_map)

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
                "related_frameworks": related_by_control.get(control_id, []),
                "severity": severity,
                "score": score,
                "requirement": item.get("requirement", control["title"]),
                "title": control["title"],
                "description": control.get("description", ""),
                "check": control["check"],
                "passed": passed,
                "status": status,
                "message": evaluation.get("message", ""),
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
