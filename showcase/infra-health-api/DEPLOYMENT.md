# Deployment Guide

## Deployment flow

```text
Source code
   │
   ▼
Build container image
   │
   ▼
Run local smoke test
   │
   ▼
Push image to registry
   │
   ▼
Kubernetes Deployment
   │
   ├── liveness probe
   ├── readiness probe
   ├── resource requests/limits
   └── non-root security context
   │
   ▼
Service endpoint
```

## Local validation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8080
```

Smoke test:

```bash
curl -f http://127.0.0.1:8080/healthz
curl -f http://127.0.0.1:8080/readyz
curl -s http://127.0.0.1:8080/api/v1/system
```

## Docker

```bash
docker build -t infra-health-api:local .
docker run --rm -p 8080:8080 infra-health-api:local
```

Repeat the smoke tests against `localhost:8080`.

## Kubernetes

The included manifests demonstrate the deployment structure:

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

Then check:

```bash
kubectl get pods
kubectl get svc
kubectl describe deployment infra-health-api
```

Port-forward for a local test when appropriate:

```bash
kubectl port-forward svc/infra-health-api 8080:80
```

## Operational checks

```bash
kubectl logs deployment/infra-health-api --tail=100
kubectl get events --sort-by=.lastTimestamp | tail -n 30
```

## Production hardening

Before exposing a service like this outside a trusted environment, consider:

- TLS termination;
- authentication/authorization;
- rate limiting;
- NetworkPolicies;
- image scanning;
- immutable image tags/digests;
- centralized logs/metrics;
- explicit metric/data exposure policy.

The example intentionally keeps the service small so the Linux → API → container → Kubernetes path is easy to inspect end-to-end.
