# Architecture

## Goal

Provide one small control plane that turns scheduler state, accounting history, and node telemetry into a consistent operations view for HPC administrators.

## Components

### Input adapters

The demo uses committed fixtures that mirror the shape of `sinfo`, `squeue`, `sacct`, and node telemetry. A production implementation would replace fixture reads with command/API collectors.

### HPC operations engine

`hpcops.py` is deliberately framework-independent. It parses source data, applies policy, calculates capacity/utilization summaries, and emits incidents.

### Policy layer

`policy.json` separates operational thresholds from application code. This makes alert behavior reviewable and configurable.

### API layer

`app.py` exposes health, readiness, cluster state, incidents, and Prometheus-style metrics.

### CLI layer

`cli.py` supports operator use, scheduled jobs, and CI. It can generate JSON, Markdown, and text metrics from the same engine used by the API.

## Failure model

The project distinguishes critical scheduler/job failures from warning-level resource conditions. The process remains healthy even when the simulated cluster is critical; `/healthz` represents service liveness, while `/api/v1/cluster` represents cluster operational state.

## Security model

The demo API is read-only. The Kubernetes manifest minimizes container privilege and does not grant Kubernetes API credentials. A production control plane that executes Slurm commands or queries cluster APIs should use dedicated read-only identities and explicit authorization boundaries.
