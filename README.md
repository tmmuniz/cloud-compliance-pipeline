# Cloud Compliance Pipeline for AWS Terraform

This repository is a portfolio-ready **Compliance-as-Code** project for AWS infrastructure defined with Terraform.

The pipeline evaluates a Terraform plan against multiple cybersecurity and regulatory frameworks using a single reusable OPA/Rego policy engine.

## Supported frameworks

- GDPR
- NIST CSF
- CIS Controls
- ISO 27001
- PCI DSS
- SOC 2
- MITRE ATT&CK
- LGPD
- BACEN
- Open Finance

Each framework has **30 controls**:

- 10 HIGH controls, worth 5 points each
- 10 MEDIUM controls, worth 3 points each
- 10 LOW controls, worth 1 point each

Total per framework: **90 points**.

## Current portfolio scope

This project is focused on **detecting compliance gaps in the Terraform plan**.

It does **not** deploy infrastructure, does **not** require AWS credentials, and does **not** use a remote Terraform state bucket.

The AWS provider is configured in demo mode with mock credentials and validation skips so GitHub Actions can generate a local plan and audit it safely.

## Architecture

```text
GitHub Actions workflow_dispatch
  ↓
One independent job per framework
  ↓
Terraform init without backend
  ↓
Terraform plan generated locally with -refresh=false
  ↓
terraform show -json
  ↓
OPA/Rego compliance evaluation
  ↓
HTML compliance report per framework
  ↓
Plan files removed from the runner
```

## Why the plan is generated in the runner

The Terraform plan JSON may contain sensitive infrastructure details. For this reason, this project does **not** require the user to commit, upload, or store `tfplan.json` in GitHub Secrets.

The file is generated temporarily during the pipeline execution and removed before the job finishes.

## Required GitHub Actions inputs

When running the workflow manually, provide:

| Input | Description | Example |
|---|---|---|
| `FRAMEWORK` | Framework to execute. Use `ALL` for all frameworks. | `ALL` |
| `AWS_REGION` | AWS region used only to render the local Terraform plan. | `us-east-1` |

Examples for `FRAMEWORK`:

```text
ALL
LGPD
ISO27001
LGPD,ISO27001,NIST_CSF
OPEN_FINANCE,BACEN
```

## Workflow behavior

The workflow has one job per framework:

- `GDPR`
- `NIST_CSF`
- `CIS`
- `ISO27001`
- `PCI_DSS`
- `SOC2`
- `MITRE`
- `LGPD`
- `BACEN`
- `OPEN_FINANCE`

If a compliance control fails, the pipeline **does not stop**. The failed control is recorded in the JSON and HTML reports as `FAIL`.

This separates pipeline execution errors from compliance findings:

- Syntax/runtime error: pipeline failure
- Compliance gap: pipeline succeeds and report shows `FAIL`

## Project structure

```text
cloud-compliance-pipeline/
├── .github/workflows/compliance.yml
├── terraform/
│   ├── providers.tf
│   ├── variables.tf
│   ├── main.tf
│   ├── network.tf
│   ├── iam.tf
│   ├── s3.tf
│   ├── compute.tf
│   └── security_services.tf
├── policy/
│   ├── compliance.rego
│   └── controls.yaml
├── scripts/
│   ├── evaluate.py
│   └── render_html.py
├── reports/
│   └── .gitkeep
├── requirements.txt
├── .gitignore
└── README.md
```

## Local execution

```bash
cd terraform
terraform init -backend=false
terraform validate
terraform plan -refresh=false -out=tfplan
terraform show -json tfplan > ../tfplan.json
cd ..
python3 scripts/evaluate.py   --plan tfplan.json   --controls policy/controls.yaml   --framework ALL   --output reports/results.json
python3 scripts/render_html.py   --input reports/results.json   --output reports/compliance-report.html
```

## Portfolio positioning

This project demonstrates:

- Cloud Security
- GRC Engineering
- DevSecOps
- Compliance-as-Code
- Policy-as-Code
- Terraform plan analysis
- OPA/Rego
- AWS security controls
- GitHub Actions automation
- Multi-framework control mapping

Suggested LinkedIn/GitHub description:

> Compliance-as-Code pipeline for AWS Terraform plans using OPA/Rego, GitHub Actions, and multi-framework control mapping across GDPR, LGPD, NIST CSF, CIS Controls, ISO 27001, PCI DSS, SOC 2, MITRE ATT&CK, BACEN, and Open Finance.
