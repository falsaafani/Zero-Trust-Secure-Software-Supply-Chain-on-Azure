# Operational Runbooks

This document contains standardized procedures for common operational tasks.

## Table of Contents
1. [Daily Operations](#daily-operations)
2. [Deployment Procedures](#deployment-procedures)
3. [Scaling Procedures](#scaling-procedures)
4. [Backup and Recovery](#backup-and-recovery)
5. [Security Operations](#security-operations)
6. [Monitoring and Alerting](#monitoring-and-alerting)

## Daily Operations

### Morning Health Check

**Frequency:** Daily at 09:00 UTC
**Duration:** 10 minutes
**Owner:** Platform Team

**Procedure:**
1. Check cluster health
   ```bash
   kubectl get nodes
   kubectl get pods --all-namespaces | grep -v "Running\|Completed"
   ```

2. Review application status
   ```bash
   kubectl get pods -n zero-trust
   kubectl top pods -n zero-trust
   ```

3. Check recent alerts
   ```bash
   kubectl logs -n monitoring deployment/alertmanager --tail=50
   ```

4. Review deployment status
   ```bash
   kubectl get deployments -n zero-trust
   kubectl rollout status deployment/zero-trust-app -n zero-trust
   ```

5. Verify metrics collection
   ```bash
   curl http://prometheus.example.com/api/v1/query?query=up
   ```

**Success Criteria:**
- All nodes in Ready state
- All pods in Running state
- No critical alerts
- Metrics being collected

### Weekly Maintenance

**Frequency:** Sunday at 02:00 UTC
**Duration:** 2 hours
**Owner:** Platform Team

**Procedure:**
1. Review resource utilization
   ```bash
   kubectl top nodes
   kubectl top pods --all-namespaces
   ```

2. Check for pod restarts
   ```bash
   kubectl get pods -n zero-trust -o json | jq '.items[] | select(.status.restartCount > 5) | {name: .metadata.name, restarts: .status.restartCount}'
   ```

3. Review security scan results
   ```bash
   kubectl get policyreport -n zero-trust
   ```

4. Check certificate expiration
   ```bash
   kubectl get certificates -n zero-trust
   ```

5. Review logs for errors
   ```bash
   kubectl logs -n zero-trust -l app=zero-trust-app --tail=1000 | grep -i error
   ```

**Action Items:**
- Document any anomalies
- Create tickets for recurring issues
- Update runbooks as needed

## Deployment Procedures

### Standard Deployment

**Trigger:** New release approved
**Duration:** 30 minutes
**Owner:** DevOps Team

**Pre-Deployment Checklist:**
- [ ] All tests passing in CI
- [ ] Security scans completed
- [ ] Change request approved
- [ ] Rollback plan prepared
- [ ] Stakeholders notified

**Procedure:**
1. Verify current state
   ```bash
   kubectl get deployment zero-trust-app -n zero-trust -o yaml
   kubectl rollout history deployment/zero-trust-app -n zero-trust
   ```

2. Tag and push new image
   ```bash
   IMAGE_TAG="v$(date +%Y%m%d-%H%M%S)"
   docker build -t acrzerotrust.azurecr.io/zero-trust-app:$IMAGE_TAG ./App
   docker push acrzerotrust.azurecr.io/zero-trust-app:$IMAGE_TAG
   ```

3. Update deployment
   ```bash
   kubectl set image deployment/zero-trust-app \
     app=acrzerotrust.azurecr.io/zero-trust-app:$IMAGE_TAG \
     -n zero-trust
   ```

4. Monitor rollout
   ```bash
   kubectl rollout status deployment/zero-trust-app -n zero-trust --timeout=10m
   ```

5. Verify deployment
   ```bash
   kubectl get pods -n zero-trust -l app=zero-trust-app
   kubectl logs -n zero-trust -l app=zero-trust-app --tail=20
   ```

6. Health check
   ```bash
   POD=$(kubectl get pod -n zero-trust -l app=zero-trust-app -o jsonpath='{.items[0].metadata.name}')
   kubectl exec -n zero-trust $POD -- curl -f http://localhost:8080/health
   ```

7. Monitor metrics
   ```bash
   # Check error rate and latency in Grafana
   # Verify no spike in errors
   ```

**Post-Deployment:**
- Update deployment documentation
- Notify stakeholders of completion
- Monitor for 1 hour

**Rollback Procedure:**
```bash
kubectl rollout undo deployment/zero-trust-app -n zero-trust
kubectl rollout status deployment/zero-trust-app -n zero-trust
```

### Emergency Hotfix

**Trigger:** Critical production issue
**Duration:** 15 minutes
**Owner:** On-call Engineer

**Procedure:**
1. Assess severity
2. Get approval from on-call manager
3. Fast-track through CI/CD
4. Deploy using standard procedure
5. Monitor closely for 2 hours
6. Post-mortem within 24 hours

## Scaling Procedures

### Manual Scale Up

**Trigger:** Anticipated traffic increase
**Duration:** 5 minutes
**Owner:** Platform Team

**Procedure:**
1. Check current capacity
   ```bash
   kubectl get hpa -n zero-trust
   kubectl get pods -n zero-trust -l app=zero-trust-app
   ```

2. Scale deployment
   ```bash
   kubectl scale deployment zero-trust-app -n zero-trust --replicas=<desired-count>
   ```

3. Verify scaling
   ```bash
   kubectl get pods -n zero-trust -l app=zero-trust-app -w
   ```

4. Monitor metrics
   ```bash
   # Check CPU/Memory utilization
   kubectl top pods -n zero-trust
   ```

### Scale Down

**Trigger:** Traffic decreased
**Duration:** 10 minutes
**Owner:** Platform Team

**Procedure:**
1. Verify low traffic
   ```bash
   # Check request rate in Grafana
   ```

2. Scale down gradually
   ```bash
   kubectl scale deployment zero-trust-app -n zero-trust --replicas=<reduced-count>
   ```

3. Monitor for 30 minutes
4. Ensure no degradation

### Auto-scaling Configuration

**Procedure:**
```bash
kubectl autoscale deployment zero-trust-app \
  -n zero-trust \
  --cpu-percent=70 \
  --min=3 \
  --max=10

kubectl get hpa -n zero-trust -w
```

## Backup and Recovery

### Application Configuration Backup

**Frequency:** Daily at 01:00 UTC
**Retention:** 30 days
**Owner:** Platform Team

**Procedure:**
1. Backup Kubernetes resources
   ```bash
   kubectl get all -n zero-trust -o yaml > backup-$(date +%Y%m%d).yaml
   kubectl get configmaps -n zero-trust -o yaml >> backup-$(date +%Y%m%d).yaml
   kubectl get secrets -n zero-trust -o yaml >> backup-$(date +%Y%m%d).yaml
   ```

2. Upload to Azure Storage
   ```bash
   az storage blob upload \
     --account-name <storage-account> \
     --container-name backups \
     --file backup-$(date +%Y%m%d).yaml \
     --name zero-trust/backup-$(date +%Y%m%d).yaml
   ```

### Disaster Recovery

**RTO:** 4 hours
**RPO:** 1 hour
**Owner:** Platform Lead

**Procedure:**
1. Assess impact and scope
2. Notify incident commander
3. Restore from backup
   ```bash
   az storage blob download \
     --account-name <storage-account> \
     --container-name backups \
     --name zero-trust/backup-<date>.yaml \
     --file restore.yaml

   kubectl apply -f restore.yaml
   ```

4. Verify restoration
5. Update DNS if needed
6. Conduct post-mortem

## Security Operations

### Security Incident Response

**Trigger:** Security alert or suspicious activity
**Owner:** Security Team

**Procedure:**
1. Identify and isolate
   ```bash
   kubectl get pods -n zero-trust
   kubectl logs <suspicious-pod> -n zero-trust
   ```

2. Capture evidence
   ```bash
   kubectl logs <pod> -n zero-trust > incident-logs-$(date +%Y%m%d-%H%M%S).txt
   kubectl describe pod <pod> -n zero-trust > incident-describe-$(date +%Y%m%d-%H%M%S).txt
   ```

3. Quarantine if necessary
   ```bash
   kubectl label pod <pod> -n zero-trust quarantine=true
   kubectl delete pod <pod> -n zero-trust
   ```

4. Investigate
5. Remediate
6. Document incident

### Certificate Renewal

**Frequency:** 60 days before expiration
**Duration:** 30 minutes
**Owner:** Platform Team

**Procedure:**
1. Check current certificates
   ```bash
   kubectl get certificates -n zero-trust
   kubectl describe certificate <cert-name> -n zero-trust
   ```

2. Renew certificate
   ```bash
   kubectl delete secret <cert-secret> -n zero-trust
   kubectl apply -f k8s/ingress.yaml
   ```

3. Verify renewal
   ```bash
   kubectl get certificate <cert-name> -n zero-trust
   ```

### Vulnerability Patching

**Trigger:** Critical CVE identified
**Duration:** Varies
**Owner:** Security Team

**Procedure:**
1. Assess impact
2. Test patch in staging
3. Schedule maintenance window
4. Deploy patched image
5. Verify fix
6. Update security documentation

## Monitoring and Alerting

### Alert Response

**Critical Alert Response Time:** 15 minutes
**Warning Alert Response Time:** 4 hours

#### High Error Rate Alert

**Procedure:**
1. Acknowledge alert
2. Check application logs
   ```bash
   kubectl logs -n zero-trust -l app=zero-trust-app --tail=100 | grep ERROR
   ```
3. Review recent deployments
4. Check dependencies
5. Rollback if caused by recent deployment
6. Escalate if unresolved in 30 minutes

#### High Latency Alert

**Procedure:**
1. Check pod resources
   ```bash
   kubectl top pods -n zero-trust
   ```
2. Review database performance
3. Check external dependencies
4. Scale if resource constrained
5. Investigate slow queries

#### Pod Restart Alert

**Procedure:**
1. Check pod status
   ```bash
   kubectl get pods -n zero-trust
   kubectl describe pod <pod> -n zero-trust
   ```
2. Review pod logs
3. Check resource limits
4. Verify health checks
5. Investigate OOMKilled events

### Metrics Review

**Frequency:** Weekly
**Owner:** Platform Team

**Key Metrics:**
- Request rate
- Error rate
- Latency (p50, p95, p99)
- Resource utilization
- Pod restarts
- Security policy violations

**Procedure:**
1. Generate weekly report
2. Identify trends
3. Capacity planning
4. Optimize as needed

## On-Call Procedures

### Handoff Checklist

- [ ] Review open incidents
- [ ] Check recent deployments
- [ ] Review upcoming maintenance
- [ ] Verify access to all systems
- [ ] Update contact information

### Escalation Path

1. On-call Engineer (15 min)
2. Platform Lead (30 min)
3. Engineering Manager (1 hour)
4. VP Engineering (2 hours)

## Maintenance Windows

**Standard Maintenance:** Sunday 02:00-04:00 UTC
**Emergency Maintenance:** As needed with 2-hour notice

**Procedure:**
1. Create maintenance ticket
2. Notify stakeholders 48 hours in advance
3. Prepare rollback plan
4. Execute maintenance
5. Verify systems
6. Close ticket and notify

## Documentation

All procedures should be:
- Reviewed quarterly
- Updated after incidents
- Validated during drills
- Accessible to all team members
