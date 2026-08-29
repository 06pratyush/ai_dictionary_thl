#!/usr/bin/env bash
# Usage: ./.orchestrator/verify.sh [--repair]
# Full-project regression check. Runs after EVERY integration, no exceptions.
set -uo pipefail
REPAIR="${1:-}"
RUN=".orchestrator/tmp/verify.out"; : > "$RUN"

echo "--- lint ---" >> "$RUN"
command -v ruff >/dev/null 2>&1 && ruff check . >> "$RUN" 2>&1

echo "--- python tests ---" >> "$RUN"
[ -d tests ] && python -m pytest -q >> "$RUN" 2>&1

echo "--- js tests ---" >> "$RUN"
[ -f tests/search-engine.test.mjs ] && node tests/search-engine.test.mjs >> "$RUN" 2>&1

echo "--- corpus + build ---" >> "$RUN"
python build/validate.py >> "$RUN" 2>&1

python -m pytest -q 2>/dev/null | grep -oE '^[A-Za-z0-9_/.:]+::[A-Za-z0-9_]+' \
  | sort > .orchestrator/tmp/now_failing.txt || true
NEW=$(comm -13 .orchestrator/baseline/failing.txt .orchestrator/tmp/now_failing.txt 2>/dev/null)

if [ -z "$NEW" ] && ! grep -qiE '^ERROR|error:|failed|FAILED' "$RUN"; then
  echo "VERIFY_PASS — no regressions"; exit 0
fi

echo "VERIFY_FAIL"
[ -n "$NEW" ] && { echo "NEW_FAILURES:"; echo "$NEW"; }
grep -iE '^ERROR|error:|failed|FAILED' "$RUN" | head -12
exit 1
