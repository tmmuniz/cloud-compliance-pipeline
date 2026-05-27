# Cloud Compliance Pipeline for AWS Terraform

This repository is a portfolio-ready **Compliance-as-Code** project for AWS infrastructure defined with Terraform.

The pipeline evaluates a Terraform plan against multiple cybersecurity and regulatory frameworks using a single reusable OPA/Rego policy engine and a framework-to-control mapping file.

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

The workflow authenticates to AWS using **GitHub Actions OIDC** only to initialize Terraform and generate the plan. The pipeline does **not** run `terraform apply` and does **not** deploy infrastructure.

The Terraform state backend uses an S3 bucket provided at workflow runtime through the `TERRAFORM_STATE_BUCKET` input.

## Architecture

```text
GitHub Actions workflow_dispatch
  ↓
Single job: compliance_pipeline
  ↓
AWS authentication through OIDC using ARN_OIDC
  ↓
Terraform init using S3 backend bucket from TERRAFORM_STATE_BUCKET
  ↓
Terraform validate
  ↓
Terraform plan generated in the runner
  ↓
terraform show -json
  ↓
One step/task per framework
  ↓
OPA/Rego compliance evaluation
  ↓
One consolidated HTML report for all selected frameworks
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
| `AWS_REGION` | AWS region used by Terraform. | `us-east-1` |
| `TERRAFORM_STATE_BUCKET` | S3 bucket name used to store the Terraform state file. | `my-terraform-state-bucket` |
| `ARN_OIDC` | AWS IAM Role ARN assumed by GitHub Actions through OIDC. | `arn:aws:iam::123456789012:role/github-actions-oidc-role` |

Examples for `FRAMEWORK`:

```text
ALL
LGPD
ISO27001
LGPD,ISO27001,NIST_CSF
OPEN_FINANCE,BACEN
```

## Workflow behavior

The workflow uses a **single job** with one independent task/step per framework:

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

Terraform, Python, OPA and the Terraform plan are prepared only once. Each framework step reads the same `tfplan.json`.

If a compliance control fails, the workflow **does not stop**. The failed control is recorded in the JSON and HTML reports as `FAIL`.

This separates pipeline execution errors from compliance findings:

- Syntax/runtime error: pipeline failure
- Compliance gap: pipeline succeeds and report shows `FAIL`

## Consolidated report

The workflow generates a single final HTML report:

```text
reports/cloud-compliance-report.html
```

The report includes:

- selected frameworks;
- total score;
- score by framework;
- detailed result per control;
- related frameworks;
- PASS/FAIL status for each item.

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
│   ├── merge_results.py
│   └── render_html.py
├── reports/
│   └── .gitkeep
├── requirements.txt
├── .gitignore
└── README.md
```

## Local execution

For local testing without remote backend:

```bash
cd terraform
terraform init -backend=false
terraform validate
terraform plan -refresh=false -out=tfplan
terraform show -json tfplan > ../tfplan.json
cd ..
python3 scripts/evaluate.py --plan tfplan.json --controls policy/controls.yaml --framework ALL --output reports/results.json
python3 scripts/render_html.py --input reports/results.json --output reports/cloud-compliance-report.html
rm -f terraform/tfplan tfplan.json
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
- GitHub Actions OIDC
- Secure Terraform plan handling
- Multi-framework control mapping

Suggested LinkedIn/GitHub description:

> Compliance-as-Code pipeline for AWS Terraform plans using OPA/Rego, GitHub Actions OIDC, and multi-framework control mapping across GDPR, LGPD, NIST CSF, CIS Controls, ISO 27001, PCI DSS, SOC 2, MITRE ATT&CK, BACEN, and Open Finance.


## Policy data model

The project separates the technical control catalog from framework mappings:

```text
policy/
├── controls.yaml      # Reusable technical controls and the OPA/Rego check name
├── frameworks.yaml    # Framework-specific items mapped to technical controls
└── compliance.rego    # Single DRY Rego policy package
```

`controls.yaml` defines one technical control only once. `frameworks.yaml` maps each framework item to a reusable control ID. The HTML report uses this relationship to show which frameworks are related to the same technical control.

Example:

```yaml
# controls.yaml
controls:
  S3_ENCRYPTED:
    title: S3 Encrypted
    check: s3_encrypted

# frameworks.yaml
frameworks:
  LGPD:
    - id: LGPD-H01
      control: S3_ENCRYPTED
      severity: HIGH
      score: 5
  GDPR:
    - id: GDPR-H01
      control: S3_ENCRYPTED
      severity: HIGH
      score: 5
```

The consolidated HTML report then lists `S3_ENCRYPTED` as one technical control related to both LGPD and GDPR.
