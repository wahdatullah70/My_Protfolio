# Cloud IDS & MLOps Research

## Overview

This project documents research into a multi-sensor intrusion-detection pipeline for cloud-native and HPC-oriented infrastructure.

The system combines network and runtime security telemetry, streaming/data services, and machine-learning inference to support reproducible security experiments.

## Architecture Areas

- Suricata network IDS telemetry
- Zeek network analysis
- Tetragon runtime/eBPF telemetry
- Redpanda streaming
- Redis
- Stream processing
- ONNX-based model inference
- Alert routing
- Kubernetes deployment

## Machine-Learning Workflow

The research workflow included:

1. Collecting and normalizing security telemetry.
2. Building a fused feature representation from multiple sensors.
3. Training/evaluating an intrusion-detection model using public IDS datasets.
4. Exporting the model for ONNX inference.
5. Deploying inference in a cloud-native pipeline.
6. Performing controlled validation and collecting reproducibility evidence.

## Research Results

Experiments included CIC-IDS2017 and UNSW-NB15 data and production-style validation in the research environment.

Reported research measurements include:

- F1 score: **0.93**
- False-positive rate: **0.04**
- Inference threshold: **0.90**
- 15-dimensional fused feature representation
- Low operational overhead during the documented validation environment

These values are research results tied to the experiment configuration and should not be interpreted as universal production performance.

## Operational Validation

The deployment work also involved controlled benign and malicious validation, negative-control checks, telemetry filtering, and timing measurements to make the experiment reproducible.

## Tools & Technologies

`Kubernetes` `Python` `ONNX` `Suricata` `Zeek` `Tetragon` `Redpanda` `Redis` `Linux` `MLOps` `Cybersecurity`

## What this demonstrates

This work demonstrates the ability to connect cybersecurity, distributed infrastructure, telemetry engineering, machine learning, and reproducible experimentation in one end-to-end system.

## Related Repository

[cloud-ids-mlops](https://github.com/wahdatullah70/cloud-ids-mlops)
