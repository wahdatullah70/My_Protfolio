#!/usr/bin/env bash
set -euo pipefail

# Read-only Kubernetes cluster health snapshot.
# Requires kubectl and access to a cluster.

if ! command -v kubectl >/dev/null 2>&1; then
  echo "kubectl is not installed or not in PATH" >&2
  exit 1
fi

section() {
  printf '\n===== %s =====\n' "$1"
}

section "CLUSTER INFO"
kubectl cluster-info || true

section "NODES"
kubectl get nodes -o wide

section "NON-RUNNING PODS"
kubectl get pods -A --field-selector=status.phase!=Running -o wide || true

section "POD STATUS SUMMARY"
kubectl get pods -A --no-headers 2>/dev/null \
  | awk '{count[$4]++} END {for (s in count) printf "%s: %d\n", s, count[s]}' \
  | sort || true

section "DEPLOYMENTS"
kubectl get deployments -A || true

section "STATEFULSETS"
kubectl get statefulsets -A || true

section "PERSISTENT VOLUME CLAIMS"
kubectl get pvc -A || true

section "RECENT WARNING EVENTS"
kubectl get events -A --field-selector=type=Warning \
  --sort-by='.lastTimestamp' 2>/dev/null | tail -n 30 || true

section "RESOURCE USAGE"
if kubectl top nodes >/dev/null 2>&1; then
  kubectl top nodes
  printf '\n'
  kubectl top pods -A --sort-by=cpu | tail -n 20 || true
else
  echo "Metrics API is unavailable; skipping kubectl top."
fi

printf '\nCluster health snapshot completed.\n'
