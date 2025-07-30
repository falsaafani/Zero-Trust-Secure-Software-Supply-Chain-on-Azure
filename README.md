# Zero-Trust Secure Software Supply Chain on Azure

This project demonstrates a secure CI/CD pipeline using GitHub Actions to deploy a containerized Python Flask application to Azure Kubernetes Service (AKS) with a Zero-Trust security model.

## Architecture
https://github.com/falsaafani/Zero-Trust-Secure-Software-Supply-Chain-on-Azure/blob/main/zero_trust_architecture.png

## Why Zero-Trust?
- No Implicit Trust: Every stage of the pipeline is validated.
- Shift-Left Security: Gitleaks, Checkov, and Trivy catch issues early.
- Runtime Protection: Kyverno enforces policies like non-root containers and trusted registries.

## Setup Instructions
1. Create Azure Resources:
   - Run `terraform apply` in the `terraform/` directory.
   - Note the ACR login server and AKS cluster name from outputs.
2. Set GitHub Secrets:
   - Add `AZURE_CREDENTIALS` and `ACR_NAME` in GitHub repository secrets.
3. Install Kyverno:
   - Apply `policies/kyverno-policies.yaml` to the AKS cluster.
4. Run CI/CD:
   - Push code to trigger `ci.yml` and `deploy.yml` workflows.

## Security Controls
- Gitleaks: Scans for hardcoded secrets.
- Checkov: Validates Terraform configurations.
- Trivy: Scans container images for CVEs.
- Kyverno: Enforces runtime policies (non-root containers, trusted ACR).
