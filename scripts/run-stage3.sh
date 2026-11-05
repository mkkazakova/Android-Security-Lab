#!/usr/bin/env bash
# Managed by project-update.yml - Stage 3
set -euo pipefail
bash scripts/run-stage2.sh
python3 scripts/storage-tests.py
