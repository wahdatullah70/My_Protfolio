import os
import shutil
import socket
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException

APP_NAME = "Infra Health API"
APP_VERSION = "1.1.0"

app = FastAPI(title=APP_NAME, version=APP_VERSION)


def uptime_seconds():
    try:
        return float(Path("/proc/uptime").read_text().split()[0])
    except Exception:
        return None


def load_average():
    try:
        return list(os.getloadavg())
    except (AttributeError, OSError):
        return []


def memory_info():
    data = {}
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            key, value = line.split(":", 1)
            data[key] = value.strip()
    except Exception:
        return {}
    return {
        "mem_total": data.get("MemTotal"),
        "mem_available": data.get("MemAvailable"),
        "swap_total": data.get("SwapTotal"),
        "swap_free": data.get("SwapFree"),
    }


def disk_info(path="/"):
    usage = shutil.disk_usage(path)
    used = usage.total - usage.free
    return {
        "path": path,
        "total_bytes": usage.total,
        "used_bytes": used,
        "free_bytes": usage.free,
        "used_percent": round((used / usage.total) * 100, 2) if usage.total else 0,
    }


def system_snapshot():
    return {
        "timestamp": int(time.time()),
        "service": APP_NAME,
        "version": APP_VERSION,
        "hostname": socket.gethostname(),
        "uptime_seconds": uptime_seconds(),
        "load_average": load_average(),
        "memory": memory_info(),
        "disk": disk_info("/"),
    }


@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": APP_NAME, "version": APP_VERSION}


@app.get("/readyz")
def readyz():
    try:
        disk = disk_info("/")
    except OSError as exc:
        raise HTTPException(status_code=503, detail=f"filesystem unavailable: {exc}") from exc

    return {
        "status": "ready",
        "checks": {
            "filesystem": "ok",
            "root_free_bytes": disk["free_bytes"],
            "proc_uptime_available": uptime_seconds() is not None,
        },
    }


@app.get("/api/v1/system")
def system_info():
    return system_snapshot()
