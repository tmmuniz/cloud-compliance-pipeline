#!/usr/bin/env python3
import argparse
import json
from collections import defaultdict
from pathlib import Path


def default_summary() -> dict:
    return {
        "achieved_score": 0,
        "total_score": 0,
        "total_controls": 0,
        "passed": 0,
        "failed": 0,
        "opa_error": 0,
        "undefined": 0,
    }


def update_summary(summary: dict, score: int, status: str) -> None:
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


def finalize_summary(summary: dict) -> dict:
    summary["score_percent"] = round((summary["achieved_score"] / summary["total_score"]) * 100, 2) if summary["total_score"] else 0
    summary["non_passed"] = summary["failed"] + summary["opa_error"] + summary["undefined"]
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge individual framework JSON results into one consolidated result file.")
    parser.add_argument("--input-dir", required=True, help="Directory containing results-*.json files.")
    parser.add_argument("--output", required=True, help="Path to consolidated output JSON file.")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_name = Path(args.output).name
    result_files = sorted(
        path for path in input_dir.glob("results-*.json")
        if path.name not in {output_name, "results-all-frameworks.json"}
    )

    all_results = []
    selected_frameworks = []
    framework_summary = defaultdict(default_summary)
    severity_summary = defaultdict(default_summary)
    achieved_score = 0
    total_score = 0

    for result_file in result_files:
        with open(result_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        for framework in data.get("selected_frameworks", []):
            if framework not in selected_frameworks:
                selected_frameworks.append(framework)

        for item in data.get("results", []):
            all_results.append(item)
            severity = item["severity"]
            framework = item["framework"]
            score = int(item["score"])
            status = item.get("status", "PASS" if item.get("passed") else "FAIL")

            total_score += score
            update_summary(framework_summary[framework], score, status)
            update_summary(severity_summary[severity], score, status)

            if status == "PASS":
                achieved_score += score

    output = {
        "selected_frameworks": sorted(selected_frameworks),
        "total_controls": len(all_results),
        "achieved_score": achieved_score,
        "total_score": total_score,
        "final_score_percent": round((achieved_score / total_score) * 100, 2) if total_score else 0,
        "framework_summary": {key: finalize_summary(value) for key, value in sorted(framework_summary.items())},
        "severity_summary": {key: finalize_summary(value) for key, value in sorted(severity_summary.items())},
        "results": sorted(all_results, key=lambda item: (item["framework"], item["id"])),
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as file:
        json.dump(output, file, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
