#!/usr/bin/env python3
import argparse
import json
import subprocess
import time
from pathlib import Path


def kubectl_json(args, context=None):
    cmd = ["kubectl"]
    if context:
        cmd += ["--context", context]
    cmd += args + ["-o", "json"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "kubectl command failed")
    return json.loads(proc.stdout)


def node_ready(node):
    for condition in node.get("status", {}).get("conditions", []):
        if condition.get("type") == "Ready":
            return condition.get("status") == "True"
    return False


def pod_status(pod):
    phase = pod.get("status", {}).get("phase", "Unknown")
    restarts = sum(
        cs.get("restartCount", 0)
        for cs in pod.get("status", {}).get("containerStatuses", []) or []
    )
    namespace = pod.get("metadata", {}).get("namespace", "default")
    name = pod.get("metadata", {}).get("name", "unknown")
    healthy = phase in {"Running", "Succeeded"}
    return {
        "namespace": namespace,
        "name": name,
        "phase": phase,
        "restarts": restarts,
        "healthy": healthy,
    }


def audit(context=None):
    nodes_payload = kubectl_json(["get", "nodes"], context)
    pods_payload = kubectl_json(["get", "pods", "--all-namespaces"], context)

    nodes = []
    for node in nodes_payload.get("items", []):
        info = node.get("status", {}).get("nodeInfo", {})
        nodes.append({
            "name": node.get("metadata", {}).get("name"),
            "ready": node_ready(node),
            "kubelet_version": info.get("kubeletVersion"),
            "os_image": info.get("osImage"),
            "kernel": info.get("kernelVersion"),
        })

    pods = [pod_status(p) for p in pods_payload.get("items", [])]
    unhealthy = [p for p in pods if not p["healthy"]]
    ready_nodes = sum(1 for n in nodes if n["ready"])
    restart_total = sum(p["restarts"] for p in pods)

    status = "healthy"
    if ready_nodes != len(nodes) or unhealthy:
        status = "warning"

    namespaces = sorted({p["namespace"] for p in unhealthy})

    return {
        "timestamp": int(time.time()),
        "context": context or "current-context",
        "status": status,
        "summary": {
            "nodes": len(nodes),
            "ready_nodes": ready_nodes,
            "pods": len(pods),
            "unhealthy_pods": len(unhealthy),
            "total_restarts": restart_total,
            "affected_namespaces": namespaces,
        },
        "nodes": nodes,
        "unhealthy_pods": unhealthy,
    }


def main():
    parser = argparse.ArgumentParser(description="Audit Kubernetes platform health")
    parser.add_argument("--context", help="Optional kubeconfig context")
    parser.add_argument("--output", help="Write report to JSON file")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = parser.parse_args()

    try:
        report = audit(args.context)
    except Exception as exc:
        report = {
            "timestamp": int(time.time()),
            "status": "error",
            "error": str(exc),
        }

    print(json.dumps(report, indent=2 if args.pretty else None))
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
