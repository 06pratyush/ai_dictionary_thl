#!/usr/bin/env bash
# Usage: ./.orchestrator/ask.sh <file|-> "<question>" [max-lines]
set -euo pipefail
SRC="${1:?file or - required}"; Q="${2:?question required}"; MAX="${3:-20}"
BODY=$([ "$SRC" = "-" ] && cat || cat "$SRC")
{ echo "Hard limit: $MAX lines."; echo; echo "QUESTION: $Q"; echo
  echo "--- CONTENT START ---"; echo "$BODY"; echo "--- CONTENT END ---"
} > .orchestrator/tmp/ask.txt
python .orchestrator/expert.py reader .orchestrator/tmp/ask.txt "$MAX"
