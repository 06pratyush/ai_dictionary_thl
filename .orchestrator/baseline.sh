#!/usr/bin/env bash
mkdir -p .orchestrator/baseline
python -m pytest -q 2>/dev/null | grep -oE '^[A-Za-z0-9_/.:]+::[A-Za-z0-9_]+' \
  | sort > .orchestrator/baseline/failing.txt || true
echo "BASELINE_CAPTURED failing=$(wc -l < .orchestrator/baseline/failing.txt)"
