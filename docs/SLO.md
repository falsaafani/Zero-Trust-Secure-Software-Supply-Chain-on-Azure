# Service Level Objectives (SLOs)

This document defines the Service Level Objectives for the Zero-Trust Secure Software Supply Chain application.

## Overview

Service Level Objectives (SLOs) define the target level of service quality we aim to provide. These are measured using Service Level Indicators (SLIs) and backed by Service Level Agreements (SLAs) where applicable.

## SLO Summary

| Service Aspect | SLO Target | Measurement Period |
|----------------|------------|-------------------|
| Availability | 99.9% | 30 days |
| Request Success Rate | 99.5% | 7 days |
| Latency (p95) | < 500ms | 7 days |
| Latency (p99) | < 1000ms | 7 days |
| Error Budget | 0.1% | 30 days |

## Detailed SLOs

### 1. Availability SLO

**Objective:** The service shall be available 99.9% of the time over a 30-day period.

**Definition of Available:**
- Service responds to health check within 5 seconds
- At least 1 pod is running and ready
- Ingress is accessible

**Measurement:**
```promql
avg_over_time(up{job="zero-trust-app"}[30d]) >= 0.999
```

**Error Budget:**
- 30 days = 43,200 minutes
- 0.1% = 43.2 minutes of allowed downtime per month

**Exclusions:**
- Scheduled maintenance windows
- Customer-side issues
- Third-party service failures (documented)
- Force majeure events

**Monitoring:**
```bash
# Check current availability
kubectl get pods -n zero-trust -l app=zero-trust-app
curl -f https://zero-trust-app.example.com/health
```

**Alert Thresholds:**
- Warning: Availability < 99.95% over 24 hours
- Critical: Availability < 99.9% over 7 days

### 2. Request Success Rate SLO

**Objective:** 99.5% of requests shall complete successfully over a 7-day period.

**Definition of Successful Request:**
- HTTP status code 2xx or 3xx
- Response received within timeout period
- No application errors

**Measurement:**
```promql
sum(rate(app_request_count{http_status=~"2..|3.."}[7d]))
/
sum(rate(app_request_count[7d])) >= 0.995
```

**Error Budget:**
- 0.5% of requests can fail
- Example: If 1M requests/week, 5,000 failures allowed

**Exclusions:**
- Client errors (4xx) due to invalid requests
- Rate limit rejections
- Authentication failures from invalid credentials

**Monitoring:**
```promql
# Current error rate
sum(rate(app_request_count{http_status=~"5.."}[5m]))
/
sum(rate(app_request_count[5m]))
```

**Alert Thresholds:**
- Warning: Error rate > 1% for 5 minutes
- Critical: Error rate > 5% for 5 minutes

### 3. Latency SLO (p95)

**Objective:** 95% of requests shall complete in less than 500ms over a 7-day period.

**Definition:**
- Time from request received to response sent
- Measured at application level
- Excludes network transit time

**Measurement:**
```promql
histogram_quantile(0.95,
  sum(rate(app_request_latency_seconds_bucket[7d])) by (le)
) < 0.5
```

**Target Breakdown by Endpoint:**
| Endpoint | p95 Target | p99 Target |
|----------|------------|------------|
| /health | 50ms | 100ms |
| / | 100ms | 200ms |
| /api/v1/data (GET) | 300ms | 600ms |
| /api/v1/data (POST) | 500ms | 1000ms |
| /metrics | 100ms | 200ms |

**Monitoring:**
```promql
# Current p95 latency
histogram_quantile(0.95,
  sum(rate(app_request_latency_seconds_bucket[5m])) by (le, endpoint)
)
```

**Alert Thresholds:**
- Warning: p95 > 750ms for 10 minutes
- Critical: p95 > 1000ms for 5 minutes

### 4. Latency SLO (p99)

**Objective:** 99% of requests shall complete in less than 1000ms over a 7-day period.

**Measurement:**
```promql
histogram_quantile(0.99,
  sum(rate(app_request_latency_seconds_bucket[7d])) by (le)
) < 1.0
```

**Monitoring:**
```promql
# Current p99 latency
histogram_quantile(0.99,
  sum(rate(app_request_latency_seconds_bucket[5m])) by (le, endpoint)
)
```

**Alert Thresholds:**
- Warning: p99 > 1500ms for 10 minutes
- Critical: p99 > 2000ms for 5 minutes

## Error Budget Policy

### Error Budget Calculation

Error budget = (1 - SLO) × Total time

**30-day Availability Example:**
- SLO: 99.9%
- Error Budget: 0.1% × 43,200 minutes = 43.2 minutes

### Error Budget Status

**Healthy (> 50% remaining):**
- Normal deployment cadence
- Feature development prioritized
- Standard testing procedures

**Warning (25-50% remaining):**
- Increased monitoring
- Code freeze for risky changes
- Enhanced testing required
- Post-mortems mandatory

**Critical (< 25% remaining):**
- All non-critical deployments frozen
- Focus on reliability improvements
- Emergency changes only
- Executive notification required

**Exhausted (0% remaining):**
- Complete deployment freeze
- All hands on reliability
- Daily executive updates
- SLO revision discussion

### Monitoring Error Budget

**Dashboard Metrics:**
```promql
# Error budget remaining (availability)
(1 - (1 - avg_over_time(up{job="zero-trust-app"}[30d])) / (1 - 0.999)) * 100

# Error budget burn rate
rate(app_request_count{http_status=~"5.."}[1h])
/
rate(app_request_count[1h])
```

**Burn Rate Alerts:**
- 2x burn rate for 1 hour: Page on-call
- 5x burn rate for 15 minutes: Escalate to engineering manager
- 10x burn rate for 5 minutes: Incident declared

## Service Level Indicators (SLIs)

### Primary SLIs

1. **Availability SLI**
   ```promql
   avg_over_time(up{job="zero-trust-app"}[5m])
   ```

2. **Success Rate SLI**
   ```promql
   sum(rate(app_request_count{http_status=~"2..|3.."}[5m]))
   /
   sum(rate(app_request_count[5m]))
   ```

3. **Latency SLI (p95)**
   ```promql
   histogram_quantile(0.95,
     sum(rate(app_request_latency_seconds_bucket[5m])) by (le)
   )
   ```

4. **Latency SLI (p99)**
   ```promql
   histogram_quantile(0.99,
     sum(rate(app_request_latency_seconds_bucket[5m])) by (le)
   )
   ```

### Secondary SLIs

1. **Resource Utilization**
   ```promql
   # CPU utilization
   sum(rate(container_cpu_usage_seconds_total{namespace="zero-trust"}[5m]))

   # Memory utilization
   sum(container_memory_usage_bytes{namespace="zero-trust"})
   ```

2. **Pod Health**
   ```promql
   # Healthy pods
   sum(kube_pod_status_phase{namespace="zero-trust", phase="Running"})

   # Pod restarts
   rate(kube_pod_container_status_restarts_total{namespace="zero-trust"}[5m])
   ```

3. **Deployment Status**
   ```promql
   # Available replicas
   kube_deployment_status_replicas_available{namespace="zero-trust"}

   # Desired replicas
   kube_deployment_spec_replicas{namespace="zero-trust"}
   ```

## Reporting

### Weekly SLO Report

**Report Template:**
```markdown
# SLO Report: Week of [Date]

## Summary
- Availability: XX.XX% (Target: 99.9%)
- Success Rate: XX.XX% (Target: 99.5%)
- Latency p95: XXXms (Target: < 500ms)
- Latency p99: XXXms (Target: < 1000ms)
- Error Budget Remaining: XX.X%

## Incidents
- [List of incidents affecting SLOs]

## Action Items
- [Improvement items]
```

### Monthly SLO Review

**Attendees:** Engineering team, Product, Leadership
**Agenda:**
1. Review SLO performance
2. Analyze trends
3. Discuss error budget
4. Plan improvements
5. Adjust SLOs if needed

### Annual SLO Planning

**Process:**
1. Review historical data
2. Assess customer needs
3. Evaluate technical capabilities
4. Set targets for next year
5. Update documentation

## SLO Exceptions

### Planned Maintenance

**Notification:**
- 7 days advance notice
- Excluded from SLO calculations
- Maximum 2 hours per month
- Off-peak hours only

**Process:**
```bash
# Before maintenance
kubectl annotate deployment zero-trust-app -n zero-trust \
  maintenance-window="start:$(date -u +%s)"

# After maintenance
kubectl annotate deployment zero-trust-app -n zero-trust \
  maintenance-window="end:$(date -u +%s)"
```

### Dependency Failures

External service failures affecting SLOs:
- Documented and tracked
- May be excluded from SLO calculations
- Require mitigation plans
- Drive architecture improvements

## Continuous Improvement

### SLO Evolution

SLOs should be reviewed and adjusted based on:
- Historical performance data
- Customer feedback
- Business requirements
- Technical capabilities
- Industry standards

### Improvement Initiatives

When SLOs are consistently met:
1. Consider tightening targets
2. Invest in new features
3. Reduce operational overhead

When SLOs are consistently missed:
1. Freeze feature development
2. Focus on reliability
3. Increase monitoring
4. Add redundancy
5. Improve automation

## Dashboards and Monitoring

### Grafana Dashboards

**SLO Overview Dashboard:**
- Current SLO status
- Trend graphs
- Error budget remaining
- Burn rate

**Detailed SLI Dashboard:**
- Request rate
- Error rate
- Latency percentiles
- Resource utilization

### Access

```bash
# Port forward to Grafana
kubectl port-forward -n monitoring svc/grafana 3000:80

# Open browser to http://localhost:3000
```

### Alerts Configuration

All SLO-related alerts defined in `/monitoring/alerts.yaml`

```bash
# Apply alerts
kubectl apply -f monitoring/alerts.yaml
```

## References

- [Google SRE Book - SLOs](https://sre.google/sre-book/service-level-objectives/)
- [Site Reliability Engineering](https://sre.google/books/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)

---

**Document Version:** 1.0
**Last Updated:** 2025-10-02
**Next Review:** 2026-01-02
**Owner:** Platform Team
