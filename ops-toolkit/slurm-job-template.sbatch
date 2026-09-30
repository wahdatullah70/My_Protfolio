#!/bin/bash
#SBATCH --job-name=demo-job
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=1
#SBATCH --time=00:10:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail

mkdir -p logs

echo "Job ID: ${SLURM_JOB_ID:-unknown}"
echo "Node list: ${SLURM_JOB_NODELIST:-unknown}"
echo "Tasks: ${SLURM_NTASKS:-unknown}"
echo "Start: $(date -Is)"

echo "Running a simple distributed hostname check..."
srun hostname

echo "End: $(date -Is)"
