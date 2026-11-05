#!/usr/bin/env bash
# Managed by project-update.yml - Stage 4
set -euo pipefail
bash scripts/run-stage3.sh
python3 scripts/keystore-tests.py
