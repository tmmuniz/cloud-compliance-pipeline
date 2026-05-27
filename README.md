# Cloud Compliance Pipeline for AWS Terraform

Portfolio project for **Cloud Security**, **GRC**, **DevSecOps**, **Policy-as-Code**, and **Compliance-as-Code**.

The pipeline audits AWS Terraform code using a single reusable OPA/Rego policy engine and maps the same technical checks to multiple compliance and cybersecurity frameworks.

## Supported frameworks

International frameworks:

- GDPR
- NIST_CSF
- CIS
- ISO27001
- PCI_DSS
- SOC2
- MITRE

Brazilian frameworks:

- LGPD
- BACEN

Each framework contains 15 mapped audit items:

- 5 HIGH items, worth 5 points each
- 5 MEDIUM items, worth 3 points each
- 5 LOW items, worth 1 point each

## Architecture

```text
User-provided Terraform plan JSON input
      ↓
OPA/Rego reusable checks
      ↓
Framework control mapping
      ↓
JSON + HTML compliance report
```

## How the user provides the Terraform plan JSON

The user provides the Terraform plan JSON directly in the GitHub Actions workflow input named `TFPLAN_JSON`.

This means the Terraform code can be created, edited, or generated outside this repository, including from an AWS-based environment. The pipeline receives only the generated `tfplan.json` content and audits it with OPA/Rego.

Example local command to generate the JSON before pasting it into the workflow input:

```bash
terraform init
terraform plan -out=tfplan
terraform show -json tfplan > tfplan.json
```

Then paste the full content of `tfplan.json` into the workflow input `TFPLAN_JSON`.

## How to run in GitHub Actions

1. Upload this project to a GitHub repository.
2. Add or replace the AWS Terraform code inside the `terraform/` directory.
3. Go to **Actions**.
4. Select **Cloud Compliance Pipeline**.
5. Click **Run workflow**.
6. In `FRAMEWORK`, choose `ALL` or one or more frameworks separated by comma.
7. In `TFPLAN_JSON`, paste the full Terraform plan JSON content.
8. Download the generated HTML report from the workflow artifacts.

## Example `FRAMEWORK` input

Run all frameworks:

```text
ALL
```

Run only Brazilian and ISO/NIST frameworks:

```text
LGPD,BACEN,ISO27001,NIST_CSF
```

## Main files

```text
.github/workflows/compliance.yml   GitHub Actions pipeline
policy/compliance.rego             Single reusable OPA policy file
policy/controls.yaml               Framework-to-control mapping
scripts/evaluate.py                OPA evaluator and scoring engine
scripts/render_html.py             HTML report generator
terraform/                         Optional sample AWS Terraform code
reports/                           Generated reports
```

## DRY design

The project avoids one Rego file per framework.

Instead, it uses:

- one generic Rego policy file;
- one YAML framework mapping file;
- one Python evaluator;
- one HTML report generator.

This means the same reusable check, such as `s3_encrypted`, can support GDPR, LGPD, ISO 27001, PCI DSS, SOC 2, BACEN, and other frameworks.

## Scoring model

| Severity | Points |
|---|---:|
| HIGH | 5 |
| MEDIUM | 3 |
| LOW | 1 |

The final score is calculated only against the selected frameworks.

```text
final_score = achieved_points / total_possible_points * 100
```

## Report output

The final report is generated at:

```text
reports/compliance-report.html
```

The report includes:

- selected frameworks;
- final percentage score;
- achieved points;
- total possible points;
- reusable control summary;
- related frameworks per reusable check;
- detailed PASS/FAIL result for each framework item.

## Local execution

Install dependencies:

```bash
pip install -r requirements.txt
```

Install OPA:

```bash
curl -L -o opa https://openpolicyagent.org/downloads/latest/opa_linux_amd64_static
chmod +x opa
sudo mv opa /usr/local/bin/opa
```

Generate a Terraform plan JSON locally:

```bash
cd terraform
terraform init
terraform plan -out=tfplan
terraform show -json tfplan > ../tfplan.json
cd ..
```

Run the compliance evaluation:

```bash
python scripts/evaluate.py \
  --plan tfplan.json \
  --controls policy/controls.yaml \
  --rego policy/compliance.rego \
  --framework "LGPD,ISO27001,NIST_CSF" \
  --output reports/results.json
```

Generate the HTML report:

```bash
python scripts/render_html.py \
  --input reports/results.json \
  --output reports/compliance-report.html
```

## Portfolio positioning

Suggested description:

> A reusable compliance-as-code pipeline that evaluates AWS Terraform infrastructure against multiple regulatory and cybersecurity frameworks using a single DRY OPA/Rego policy engine and framework-specific control mappings.

## Important note

This project is designed for portfolio, educational, and architecture demonstration purposes. The framework mappings are simplified technical mappings and should not be treated as a formal legal, regulatory, or audit certification opinion.


## GitHub Actions inputs

| Input | Description | Example |
|---|---|---|
| `FRAMEWORK` | Framework selection. Use `ALL` or a comma-separated list. | `ALL` |
| `TFPLAN_JSON` | Full Terraform plan JSON content to audit. | `{ "format_version": "..." }` |

All project-level input variables used by the workflow are written in uppercase.
