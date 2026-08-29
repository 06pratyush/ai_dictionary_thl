#!/usr/bin/env bash
# Usage: ./.orchestrator/gate.sh <path> [package-dir]
set -uo pipefail
T="${1:?path required}"
PKG="${2:-}"
FAIL=0
case "$T" in
  *.py)
    python -m py_compile "$T" || FAIL=1
    if command -v ruff >/dev/null 2>&1; then ruff check "$T" || FAIL=1; fi
    if [ -n "$PKG" ]; then
      python .orchestrator/imports.py "$T" --package "$PKG" || FAIL=1
    else
      python .orchestrator/imports.py "$T" || FAIL=1
    fi
    ;;
  *.json) python -c "import json,sys; json.load(open(sys.argv[1],encoding='utf-8'))" "$T" || FAIL=1 ;;
  *.js|*.mjs) node --check "$T" || FAIL=1 ;;
  *.html) python .orchestrator/htmlcheck.py "$T" || FAIL=1 ;;
esac
exit $FAIL
