#!/usr/bin/env bash
# Usage: ./.orchestrator/expert.sh <expert> <prompt-file> [max-lines]
set -euo pipefail
exec python .orchestrator/expert.py "$@"
