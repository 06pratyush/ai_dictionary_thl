#!/usr/bin/env bash
# Usage: ./.orchestrator/ask.sh <file-or-"-"> "<question>" [max-lines]
set -euo pipefail
SRC="${1:?file or - required}"
Q="${2:?question required}"
MAXLINES="${3:-25}"
READER="${ORCH_READER:-orch-reader}"
BODY=$([ "$SRC" = "-" ] && cat || cat "$SRC")
{
  echo "You are a code-reading assistant. Answer ONLY from the content below."
  echo "If the answer is not present, reply exactly: NOT_FOUND."
  echo "Do not summarize anything not asked. Do not add preamble or opinions."
  echo "Quote exact identifiers, signatures and line numbers where relevant."
  echo "Hard limit: $MAXLINES lines of output."
  echo
  echo "QUESTION: $Q"
  echo
  echo "--- CONTENT START ---"
  echo "$BODY"
  echo "--- CONTENT END ---"
} | ollama run "$READER" 2>/dev/null | head -n "$MAXLINES"
