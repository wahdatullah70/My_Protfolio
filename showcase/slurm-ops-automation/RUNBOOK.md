# Slurm Ops Automation Runbook

This runbook shows how to use the project during routine checks and incident triage.

## 1. Pre-flight check

Confirm the CLI tools are available:

```bash
which sinfo
which squeue
sinfo
squeue
```

If you do not have a live cluster, use the fixture mode documented in the README.

## 2. Generate a cluster snapshot

```bash
python3 slurm_ops.py \
  --json-out slurm-report.json \
  --markdown-out slurm-report.md
```

Interpretation:

- exit `0`: no configured warnings detected;
- exit `1`: one or more warning conditions detected;
- other failures: command execution/parsing problem.

## 3. Investigate node alerts

For a node in `DRAIN`, `DOWN`, `FAIL`, or another problematic state:

```bash
scontrol show node <node>
sinfo -N -l
```

Check:

- state reason;
- last busy time;
- available CPUs/memory;
- configured/allocated GRES;
- daemon health;
- filesystem/network availability.

Typical next actions may include fixing the underlying problem, validating the node, then returning it to service using the site's approved operational process.

## 4. Investigate pending jobs

For a pending job:

```bash
scontrol show job <job-id>
squeue -j <job-id> -o '%.18i %.9P %.20j %.8u %.2t %.10M %.6D %R'
```

Common reasons include:

- `Resources`
- `Priority`
- `Dependency`
- `QOSMax*`
- partition/account restrictions

Do not treat every pending job as an incident; pending state is highlighted because an operator may need to explain why it is waiting.

## 5. Investigate failed jobs

Use accounting when available:

```bash
sacct -j <job-id> --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
```

Then review the job's stdout/stderr files and application logs.

## 6. Maintenance workflow

Before maintenance:

```text
snapshot → drain target node → wait for workloads → perform maintenance
```

After maintenance:

```text
validate OS/network/storage → validate slurmd → inspect node → return to service → snapshot again
```

Keep the before/after Markdown reports with the maintenance record when useful.

## 7. Automation pattern

Example wrapper:

```bash
#!/usr/bin/env bash
set -euo pipefail

if python3 slurm_ops.py --json-out /tmp/slurm.json --markdown-out /tmp/slurm.md; then
  echo 'Slurm health check passed'
else
  rc=$?
  if [ "$rc" -eq 1 ]; then
    echo 'Slurm health check found warnings'
    cat /tmp/slurm.md
  else
    echo "Health collector failed with rc=$rc"
  fi
fi
```

## Scope

This utility is a first-pass operational aid. It does not replace Slurm accounting, monitoring, hardware telemetry, log aggregation, or site-specific operating procedures.
