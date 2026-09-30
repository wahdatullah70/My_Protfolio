# Infra Health API

A small **container-ready infrastructure health service** that exposes Linux host information through a REST API and includes Docker and Kubernetes deployment examples.

This project demonstrates how system administration data can be wrapped into a service that is easy to monitor, deploy, test, and integrate into platform tooling.

## Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /healthz` | Lightweight liveness response |
| `GET /readyz` | Readiness response |
| `GET /api/v1/system` | Hostname, uptime, load, memory, disk |

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
  Docker -> container
  Kubernetes -> Deployment + Service + probes
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
curl http://localhost:8080/api/v1/system
```

## Docker

```bash
docker build -t infra-health-api .
docker run --rm -p 8080:8080 infra-health-api
```

## Kubernetes

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

The Deployment includes **liveness and readiness probes**, resource requests/limits, and a non-root container security context.

## Engineering concepts demonstrated

- Linux system telemetry
- Python / FastAPI
- REST API design
- Docker
- Kubernetes
- Health/readiness probes
- Resource management
- Container security basics
- Platform engineering
- DevOps deployment structure

## Security note

This demo intentionally exposes only non-sensitive operational information. Production deployments should add authentication/authorization, network policy, TLS, rate limiting, and explicit controls over which host metrics are exposed.
