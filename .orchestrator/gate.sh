#!/usr/bin/env bash
# Usage: ./.orchestrator/gate.sh <path>   -> exits non-zero on any failure
set -uo pipefail
TARGET="${1:?path required}"
FAIL=0
case "$TARGET" in
  *.json)
    python -c "import json,sys; json.load(open(sys.argv[1],encoding='utf-8'))" "$TARGET" || FAIL=1
    ;;
  *.js)
    node --check "$TARGET" || FAIL=1
    ;;
  *.html)
    python .orchestrator/htmlcheck.py "$TARGET" || FAIL=1
    ;;
  *.py)
    python -m py_compile "$TARGET" || FAIL=1
    ;;
esac
exit $FAIL
