#!/usr/bin/env bash
# Managed by project-update.yml - current full test suite
set -euo pipefail
bash scripts/run-stage4.sh
# ASL_VISUAL_EVIDENCE_V1: record screenshots after validated full run
python3 scripts/capture-visual-evidence.py
