#!/usr/bin/env python3
"""Core parsing, health rules, reporting, and metrics for the HPC Platform Control Plane."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

ALERT_NODE_STATES = {"down", "drain", "drained", "fail", "failing", "unknown"}
FAILED_JOB_STATES = {"FAILED", "CANCELLED", "TIMEOUT", "NODE_FAIL", "OUT_OF_MEMORY"}


@dataclass
class Node:
    name: str
    state: str
    cpus: int
    allocated_cpus: int
    idle_cpus: int
    memory_mb: int
    gres: str


@dataclass
class Job:
    job_id: str
    user: str
    partition: str
    state: str
    elapsed: str
    nodes: int
    reason: str


@dataclass
class AccountingRecord:
    job_id: str
    state: str
    elapsed: str
    exit_code: str
    max_rss: str


def _lines(text: str) -> Iterable[str]:
    for raw in text.splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            yield line


def parse_sinfo(text: str) -> list[Node]:
    nodes = []
    for line in _lines(text):
        p = line.split("|")
        if len(p) != 7:
            raise ValueError(f"invalid sinfo fixture line: {line}")
        nodes.append(Node(p[0], p[1], int(p[2]), int(p[3]), int(p[4]), int(p[5]), p[6]))
    return nodes


def parse_squeue(text: str) -> list[Job]:
    jobs = []
    for line in _lines(text):
        p = line.split("|")
        if len(p) != 7:
            raise ValueError(f"invalid squeue fixture line: {line}")
        jobs.append(Job(p[0], p[1], p[2], p[3], p[4], int(p[5]), p[6]))
    return jobs


def parse_sacct(text: str) -> list[AccountingRecord]:
    records = []
    for line in _lines(text):
        p = line.split("|")
        if len(p) != 5:
            raise ValueError(f"invalid sacct fixture line: {line}")
        records.append(AccountingRecord(*p))
    return records


def elapsed_seconds(value: str) -> int:
    """Parse Slurm-like D-HH:MM:SS, HH:MM:SS, or MM:SS durations."""
    days = 0
    if "-" in value:
        day_text, value = value.split("-", 1)
        days = int(day_text)
    parts = [int(x) for x in value.split(":")]
    if len(parts) == 3:
        h, m, s = parts
    elif len(parts) == 2:
        h, m, s = 0, parts[0], parts[1]
    else:
        raise ValueError(f"unsupported elapsed value: {value}")
    return days * 86400 + h * 3600 + m * 60 + s


def load_policy(path: Path | None = None) -> dict:
    policy = {
        "pending_minutes_warning": 15,
        "memory_used_percent_warning": 90,
        "disk_used_percent_warning": 90,
        "load_per_cpu_warning": 1.5,
        "gpu_temperature_c_warning": 82,
    }
    if path:
        policy.update(json.loads(path.read_text()))
    return policy


def analyze(nodes: list[Node], jobs: list[Job], accounting: list[AccountingRecord], metrics: list[dict], policy: dict) -> dict:
    incidents: list[dict] = []

    for node in nodes:
        state = node.state.lower().rstrip("*")
        if state in ALERT_NODE_STATES:
            incidents.append({"severity": "critical", "type": "node_state", "subject": node.name, "message": f"node state is {node.state}"})

    pending_limit = int(policy["pending_minutes_warning"]) * 60
    for job in jobs:
        if job.state.upper() == "PENDING" and elapsed_seconds(job.elapsed) >= pending_limit:
            incidents.append({"severity": "warning", "type": "pending_job", "subject": job.job_id, "message": f"pending {job.elapsed}: {job.reason}"})
        if job.state.upper() in FAILED_JOB_STATES:
            incidents.append({"severity": "critical", "type": "job_state", "subject": job.job_id, "message": f"job state is {job.state}"})

    for record in accounting:
        if record.state.upper() in FAILED_JOB_STATES:
            incidents.append({"severity": "critical", "type": "accounting_failure", "subject": record.job_id, "message": f"historical job ended {record.state} (exit {record.exit_code})"})

    node_by_name = {n.name: n for n in nodes}
    for item in metrics:
        name = item["node"]
        if item.get("memory_used_percent", 0) >= policy["memory_used_percent_warning"]:
            incidents.append({"severity": "warning", "type": "memory_pressure", "subject": name, "message": f"memory usage {item['memory_used_percent']}%"})
        if item.get("disk_used_percent", 0) >= policy["disk_used_percent_warning"]:
            incidents.append({"severity": "warning", "type": "disk_pressure", "subject": name, "message": f"disk usage {item['disk_used_percent']}%"})
        if item.get("gpu_temperature_c", 0) >= policy["gpu_temperature_c_warning"]:
            incidents.append({"severity": "warning", "type": "gpu_temperature", "subject": name, "message": f"GPU temperature {item['gpu_temperature_c']} C"})
        node = node_by_name.get(name)
        if node and node.cpus:
            load_per_cpu = item.get("load1", 0) / node.cpus
            if load_per_cpu >= policy["load_per_cpu_warning"]:
                incidents.append({"severity": "warning", "type": "cpu_load", "subject": name, "message": f"1m load per CPU {load_per_cpu:.2f}"})

    critical = sum(1 for i in incidents if i["severity"] == "critical")
    warning = sum(1 for i in incidents if i["severity"] == "warning")
    total_cpus = sum(n.cpus for n in nodes)
    allocated_cpus = sum(n.allocated_cpus for n in nodes)

    return {
        "status": "critical" if critical else "warning" if warning else "healthy",
        "summary": {
            "nodes_total": len(nodes),
            "nodes_alerting": sum(1 for n in nodes if n.state.lower().rstrip("*") in ALERT_NODE_STATES),
            "cpus_total": total_cpus,
            "cpus_allocated": allocated_cpus,
            "cpu_allocation_percent": round((allocated_cpus / total_cpus) * 100, 2) if total_cpus else 0,
            "jobs_total": len(jobs),
            "jobs_running": sum(1 for j in jobs if j.state.upper() == "RUNNING"),
            "jobs_pending": sum(1 for j in jobs if j.state.upper() == "PENDING"),
            "incidents_total": len(incidents),
            "incidents_critical": critical,
            "incidents_warning": warning,
        },
        "incidents": incidents,
        "nodes": [asdict(n) for n in nodes],
        "jobs": [asdict(j) for j in jobs],
        "accounting": [asdict(r) for r in accounting],
        "node_metrics": metrics,
    }


def load_fixture_report(fixture_dir: Path, policy_path: Path | None = None) -> dict:
    nodes = parse_sinfo((fixture_dir / "sinfo.txt").read_text())
    jobs = parse_squeue((fixture_dir / "squeue.txt").read_text())
    accounting = parse_sacct((fixture_dir / "sacct.txt").read_text())
    metrics = json.loads((fixture_dir / "node_metrics.json").read_text())
    return analyze(nodes, jobs, accounting, metrics, load_policy(policy_path))


def prometheus_metrics(report: dict) -> str:
    s = report["summary"]
    values = {
        "hpc_nodes_total": s["nodes_total"],
        "hpc_nodes_alerting": s["nodes_alerting"],
        "hpc_cpus_total": s["cpus_total"],
        "hpc_cpus_allocated": s["cpus_allocated"],
        "hpc_jobs_running": s["jobs_running"],
        "hpc_jobs_pending": s["jobs_pending"],
        "hpc_incidents_total": s["incidents_total"],
        "hpc_incidents_critical": s["incidents_critical"],
        "hpc_incidents_warning": s["incidents_warning"],
    }
    return "\n".join(f"{key} {value}" for key, value in values.items()) + "\n"
