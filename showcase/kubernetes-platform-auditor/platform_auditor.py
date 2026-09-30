#!/usr/bin/env python3
import argparse
import json
import subprocess
import time
from pathlib import Path

PRESSURE_CONDITIONS = {"MemoryPressure", "DiskPressure", "PIDPressure", "NetworkUnavailable"}
CRITICAL_WAITING_REASONS = {"CrashLoopBackOff", "ImagePullBackOff", "ErrImagePull", "CreateContainerConfigError"}


def kubectl_json(args, context=None):
    cmd = ["kubectl"]
    if context:
        cmd += ["--context", context]
    cmd += args + ["-o", "json"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "kubectl command failed")
    return json.loads(proc.stdout)


def node_status(node):
    conditions = node.get("status", {}).get("conditions", []) or []
    cond_map = {c.get("type"): c.get("status") for c in conditions}
    info = node.get("status", {}).get("nodeInfo", {})
    pressure = [name for name in PRESSURE_CONDITIONS if cond_map.get(name) == "True"]
    return {
        "name": node.get("metadata", {}).get("name", "unknown"),
        "ready": cond_map.get("Ready") == "True",
        "pressure_conditions": sorted(pressure),
        "kubelet_version": info.get("kubeletVersion"),
        "os_image": info.get("osImage"),
        "kernel": info.get("kernelVersion"),
    }


def pod_status(pod, restart_threshold=5):
    status = pod.get("status", {})
    phase = status.get("phase", "Unknown")
    namespace = pod.get("metadata", {}).get("namespace", "default")
    name = pod.get("metadata", {}).get("name", "unknown")
    statuses = status.get("containerStatuses", []) or []

    restarts = sum(cs.get("restartCount", 0) for cs in statuses)
    unready = [cs.get("name", "unknown") for cs in statuses if not cs.get("ready", False)]
    waiting_reasons = []
    terminated_reasons = []
    for cs in statuses:
        state = cs.get("state", {}) or {}
        if state.get("waiting", {}).get("reason"):
            waiting_reasons.append(state["waiting"]["reason"])
        if state.get("terminated", {}).get("reason"):
            terminated_reasons.append(state["terminated"]["reason"])

    reasons = []
    if phase not in {"Running", "Succeeded"}:
        reasons.append(f"phase={phase}")
    if phase == "Running" and unready:
        reasons.append("containers_not_ready")
    critical_waiting = sorted(set(waiting_reasons) & CRITICAL_WAITING_REASONS)
    if critical_waiting:
        reasons.extend(critical_waiting)
    if restarts >= restart_threshold:
        reasons.append(f"high_restarts={restarts}")

    healthy = not reasons
    return {
        "namespace": namespace,
        "name": name,
        "phase": phase,
        "restarts": restarts,
        "containers": len(statuses),
        "unready_containers": unready,
        "waiting_reasons": sorted(set(waiting_reasons)),
        "terminated_reasons": sorted(set(terminated_reasons)),
        "healthy": healthy,
        "reasons": reasons,
    }


def build_report(nodes_payload, pods_payload, context="current-context", restart_threshold=5):
    nodes = [node_status(n) for n in nodes_payload.get("items", [])]
    pods = [pod_status(p, restart_threshold) for p in pods_payload.get("items", [])]

    unhealthy_nodes = [n for n in nodes if not n["ready"] or n["pressure_conditions"]]
    unhealthy_pods = [p for p in pods if not p["healthy"]]
    crashloop_pods = [p for p in pods if "CrashLoopBackOff" in p["waiting_reasons"]]
    high_restart_pods = [p for p in pods if p["restarts"] >= restart_threshold]
    unready_container_pods = [p for p in pods if p["unready_containers"]]

    summary = {
        "nodes": len(nodes),
        "ready_nodes": sum(1 for n in nodes if n["ready"]),
        "nodes_with_pressure": sum(1 for n in nodes if n["pressure_conditions"]),
        "pods": len(pods),
        "unhealthy_pods": len(unhealthy_pods),
        "crashloop_pods": len(crashloop_pods),
        "high_restart_pods": len(high_restart_pods),
        "pods_with_unready_containers": len(unready_container_pods),
        "total_restarts": sum(p["restarts"] for p in pods),
        "affected_namespaces": sorted({p["namespace"] for p in unhealthy_pods}),
    }

    return {
        "timestamp": int(time.time()),
        "context": context,
        "status": "healthy" if not unhealthy_nodes and not unhealthy_pods else "warning",
        "restart_threshold": restart_threshold,
        "summary": summary,
        "unhealthy_nodes": unhealthy_nodes,
        "unhealthy_pods": unhealthy_pods,
        "nodes": nodes,
    }


def audit(context=None, restart_threshold=5):
    nodes_payload = kubectl_json(["get", "nodes"], context)
    pods_payload = kubectl_json(["get", "pods", "--all-namespaces"], context)
    return build_report(nodes_payload, pods_payload, context or "current-context", restart_threshold)


def main():
    parser = argparse.ArgumentParser(description="Audit Kubernetes platform health")
    parser.add_argument("--context", help="Optional kubeconfig context")
    parser.add_argument("--output", help="Write report to JSON file")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    parser.add_argument("--restart-threshold", type=int, default=5, help="Warn when pod restarts reach this value")
    parser.add_argument("--fixture-dir", type=Path, help="Read nodes.json and pods.json instead of calling kubectl")
    args = parser.parse_args()

    try:
        if args.fixture_dir:
            nodes_payload = json.loads((args.fixture_dir / "nodes.json").read_text())
            pods_payload = json.loads((args.fixture_dir / "pods.json").read_text())
            report = build_report(nodes_payload, pods_payload, f"fixture:{args.fixture_dir}", args.restart_threshold)
        else:
            report = audit(args.context, args.restart_threshold)
    except Exception as exc:
        report = {"timestamp": int(time.time()), "status": "error", "error": str(exc)}

    print(json.dumps(report, indent=2 if args.pretty else None))
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=2) + "\n")

    raise SystemExit(0 if report.get("status") == "healthy" else 1)


if __name__ == "__main__":
    main()
