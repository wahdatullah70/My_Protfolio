# Operator Runbook

## 1. Generate a snapshot

```bash
python3 cli.py --json-out cluster-report.json --markdown-out cluster-report.md --pretty
```

Exit codes:
- `0` — healthy fixture state
- `2` — warning or critical incidents detected

## 2. Investigate node-state incidents

For a real Slurm cluster:

```bash
sinfo -N -l
scontrol show node <node>
```

Check drain reason, hardware state, daemon reachability, filesystem mounts, memory pressure, GPU visibility, and recent system logs before returning a node to service.

## 3. Investigate pending jobs

```bash
squeue -j <jobid> -o '%.18i %.9P %.16j %.8u %.2t %.10M %.6D %R'
scontrol show job <jobid>
```

Review requested resources, partition/QOS, reservations, constraints, dependency state, licenses, and available nodes.

## 4. Investigate failed/OOM jobs

```bash
sacct -j <jobid> --format JobID,JobName,Partition,State,Elapsed,ExitCode,MaxRSS,ReqMem
scontrol show job <jobid>
```

For `OUT_OF_MEMORY`, compare `MaxRSS` with requested memory and inspect application logs before increasing memory blindly.

## 5. Investigate node pressure

```bash
uptime
free -h
df -h
df -i
ps aux --sort=-%mem | head
```

GPU nodes:

```bash
nvidia-smi
nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv
```

## 6. API checks

```bash
curl -fsS http://localhost:8080/healthz
curl -fsS http://localhost:8080/readyz
curl -s http://localhost:8080/api/v1/incidents | python3 -m json.tool
curl -s http://localhost:8080/metrics
```

## 7. Kubernetes checks

```bash
kubectl get deploy,pods,svc -l app=hpc-platform-control-plane
kubectl describe deployment hpc-platform-control-plane
kubectl logs deployment/hpc-platform-control-plane
```

## Safety

This repository is read-only by design. Do not automate `scontrol update NodeName=... State=RESUME/DRAIN` or job cancellation from alert logic without human approval, authorization, audit logging, and cluster-specific safeguards.
