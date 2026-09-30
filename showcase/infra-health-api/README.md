# Infra Health API

A production-minded **container-ready infrastructure health service** that exposes a small, controlled set of Linux host telemetry through FastAPI and includes hardened Docker/Kubernetes deployment examples.

This project demonstrates how system-administration data can be wrapped in a service that is easy to monitor, test, containerize, and deploy in a platform-engineering workflow.

## Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /healthz` | Lightweight liveness response with service/version metadata |
| `GET /readyz` | Readiness check including filesystem accessibility |
| `GET /api/v1/system` | Hostname, uptime, load, memory, and disk telemetry |

## Architecture

```text
Client / Monitoring
       |
       | HTTP
       v
+------------------+
|  FastAPI service |
+--------+---------+
         |
         +----> Linux /proc
         +----> filesystem statistics
         +----> load average
         |
         v
      JSON API

Deployment options:
  Docker -> non-root container + HEALTHCHECK
  Kubernetes -> Deployment + Service + startup/liveness/readiness probes
```

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8080
```

Then:

```bash
curl http://localhost:8080/healthz
curl http://localhost:8080/readyz
curl http://localhost:8080/api/v1/system
```

## Tests

```bash
python -m unittest discover -s tests -v
```

The tests validate:

- liveness endpoint status and metadata;
- readiness endpoint structure;
- system telemetry response shape;
- expected disk/memory/service fields.

The same tests run automatically in the portfolio GitHub Actions workflow.

## Example response

See [`examples/system-response.example.json`](examples/system-response.example.json).

The committed example is **synthetic documentation data**, not a claim about a specific production host.

## Docker

```bash
docker build -t infra-health-api .
docker run --rm -p 8080:8080 infra-health-api
```

The Docker image:

- runs as UID `10001` instead of root;
- exposes port `8080`;
- includes a native `HEALTHCHECK` against `/healthz`;
- disables the Uvicorn server header.

## Kubernetes

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

The Deployment includes:

- startup, liveness, and readiness probes;
- CPU/memory requests and limits;
- `runAsNonRoot` with fixed UID/GID;
- `allowPrivilegeEscalation: false`;
- all Linux capabilities dropped;
- `readOnlyRootFilesystem: true`;
- `RuntimeDefault` seccomp profile;
- service-account token automount disabled.

These controls make the example more representative of a production-minded platform workload while keeping the service simple enough to understand.

## Operational flow

```text
Container starts
      |
      v
startupProbe -> /healthz
      |
      v
readinessProbe -> /readyz
      |
      +---- ready -> Service can send traffic
      |
      v
livenessProbe -> /healthz
      |
      +---- repeated failure -> kubelet restarts container
```

## Engineering concepts demonstrated

- Linux system telemetry
- Python / FastAPI
- REST API design
- endpoint testing
- Docker healthchecks
- Kubernetes probes
- resource management
- non-root containers
- capability dropping
- seccomp
- read-only root filesystem
- platform engineering
- CI validation

## Security note

This demo intentionally exposes only a narrow set of non-secret operational information. Production deployments should still consider authentication/authorization, TLS, NetworkPolicy, rate limiting, audit logging, and explicit policy for which host metrics may leave a node.

## Related deployment guide

See [`DEPLOYMENT.md`](DEPLOYMENT.md) for build, rollout, verification, and troubleshooting steps.
