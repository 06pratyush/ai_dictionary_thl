#!/usr/bin/env bash
# Usage: ./.orchestrator/gate.sh <path> [package-dir]
set -uo pipefail
T="${1:?path required}"
PKG="${2:-}"
FAIL=0

# An empty file compiles, lints and imports cleanly. A model timeout produces
# exactly that, so without this check the pipeline reports PASS on nothing --
# the worst available failure, because it looks like success. 12 lines is below
# any real artefact this project generates and above any plausible stub.
if [ ! -s "$T" ]; then
  echo "EMPTY_ARTEFACT: $T is zero bytes"
  exit 1
fi
if [ "$(grep -cve '^[[:space:]]*$' "$T")" -lt 12 ]; then
  echo "STUB_ARTEFACT: $T has fewer than 12 non-blank lines"
  exit 1
fi

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
