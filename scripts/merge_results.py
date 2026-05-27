#!/usr/bin/env python3
import argparse
import json
from collections import defaultdict
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge individual framework JSON results into one consolidated result file.")
    parser.add_argument("--input-dir", required=True, help="Directory containing results-*.json files.")
    parser.add_argument("--output", required=True, help="Path to consolidated output JSON file.")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    result_files = sorted(
        path for path in input_dir.glob("results-*.json")
        if path.name != Path(args.output).name and path.name != "results-all-frameworks.json"
    )

    all_results = []
    selected_frameworks = []
    framework_summary = defaultdict(lambda: {"achieved_score": 0, "total_score": 0, "passed": 0, "failed": 0})
    severity_summary = defaultdict(lambda: {"achieved_score": 0, "total_score": 0, "passed": 0, "failed": 0})
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
            passed = item["status"] == "PASS"

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

    for summary in framework_summary.values():
        summary["score_percent"] = round((summary["achieved_score"] / summary["total_score"]) * 100, 2) if summary["total_score"] else 0

    for summary in severity_summary.values():
        summary["score_percent"] = round((summary["achieved_score"] / summary["total_score"]) * 100, 2) if summary["total_score"] else 0

    output = {
        "selected_frameworks": sorted(selected_frameworks),
        "total_controls": len(all_results),
        "achieved_score": achieved_score,
        "total_score": total_score,
        "final_score_percent": round((achieved_score / total_score) * 100, 2) if total_score else 0,
        "framework_summary": dict(sorted(framework_summary.items())),
        "severity_summary": dict(sorted(severity_summary.items())),
        "results": sorted(all_results, key=lambda item: (item["framework"], item["id"])),
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as file:
        json.dump(output, file, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
