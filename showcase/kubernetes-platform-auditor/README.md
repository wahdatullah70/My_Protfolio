# Kubernetes Platform Auditor

A compact **Kubernetes operations auditing utility** for identifying unhealthy nodes, failing workloads, and namespace-level issues from a cluster snapshot.

## What it checks

- Node readiness and Kubernetes versions
- Pods not in `Running` or `Succeeded`
- Restart counts
- Namespaces containing unhealthy workloads
- Basic summary counts for fast triage
- JSON output for CI/CD or incident records

## Why it is useful

When a cluster is degraded, operators need a concise answer before opening dozens of `kubectl describe` views. This tool converts common `kubectl` observations into a structured report that highlights where to investigate first.

## Request flow

```text
kubectl / Kubernetes API
          |
          v
+-----------------------+
| platform_auditor.py   |
+-----------+-----------+
            |
   +--------+--------+
   |                 |
   v                 v
Node health       Pod health
   |                 |
   +--------+--------+
            |
            v
      audit-report.json
```

## Requirements

- Python 3.9+
- `kubectl`
- A working kubeconfig / Kubernetes context

## Run

```bash
python3 platform_auditor.py --pretty
```

Write the audit to disk:

```bash
python3 platform_auditor.py --output audit-report.json
```

Audit another context:

```bash
python3 platform_auditor.py --context my-cluster --pretty
```

## Example summary

```json
{
  "status": "warning",
  "summary": {
    "nodes": 3,
    "ready_nodes": 3,
    "pods": 42,
    "unhealthy_pods": 2,
    "total_restarts": 7
  }
}
```

## Engineering concepts demonstrated

`Kubernetes` · `kubectl` · `Python` · `Platform Engineering` · `JSON` · `Operations` · `Troubleshooting` · `DevOps`

## Next production extensions

- Prometheus metrics export
- Event analysis
- PVC/StorageClass checks
- resource requests/limits auditing
- CrashLoopBackOff reason extraction
- NetworkPolicy coverage checks
- Slack/email alert integration
