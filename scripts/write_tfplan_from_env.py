#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Create tfplan.json from a GitHub Actions environment variable.")
    parser.add_argument("--env-var", default="TFPLAN_JSON", help="Environment variable containing Terraform plan JSON.")
    parser.add_argument("--output", default="tfplan.json", help="Output path for tfplan.json.")
    args = parser.parse_args()

    raw_value = os.environ.get(args.env_var, "").strip()
    if not raw_value:
        raise ValueError(f"Environment variable {args.env_var} is empty.")

    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Environment variable {args.env_var} does not contain valid JSON: {exc}") from exc

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(parsed, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
