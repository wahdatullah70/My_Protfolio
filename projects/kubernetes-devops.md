# Kubernetes & DevOps Platform Engineering

## Overview

This case study summarizes work on a cloud-native research platform used for infrastructure, security, and distributed-systems experimentation.

## Platform Components

- Multi-node Kubernetes cluster
- Calico networking
- Helm-based deployments
- Longhorn persistent storage
- Security telemetry services
- Streaming and data-processing services
- Model inference and alert-processing components
- Slurm services deployed in Kubernetes for HPC experimentation

## Engineering Work

### Kubernetes operations
- Validated control-plane and worker-node readiness.
- Inspected pods, services, namespaces, deployments, and cluster resources.
- Diagnosed application and infrastructure issues using Kubernetes status, events, and logs.
- Managed Helm-based research services.

### Networking and storage
- Worked with Calico networking in a multi-node environment.
- Used Longhorn-backed persistent storage for stateful workloads.
- Investigated connectivity and service availability between components.

### Research service stack
Worked with services including:

- Suricata
- Zeek
- Tetragon
- Redpanda
- Redis
- Stream-processing services
- ML inference services
- Alert-routing services
- Fluent Bit

### Slurm + Kubernetes
- Validated Slurm controller and worker components running in a Kubernetes research environment.
- Inspected node readiness and controller placement.
- Supported experimentation combining HPC scheduling and container orchestration.

## Tools & Technologies

`Kubernetes` `Helm` `Calico` `Longhorn` `Docker` `Slurm` `Linux` `Redpanda` `Redis` `Fluent Bit`

## What this demonstrates

This project demonstrates practical platform-engineering skills across orchestration, networking, storage, observability, security services, workload scheduling, and multi-component troubleshooting.
