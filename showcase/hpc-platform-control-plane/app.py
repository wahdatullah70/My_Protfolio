from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse

from hpcops import load_fixture_report, prometheus_metrics

BASE_DIR = Path(__file__).resolve().parent
FIXTURE_DIR = BASE_DIR / "fixtures"
POLICY = BASE_DIR / "policy.json"

app = FastAPI(
    title="HPC Platform Control Plane",
    version="1.0.0",
    description="Fixture-backed HPC/Slurm operations API for health, incidents and metrics.",
)


def current_report():
    try:
        return load_fixture_report(FIXTURE_DIR, POLICY)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "hpc-platform-control-plane"}


@app.get("/readyz")
def readyz():
    required = ["sinfo.txt", "squeue.txt", "sacct.txt", "node_metrics.json"]
    missing = [name for name in required if not (FIXTURE_DIR / name).exists()]
    if missing:
        raise HTTPException(status_code=503, detail={"missing": missing})
    return {"status": "ready", "mode": "fixture", "files": required}


@app.get("/api/v1/cluster")
def cluster():
    return current_report()


@app.get("/api/v1/incidents")
def incidents():
    report = current_report()
    return {"status": report["status"], "incidents": report["incidents"]}


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    return prometheus_metrics(current_report())
