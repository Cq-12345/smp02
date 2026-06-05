#!/usr/bin/env bash
set -euo pipefail

export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0,1}"
PYTHONPATH=src conda run --no-capture-output -n mhc_pyg314 python -m smp02.cli run-all --config configs/reproduce.yaml
