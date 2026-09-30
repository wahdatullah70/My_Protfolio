#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import socket
import subprocess
import time
from pathlib import Path


def run(cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return {
            "ok": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
        }
    except Exception as exc:
        return {"ok": False, "stdout": "", "stderr": str(exc), "returncode": -1}


def load_average():
    try:
        return list(os.getloadavg())
    except (AttributeError, OSError):
        return []


def uptime_seconds():
    try:
        return float(Path('/proc/uptime').read_text().split()[0])
    except Exception:
        return None


def memory_summary():
    result = run(["free", "-m"])
    return result["stdout"] if result["ok"] else None


def filesystem_summary():
    result = run(["df", "-P", "/"])
    if not result["ok"]:
        return {"mount": "/", "used_percent": None, "raw": result["stderr"]}
    lines = result["stdout"].splitlines()
    if len(lines) < 2:
        return {"mount": "/", "used_percent": None, "raw": result["stdout"]}
    parts = lines[-1].split()
    used = int(parts[4].rstrip('%')) if len(parts) >= 5 else None
    return {
        "mount": parts[-1] if parts else "/",
        "used_percent": used,
        "raw": lines[-1],
    }


def slurm_summary():
    available = shutil.which("sinfo") is not None
    if not available:
        return {"available": False}

    sinfo = run(["sinfo", "-h", "-o", "%P %a %l %D %t"])
    squeue = run(["squeue", "-h", "-o", "%i %P %j %u %T %M %D %R"])
    scontrol = run(["scontrol", "show", "nodes"])
    return {
        "available": True,
        "partitions": sinfo["stdout"] if sinfo["ok"] else sinfo["stderr"],
        "jobs": squeue["stdout"] if squeue["ok"] else squeue["stderr"],
        "nodes": scontrol["stdout"] if scontrol["ok"] else scontrol["stderr"],
    }


def overall_status(fs):
    used = fs.get("used_percent")
    if used is not None and used >= 90:
        return "warning"
    return "healthy"


def collect():
    fs = filesystem_summary()
    return {
        "timestamp": int(time.time()),
        "host": socket.gethostname(),
        "status": overall_status(fs),
        "uptime_seconds": uptime_seconds(),
        "load_average": load_average(),
        "memory": memory_summary(),
        "filesystem": fs,
        "slurm": slurm_summary(),
    }


def main():
    parser = argparse.ArgumentParser(description="Collect Linux and Slurm cluster health information")
    parser.add_argument("--output", help="Write JSON report to a file")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = parser.parse_args()

    report = collect()
    text = json.dumps(report, indent=2 if args.pretty else None)
    print(text)

    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
