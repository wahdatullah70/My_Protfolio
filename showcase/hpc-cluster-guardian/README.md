# HPC Cluster Guardian

A lightweight **Linux + Slurm cluster health diagnostic tool** designed for HPC administrators and research environments.

It collects host health, memory/storage information, and — when Slurm is installed — scheduler/node status into a machine-readable JSON report.

## Why this project exists

HPC incidents often begin with a simple question: **is the operating system healthy, is storage available, and does Slurm agree that the nodes are healthy?**

`cluster_guardian.py` provides one small diagnostic entry point that can be run manually, through cron, or from an operations pipeline.

## Features

- Hostname and timestamp
- System uptime
- Memory summary
- Root filesystem capacity
- Load average
- Slurm partition summary with `sinfo`
- Active job summary with `squeue`
- Node information with `scontrol`
- Graceful behavior when Slurm commands are unavailable
- JSON output suitable for logging or downstream automation

## Architecture

```text
                    +----------------------+
                    |  cluster_guardian.py |
                    +----------+-----------+
                               |
            +------------------+------------------+
            |                  |                  |
            v                  v                  v
       Linux /proc         Core utilities       Slurm CLI
      load + uptime       free / df / host   sinfo/squeue/scontrol
            |                  |                  |
            +------------------+------------------+
                               |
                               v
                       JSON health report
```

## Run

```bash
python3 cluster_guardian.py
```

Save a report:

```bash
python3 cluster_guardian.py --output cluster-report.json
```

Pretty-print to the terminal:

```bash
python3 cluster_guardian.py --pretty
```

## Example output

```json
{
  "host": "compute01",
  "status": "healthy",
  "load_average": [0.21, 0.18, 0.16],
  "filesystem": {
    "mount": "/",
    "used_percent": 42
  },
  "slurm": {
    "available": true,
    "partitions": "compute* up infinite 2 idle"
  }
}
```

## Operations use cases

- Pre-flight checks before submitting workloads
- Compute-node readiness validation
- Incident triage
- Cron-based health snapshots
- Cluster maintenance verification
- Collecting evidence for troubleshooting

## Skills demonstrated

`Python` · `Linux` · `Slurm` · `HPC Operations` · `System Administration` · `Observability` · `Troubleshooting`

> This project intentionally uses standard system commands and Python's standard library so it remains easy to deploy on restricted HPC systems.
