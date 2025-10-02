# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the Zero-Trust Secure Software Supply Chain application.

## Table of Contents
1. [Application Issues](#application-issues)
2. [Infrastructure Issues](#infrastructure-issues)
3. [Deployment Issues](#deployment-issues)
4. [Networking Issues](#networking-issues)
5. [Security Issues](#security-issues)
6. [Monitoring Issues](#monitoring-issues)

## Application Issues

### Pods Not Starting

**Symptoms:**
- Pods stuck in `Pending`, `CrashLoopBackOff`, or `ImagePullBackOff` state

**Diagnosis:**
```bash
kubectl get pods -n zero-trust
kubectl describe pod <pod-name> -n zero-trust
kubectl logs <pod-name> -n zero-trust
```

**Common Causes & Solutions:**

1. **Image Pull Errors**
   ```bash
   kubectl get events -n zero-trust --sort-by='.lastTimestamp'

   az acr login --name acrzerotrust
   kubectl delete pod <pod-name> -n zero-trust
   ```

2. **Resource Constraints**
   ```bash
   kubectl top nodes
   kubectl describe nodes

   kubectl scale deployment zero-trust-app -n zero-trust --replicas=2
   ```

3. **Failed Health Checks**
   ```bash
   kubectl logs <pod-name> -n zero-trust

   kubectl edit deployment zero-trust-app -n zero-trust
   ```

### High Memory Usage

**Symptoms:**
- Pods being OOMKilled
- High memory consumption

**Diagnosis:**
```bash
kubectl top pods -n zero-trust
kubectl describe pod <pod-name> -n zero-trust | grep -A 5 "Limits"
```

**Solutions:**
```bash
kubectl edit deployment zero-trust-app -n zero-trust

resources:
  limits:
    memory: "1Gi"
  requests:
    memory: "256Mi"
```

### Application Errors

**Symptoms:**
- 500 errors in application
- Unexpected behavior

**Diagnosis:**
```bash
kubectl logs -f deployment/zero-trust-app -n zero-trust
kubectl exec -it <pod-name> -n zero-trust -- /bin/sh
```

**Solutions:**
1. Check application logs for stack traces
2. Verify environment variables
3. Test health endpoints
4. Review Prometheus metrics

## Infrastructure Issues

### AKS Cluster Not Accessible

**Symptoms:**
- Cannot connect to cluster
- kubectl commands timeout

**Diagnosis:**
```bash
az aks show --resource-group rg-zero-trust-prod --name aks-zero-trust
kubectl cluster-info
```

**Solutions:**
```bash
az aks get-credentials \
  --resource-group rg-zero-trust-prod \
  --name aks-zero-trust \
  --overwrite-existing

az aks check-acr \
  --resource-group rg-zero-trust-prod \
  --name aks-zero-trust \
  --acr acrzerotrust.azurecr.io
```

### Node Issues

**Symptoms:**
- Nodes in NotReady state
- Resource exhaustion

**Diagnosis:**
```bash
kubectl get nodes
kubectl describe node <node-name>
kubectl top nodes
```

**Solutions:**
```bash
az aks nodepool scale \
  --resource-group rg-zero-trust-prod \
  --cluster-name aks-zero-trust \
  --name default \
  --node-count 5

az aks nodepool update \
  --resource-group rg-zero-trust-prod \
  --cluster-name aks-zero-trust \
  --name default \
  --enable-cluster-autoscaler \
  --min-count 2 \
  --max-count 5
```

### Terraform State Issues

**Symptoms:**
- Terraform state lock
- State drift

**Diagnosis:**
```bash
terraform show
terraform state list
```

**Solutions:**
```bash
terraform force-unlock <lock-id>

terraform refresh

terraform import azurerm_resource_group.main /subscriptions/<sub-id>/resourceGroups/rg-zero-trust-prod
```

## Deployment Issues

### CI/CD Pipeline Failures

**Symptoms:**
- GitHub Actions workflow fails
- Security scans block deployment

**Diagnosis:**
1. Review GitHub Actions logs
2. Check security scan reports
3. Verify secrets configuration

**Solutions:**

1. **Gitleaks Failures**
   ```bash
   docker run --rm -v $(pwd):/repo zricethezav/gitleaks:latest detect --source /repo
   git filter-branch --tree-filter 'rm -f secrets.txt' HEAD
   ```

2. **Checkov Failures**
   ```bash
   checkov -d terraform/ --framework terraform
   ```

3. **Trivy Failures**
   ```bash
   docker build -t test-image:latest ./App
   trivy image test-image:latest
   ```

### Failed Deployments

**Symptoms:**
- Deployment rollout stuck
- New pods not starting

**Diagnosis:**
```bash
kubectl rollout status deployment/zero-trust-app -n zero-trust
kubectl get events -n zero-trust --sort-by='.lastTimestamp'
```

**Solutions:**
```bash
kubectl rollout undo deployment/zero-trust-app -n zero-trust

kubectl rollout restart deployment/zero-trust-app -n zero-trust

kubectl delete pod -l app=zero-trust-app -n zero-trust
```

## Networking Issues

### Ingress Not Working

**Symptoms:**
- Cannot access application via ingress
- 502/503 errors

**Diagnosis:**
```bash
kubectl get ingress -n zero-trust
kubectl describe ingress zero-trust-app -n zero-trust
kubectl get svc -n ingress-nginx
```

**Solutions:**
```bash
helm upgrade ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --set controller.service.loadBalancerIP=<static-ip>

kubectl apply -f k8s/ingress.yaml
```

### Network Policy Blocking Traffic

**Symptoms:**
- Pods cannot communicate
- Services unreachable

**Diagnosis:**
```bash
kubectl get networkpolicies -n zero-trust
kubectl describe networkpolicy zero-trust-app-network-policy -n zero-trust
```

**Solutions:**
```bash
kubectl delete networkpolicy default-deny-all -n zero-trust

kubectl apply -f k8s/network-policy.yaml
```

### DNS Resolution Issues

**Symptoms:**
- Cannot resolve service names
- External DNS failures

**Diagnosis:**
```bash
kubectl run -it --rm debug --image=busybox --restart=Never -n zero-trust -- nslookup kubernetes.default

kubectl get pods -n kube-system -l k8s-app=kube-dns
```

**Solutions:**
```bash
kubectl rollout restart deployment/coredns -n kube-system
```

## Security Issues

### Failed Security Scans

**Symptoms:**
- Kyverno policy violations
- Container vulnerabilities

**Diagnosis:**
```bash
kubectl get policyreport -n zero-trust
kubectl describe policyreport -n zero-trust

trivy image <image-name>
```

**Solutions:**
```bash
kubectl annotate pod <pod-name> -n zero-trust policies.kyverno.io/skip="require-non-root-user"

docker build --no-cache -t <image-name> ./App
```

### Authentication Issues

**Symptoms:**
- Cannot authenticate to ACR
- RBAC permission denied

**Diagnosis:**
```bash
az acr check-health --name acrzerotrust

kubectl auth can-i create pods --namespace zero-trust
```

**Solutions:**
```bash
az role assignment create \
  --assignee <object-id> \
  --role AcrPull \
  --scope /subscriptions/<sub-id>/resourceGroups/rg-zero-trust-prod/providers/Microsoft.ContainerRegistry/registries/acrzerotrust

kubectl create rolebinding <binding-name> \
  --clusterrole=<role> \
  --serviceaccount=zero-trust:zero-trust-app \
  --namespace=zero-trust
```

## Monitoring Issues

### Prometheus Not Scraping Metrics

**Symptoms:**
- No metrics in Prometheus
- Empty graphs in Grafana

**Diagnosis:**
```bash
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090

kubectl get servicemonitor -n zero-trust
```

**Solutions:**
```bash
kubectl apply -f monitoring/prometheus-config.yaml

kubectl label namespace zero-trust monitoring=enabled

kubectl annotate pod <pod-name> -n zero-trust \
  prometheus.io/scrape=true \
  prometheus.io/port=8080 \
  prometheus.io/path=/metrics
```

### Grafana Dashboard Issues

**Symptoms:**
- Dashboards not loading
- No data displayed

**Diagnosis:**
```bash
kubectl logs -n monitoring deployment/grafana
kubectl port-forward -n monitoring svc/grafana 3000:80
```

**Solutions:**
1. Verify Prometheus data source configuration
2. Check dashboard JSON syntax
3. Ensure correct PromQL queries

### Alerts Not Firing

**Symptoms:**
- Expected alerts not triggering
- Alertmanager not receiving alerts

**Diagnosis:**
```bash
kubectl logs -n monitoring deployment/alertmanager
kubectl port-forward -n monitoring svc/alertmanager 9093:9093
```

**Solutions:**
```bash
kubectl apply -f monitoring/alerts.yaml

kubectl rollout restart deployment/prometheus -n monitoring
```

## Common Commands

### View All Resources
```bash
kubectl get all -n zero-trust
kubectl get events -n zero-trust --sort-by='.lastTimestamp'
```

### Debug Pod
```bash
kubectl exec -it <pod-name> -n zero-trust -- /bin/sh
kubectl debug <pod-name> -n zero-trust -it --image=busybox
```

### View Logs
```bash
kubectl logs -f <pod-name> -n zero-trust
kubectl logs <pod-name> -n zero-trust --previous
kubectl logs -l app=zero-trust-app -n zero-trust --tail=100
```

### Port Forwarding
```bash
kubectl port-forward -n zero-trust svc/zero-trust-app 8080:80
kubectl port-forward -n zero-trust pod/<pod-name> 8080:8080
```

## Getting Help

If you cannot resolve an issue:

1. Check Azure Monitor logs
2. Review Application Insights
3. Consult [RUNBOOKS.md](RUNBOOKS.md) for procedures
4. Contact platform team
5. Open GitHub issue with logs and diagnostics

## Additional Resources

- [Azure AKS Troubleshooting](https://docs.microsoft.com/en-us/azure/aks/troubleshooting)
- [Kubernetes Troubleshooting](https://kubernetes.io/docs/tasks/debug/)
- [Prometheus Troubleshooting](https://prometheus.io/docs/prometheus/latest/troubleshooting/)
