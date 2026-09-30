# Kubernetes Auditor Runbook

## Purpose

Use `platform_auditor.py` to create a concise first-pass snapshot before deeper `kubectl describe` and log analysis.

## Workflow

```text
Select Kubernetes context
        │
        ▼
Run auditor
        │
        ▼
Review node readiness
        │
        ▼
Review unhealthy pods / restarts
        │
        ▼
Identify namespace
        │
        ▼
Drill down with kubectl
```

## Standard audit

```bash
kubectl config current-context
python3 platform_auditor.py --pretty
```

For a different context:

```bash
python3 platform_auditor.py --context my-cluster --pretty
```

## Save incident evidence

```bash
mkdir -p reports
python3 platform_auditor.py --output "reports/audit-$(date +%Y%m%d-%H%M%S).json"
```

## Follow-up commands

### Node not ready

```bash
kubectl describe node <NODE>
kubectl get events -A --sort-by=.lastTimestamp | tail -n 50
```

### Pod unhealthy

```bash
kubectl describe pod <POD> -n <NAMESPACE>
kubectl logs <POD> -n <NAMESPACE> --all-containers --tail=200
```

### High restart count

```bash
kubectl get pod <POD> -n <NAMESPACE> -o wide
kubectl logs <POD> -n <NAMESPACE> --previous --tail=200
```

## CI / scheduled usage

Because the output is JSON, it can be archived as a pipeline artifact or parsed by another automation step.

Keep the tool read-only: the auditor should identify issues, not mutate the cluster automatically.

## Limitations

This is a fast triage utility, not a full observability platform. It complements metrics, logs, events, Prometheus/Grafana, and Kubernetes-native troubleshooting rather than replacing them.
