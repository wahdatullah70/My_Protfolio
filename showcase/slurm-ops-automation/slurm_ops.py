#!/usr/bin/env python3
"""Slurm operations automation utility.

Collects node/job state from Slurm CLI output (or local fixtures), identifies
common operational warnings, and emits JSON plus an optional Markdown report.

The tool uses standard Slurm text formats rather than private APIs so it can be
used on login/head nodes with minimal dependencies.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

NODE_FORMAT = "%N|%T|%c|%m|%G"
JOB_FORMAT = "%i|%P|%j|%u|%T|%M|%D|%R"

BAD_NODE_STATES = {"down", "drain", "drained", "fail", "failing", "unknown"}
WATCH_JOB_STATES = {"pending", "failed", "cancelled", "timeout", "node_fail", "out_of_memory"}


@dataclass
class NodeRecord:
    name: str
    state: str
    cpus: int
    memory_mb: int
    gres: str


@dataclass
class JobRecord:
    job_id: str
    partition: str
    name: str
    user: str
    state: str
    elapsed: str
    nodes: int
    reason_or_nodelist: str


def run(command: list[str]) -> str:
    proc = subprocess.run(command, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(command)}\n{proc.stderr.strip()}")
    return proc.stdout


def parse_nodes(text: str) -> list[NodeRecord]:
    nodes: list[NodeRecord] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split("|", 4)
        if len(parts) != 5:
            raise ValueError(f"invalid sinfo fixture/output line: {line}")
        name, state, cpus, memory_mb, gres = parts
        nodes.append(NodeRecord(name=name, state=state.lower(), cpus=int(cpus), memory_mb=int(memory_mb), gres=gres))
    return nodes


def parse_jobs(text: str) -> list[JobRecord]:
    jobs: list[JobRecord] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split("|", 7)
        if len(parts) != 8:
            raise ValueError(f"invalid squeue fixture/output line: {line}")
        job_id, partition, name, user, state, elapsed, nodes, reason = parts
        jobs.append(JobRecord(job_id=job_id, partition=partition, name=name, user=user,
                              state=state.lower(), elapsed=elapsed, nodes=int(nodes),
                              reason_or_nodelist=reason))
    return jobs


def load_live() -> tuple[list[NodeRecord], list[JobRecord], str]:
    missing = [cmd for cmd in ("sinfo", "squeue") if shutil.which(cmd) is None]
    if missing:
        raise RuntimeError(f"required Slurm commands not found: {', '.join(missing)}")

    nodes_raw = run(["sinfo", "-N", "-h", "-o", NODE_FORMAT])
    jobs_raw = run(["squeue", "-h", "-o", JOB_FORMAT])
    return parse_nodes(nodes_raw), parse_jobs(jobs_raw), "live"


def load_fixture(directory: Path) -> tuple[list[NodeRecord], list[JobRecord], str]:
    nodes = parse_nodes((directory / "sinfo.txt").read_text())
    jobs = parse_jobs((directory / "squeue.txt").read_text())
    return nodes, jobs, f"fixture:{directory}"


def build_report(nodes: Iterable[NodeRecord], jobs: Iterable[JobRecord], source: str) -> dict:
    nodes = list(nodes)
    jobs = list(jobs)

    node_alerts = [
        {"node": n.name, "state": n.state, "message": f"node {n.name} requires attention ({n.state})"}
        for n in nodes
        if n.state.split("+")[0] in BAD_NODE_STATES
    ]

    job_alerts = []
    for j in jobs:
        state = j.state.split("+")[0]
        if state in WATCH_JOB_STATES:
            job_alerts.append({
                "job_id": j.job_id,
                "state": j.state,
                "reason": j.reason_or_nodelist,
                "message": f"job {j.job_id} is {j.state}: {j.reason_or_nodelist}",
            })

    ready_states = {"idle", "alloc", "allocated", "mixed", "comp", "completing"}
    ready_nodes = sum(1 for n in nodes if n.state.split("+")[0] in ready_states)

    summary = {
        "nodes_total": len(nodes),
        "nodes_ready_or_busy": ready_nodes,
        "node_alerts": len(node_alerts),
        "jobs_total": len(jobs),
        "jobs_running": sum(1 for j in jobs if j.state.startswith("running")),
        "jobs_pending": sum(1 for j in jobs if j.state.startswith("pending")),
        "job_alerts": len(job_alerts),
    }

    status = "healthy" if not node_alerts and not job_alerts else "warning"
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "status": status,
        "summary": summary,
        "alerts": {"nodes": node_alerts, "jobs": job_alerts},
        "nodes": [asdict(n) for n in nodes],
        "jobs": [asdict(j) for j in jobs],
    }


def render_markdown(report: dict) -> str:
    s = report["summary"]
    lines = [
        "# Slurm Operations Report",
        "",
        f"- **Status:** {report['status'].upper()}",
        f"- **Source:** `{report['source']}`",
        f"- **Generated:** `{report['generated_at']}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Nodes total | {s['nodes_total']} |",
        f"| Nodes ready/busy | {s['nodes_ready_or_busy']} |",
        f"| Node alerts | {s['node_alerts']} |",
        f"| Jobs total | {s['jobs_total']} |",
        f"| Running jobs | {s['jobs_running']} |",
        f"| Pending jobs | {s['jobs_pending']} |",
        f"| Job alerts | {s['job_alerts']} |",
        "",
        "## Alerts",
        "",
    ]

    alerts = report["alerts"]["nodes"] + report["alerts"]["jobs"]
    if not alerts:
        lines.append("No operational alerts detected.")
    else:
        lines.extend(f"- {a['message']}" for a in alerts)

    lines += ["", "## Nodes", "", "| Node | State | CPUs | Memory MB | GRES |", "|---|---|---:|---:|---|"]
    for n in report["nodes"]:
        lines.append(f"| {n['name']} | {n['state']} | {n['cpus']} | {n['memory_mb']} | {n['gres']} |")

    lines += ["", "## Jobs", "", "| Job | User | State | Nodes | Reason / NodeList |", "|---|---|---|---:|---|"]
    for j in report["jobs"]:
        lines.append(f"| {j['job_id']} | {j['user']} | {j['state']} | {j['nodes']} | {j['reason_or_nodelist']} |")

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit Slurm nodes/jobs and generate an operations report")
    parser.add_argument("--fixture-dir", type=Path, help="Use sinfo.txt and squeue.txt from a fixture directory")
    parser.add_argument("--json-out", type=Path, default=Path("slurm-report.json"))
    parser.add_argument("--markdown-out", type=Path, default=Path("slurm-report.md"))
    parser.add_argument("--pretty", action="store_true", help="Also print JSON report to stdout")
    args = parser.parse_args()

    if args.fixture_dir:
        nodes, jobs, source = load_fixture(args.fixture_dir)
    else:
        nodes, jobs, source = load_live()

    report = build_report(nodes, jobs, source)
    args.json_out.write_text(json.dumps(report, indent=2) + "\n")
    args.markdown_out.write_text(render_markdown(report))

    if args.pretty:
        print(json.dumps(report, indent=2))

    raise SystemExit(0 if report["status"] == "healthy" else 1)


if __name__ == "__main__":
    main()
