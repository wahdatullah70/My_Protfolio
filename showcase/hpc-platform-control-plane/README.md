# HPC Platform Control Plane

A recruiter-grade **HPC operations control plane** that combines Slurm-style scheduler state, job accounting, Linux/node telemetry, incident rules, REST APIs, Prometheus-style metrics, Docker, Kubernetes, automated tests, and operator runbooks.

> **Evidence policy:** all committed cluster/job/node data in `fixtures/` is **synthetic demo data** created to make the project reproducible. It is not presented as historical production evidence.

## What this project demonstrates

- HPC / Slurm operations thinking
- scheduler and job-state parsing
- node health and capacity analysis
- failed-job and OOM triage
- pending-job policy checks
- CPU allocation visibility
- memory/disk pressure detection
- GPU temperature alerting
- REST API design with FastAPI
- Prometheus-style metrics endpoint
- CLI report generation
- JSON + Markdown operational reports
- Docker containerization
- hardened Kubernetes deployment
- unit + API testing
- CI/CD-ready project structure

## Architecture

```mermaid
flowchart LR
    A[Slurm / node inputs] --> B[HPC Ops Engine]
    A1[sinfo] --> B
    A2[squeue] --> B
    A3[sacct] --> B
    A4[Linux/GPU telemetry] --> B
    P[policy.json] --> B
    B --> C[Incident Rules]
    B --> D[Cluster Summary]
    C --> E[FastAPI]
    D --> E
    C --> F[CLI Reports]
    D --> F
    E --> G[/api/v1/cluster]
    E --> H[/api/v1/incidents]
    E --> I[/metrics]
    F --> J[JSON]
    F --> K[Markdown]
    F --> L[Prometheus text]
```

## Demo scenario

The committed fixtures intentionally include operational problems so the incident engine can be demonstrated:

- one drained compute node
- a job pending longer than policy threshold
- one currently failed job
- historical failed and out-of-memory jobs
- memory pressure
- disk pressure
- elevated GPU temperature

These values are synthetic and exist only for deterministic testing.

## Run the CLI

```bash
cd showcase/hpc-platform-control-plane
python3 cli.py --pretty
```

Generate artifacts:

```bash
python3 cli.py \
  --json-out cluster-report.json \
  --markdown-out cluster-report.md \
  --metrics-out metrics.txt \
  --pretty
```

The demo exits with code `2` when the fixture-backed cluster has warnings/critical incidents. This makes it useful in scheduled checks or CI automation.

## Run the API

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8080
```

Endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /healthz` | process liveness |
| `GET /readyz` | fixture/input readiness |
| `GET /api/v1/cluster` | complete cluster operations report |
| `GET /api/v1/incidents` | incident-focused response |
| `GET /metrics` | Prometheus-style numeric metrics |

Examples:

```bash
curl http://localhost:8080/healthz
curl http://localhost:8080/api/v1/cluster
curl http://localhost:8080/api/v1/incidents
curl http://localhost:8080/metrics
```

## Policy-driven alerting

`policy.json` controls thresholds without changing code:

```json
{
  "pending_minutes_warning": 15,
  "memory_used_percent_warning": 90,
  "disk_used_percent_warning": 90,
  "load_per_cpu_warning": 1.5,
  "gpu_temperature_c_warning": 82
}
```

## Prometheus-style metrics

Example metric names:

```text
hpc_nodes_total
hpc_nodes_alerting
hpc_cpus_total
hpc_cpus_allocated
hpc_jobs_running
hpc_jobs_pending
hpc_incidents_total
hpc_incidents_critical
hpc_incidents_warning
```

## Tests

```bash
python -m unittest discover -s tests -v
```

Coverage includes duration parsing, incident detection, fixture analysis, Prometheus output, health/readiness endpoints, cluster API, incidents API, and metrics API.

## Docker

```bash
docker build -t hpc-platform-control-plane .
docker run --rm -p 8080:8080 hpc-platform-control-plane
```

The image runs as an unprivileged user and includes a container healthcheck.

## Kubernetes

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

Deployment controls include:

- non-root execution
- privilege escalation disabled
- all Linux capabilities dropped
- read-only root filesystem
- `RuntimeDefault` seccomp
- service-account token disabled
- CPU/memory requests and limits
- startup, readiness and liveness probes

## Repository structure

```text
hpc-platform-control-plane/
├── app.py
├── cli.py
├── hpcops.py
├── policy.json
├── requirements.txt
├── Dockerfile
├── fixtures/
│   ├── sinfo.txt
│   ├── squeue.txt
│   ├── sacct.txt
│   └── node_metrics.json
├── k8s/
│   ├── deployment.yaml
│   └── service.yaml
├── tests/
│   ├── test_hpcops.py
│   └── test_api.py
├── ARCHITECTURE.md
└── RUNBOOK.md
```

## Production extension path

A real-cluster adapter can replace fixture input with commands such as:

```bash
sinfo -N -h -o '%N|%T|%c|%C|%m|%G'
squeue -h -o '%i|%u|%P|%T|%M|%D|%R'
sacct -n -P --format JobID,State,Elapsed,ExitCode,MaxRSS
```

Additional production work could add:

- `scontrol show node/job` enrichment
- SlurmDBD/accounting database integration
- NVIDIA DCGM / `nvidia-smi` telemetry
- Prometheus exporter/client library
- Grafana dashboards
- alert webhooks / Slack / email
- authentication and RBAC
- persistent incident history
- reservation/QOS/fair-share checks
- filesystem/storage checks
- multi-cluster inventory

## Skills demonstrated

`HPC` · `Slurm` · `Linux` · `Python` · `FastAPI` · `REST API` · `Prometheus` · `Docker` · `Kubernetes` · `GPU Operations` · `Observability` · `Incident Response` · `DevOps` · `Platform Engineering` · `Testing`
