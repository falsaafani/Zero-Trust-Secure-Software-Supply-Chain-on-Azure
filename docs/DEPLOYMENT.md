# Deployment Guide

This guide provides detailed instructions for deploying the Zero-Trust Secure Software Supply Chain application to Azure Kubernetes Service (AKS).

## Prerequisites

### Required Tools
- Azure CLI (>= 2.50.0)
- Terraform (>= 1.0)
- kubectl (>= 1.28)
- Docker (>= 24.0)
- Git (>= 2.40)

### Azure Resources
- Active Azure subscription
- Sufficient permissions to create resources
- Azure AD tenant access

## Initial Setup

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/zero-trust.git
cd zero-trust
```

### 2. Configure Azure CLI
```bash
az login
az account set --subscription <subscription-id>
```

### 3. Create Terraform Backend Storage
```bash
RESOURCE_GROUP="rg-terraform-state"
STORAGE_ACCOUNT="sttfstatezerotrust"
CONTAINER_NAME="tfstate"
LOCATION="eastus"

az group create --name $RESOURCE_GROUP --location $LOCATION

az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --encryption-services blob

az storage container create \
  --name $CONTAINER_NAME \
  --account-name $STORAGE_ACCOUNT
```

## Infrastructure Deployment

### 1. Configure Terraform Variables
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your specific values:
- Update resource names to be globally unique
- Adjust node counts and VM sizes as needed
- Configure network address spaces

### 2. Initialize Terraform
```bash
terraform init
```

### 3. Plan Infrastructure Changes
```bash
terraform plan -out=tfplan
```

Review the plan carefully to ensure all resources are correct.

### 4. Apply Infrastructure
```bash
terraform apply tfplan
```

This will create:
- Resource Group
- Virtual Network with subnets
- Network Security Groups
- AKS Cluster
- Azure Container Registry
- Azure Key Vault
- Log Analytics Workspace
- Managed Identities

### 5. Retrieve Outputs
```bash
terraform output -json > outputs.json
```

## Application Deployment

### 1. Configure kubectl
```bash
az aks get-credentials \
  --resource-group rg-zero-trust-prod \
  --name aks-zero-trust
```

### 2. Verify Cluster Access
```bash
kubectl cluster-info
kubectl get nodes
```

### 3. Create Namespace
```bash
kubectl create namespace zero-trust
```

### 4. Install Monitoring Stack

#### Install Prometheus
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --values monitoring/prometheus-config.yaml
```

#### Install Grafana Dashboards
```bash
kubectl apply -f monitoring/grafana-dashboards/ -n monitoring
```

### 5. Install Policy Engine

#### Install Kyverno
```bash
helm repo add kyverno https://kyverno.github.io/kyverno/
helm repo update

helm install kyverno kyverno/kyverno \
  --namespace kyverno \
  --create-namespace
```

#### Apply Policies
```bash
kubectl apply -f policies/kyverno-policies.yaml
```

### 6. Configure GitHub Secrets

Set up the following GitHub repository secrets:

```bash
AZURE_CREDENTIALS: Service Principal JSON
ACR_NAME: acrzerotrust
AZURE_RESOURCE_GROUP: rg-zero-trust-prod
AKS_CLUSTER_NAME: aks-zero-trust
```

To create Azure credentials:
```bash
az ad sp create-for-rbac \
  --name "github-actions-zero-trust" \
  --role contributor \
  --scopes /subscriptions/<subscription-id>/resourceGroups/rg-zero-trust-prod \
  --sdk-auth
```

### 7. Deploy Application via CI/CD

Push code to trigger the deployment:
```bash
git add .
git commit -m "Initial deployment"
git push origin main
```

Monitor the GitHub Actions workflow for deployment status.

### 8. Manual Deployment (Alternative)

If needed, deploy manually:

```bash
export ACR_NAME="acrzerotrust"
export APP_NAME="zero-trust-app"
export IMAGE_TAG="v1.0.0"

kubectl apply -f k8s/service-account.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/network-policy.yaml
kubectl apply -f k8s/ingress.yaml
```

## Post-Deployment Verification

### 1. Check Pod Status
```bash
kubectl get pods -n zero-trust
kubectl describe pod <pod-name> -n zero-trust
```

### 2. View Logs
```bash
kubectl logs -f deployment/zero-trust-app -n zero-trust
```

### 3. Test Health Endpoints
```bash
POD_NAME=$(kubectl get pods -n zero-trust -l app=zero-trust-app -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n zero-trust $POD_NAME -- curl http://localhost:8080/health
```

### 4. Access Application
```bash
kubectl get ingress -n zero-trust
```

### 5. View Metrics
```bash
kubectl port-forward -n zero-trust svc/zero-trust-app 8080:80
curl http://localhost:8080/metrics
```

## Rollback Procedure

### Rollback Deployment
```bash
kubectl rollout undo deployment/zero-trust-app -n zero-trust
kubectl rollout status deployment/zero-trust-app -n zero-trust
```

### Rollback to Specific Revision
```bash
kubectl rollout history deployment/zero-trust-app -n zero-trust
kubectl rollout undo deployment/zero-trust-app -n zero-trust --to-revision=<revision-number>
```

## Scaling

### Manual Scaling
```bash
kubectl scale deployment zero-trust-app -n zero-trust --replicas=5
```

### Enable Horizontal Pod Autoscaling
```bash
kubectl autoscale deployment zero-trust-app \
  -n zero-trust \
  --cpu-percent=70 \
  --min=3 \
  --max=10
```

## Cleanup

### Delete Application
```bash
kubectl delete namespace zero-trust
```

### Destroy Infrastructure
```bash
cd terraform
terraform destroy
```

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and solutions.

## Security Considerations

- All secrets stored in Azure Key Vault
- Network policies enforce zero-trust
- Pod security standards enforced via Kyverno
- TLS termination at ingress
- Container images scanned for vulnerabilities
- Regular security updates via automated CI/CD

## Support

For issues or questions, please open an issue in the GitHub repository or contact the platform team.
