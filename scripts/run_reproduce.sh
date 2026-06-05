#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH=src conda run --no-capture-output -n mhc_pyg314 python -m smp02.cli run-all --config configs/reproduce.yaml

