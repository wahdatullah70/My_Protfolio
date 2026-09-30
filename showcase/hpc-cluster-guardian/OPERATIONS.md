# Operations Runbook

## Purpose

Use `cluster_guardian.py` as a quick pre-flight or incident-triage tool on a Linux/Slurm host.

## Standard workflow

```text
Run diagnostic
    │
    ▼
Collect Linux health
    │
    ▼
Collect Slurm health
    │
    ▼
Generate JSON
    │
    ▼
Review warnings
    │
    ▼
Investigate with native tools
```

## Pre-flight check

```bash
python3 cluster_guardian.py --pretty
```

Before a maintenance window or workload test, confirm:

- load is reasonable;
- memory is available;
- filesystem is not near capacity;
- Slurm is reachable;
- expected partitions/nodes appear.

## Save evidence

```bash
mkdir -p reports
python3 cluster_guardian.py --output "reports/$(hostname)-$(date +%Y%m%d-%H%M%S).json"
```

## Follow-up commands

If the report identifies a scheduler problem:

```bash
sinfo -Nel
squeue
scontrol show node <NODE>
```

If filesystem capacity is concerning:

```bash
df -h
du -xhd1 /path 2>/dev/null | sort -h
```

If memory/load is concerning:

```bash
free -h
uptime
ps aux --sort=-%mem | head
ps aux --sort=-%cpu | head
```

## Automation example

A simple cron workflow can save periodic snapshots:

```cron
*/15 * * * * /usr/bin/python3 /opt/cluster-guardian/cluster_guardian.py --output /var/log/cluster-guardian/latest.json
```

Choose paths and permissions appropriate for the environment.

## Limitations

This tool is a diagnostic summary, not a replacement for Prometheus, Slurm accounting, centralized logs, or full monitoring. Its value is fast, dependency-light operational visibility.
