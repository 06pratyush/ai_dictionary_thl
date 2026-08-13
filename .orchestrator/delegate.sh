#!/usr/bin/env bash
# Usage: ./.orchestrator/delegate.sh <model> <prompt-file> <output-file> [json]
#
# Dispatches through the Ollama HTTP API rather than `ollama run`. The CLI is a
# TUI: it emits cursor-movement and erase-line codes even when redirected, and
# hard-wraps at the terminal width. Stripping those codes after the fact leaves
# duplicated word fragments ("generaliz generalize") because an erase-line is
# semantic, not decorative. The API returns the raw completion with none of it.
set -euo pipefail
MODEL="${1:?model required}"
PROMPT_FILE="${2:?prompt file required}"
OUT_FILE="${3:?output file required}"
FORMAT="${4:-}"

mkdir -p .orchestrator/logs
START=$(date +%s)

REQ=".orchestrator/tmp/$(basename "$PROMPT_FILE").req.json"
python - "$PROMPT_FILE" "$MODEL" "$FORMAT" > "$REQ" <<'PY'
import json, sys
prompt = open(sys.argv[1], encoding="utf-8").read()
import os
# Leave num_ctx to the Modelfile by default. orch-reader is built with 65536;
# overriding it here would force Ollama to evict and reload the resident model.
options = {"temperature": float(os.environ.get("ORCH_TEMP", "0.2"))}
if os.environ.get("ORCH_NUM_CTX"):
    options["num_ctx"] = int(os.environ["ORCH_NUM_CTX"])
body = {
    "model": sys.argv[2],
    "prompt": prompt,
    "stream": False,
    "keep_alive": "8h",
    "options": options,
}
if sys.argv[3] == "json":
    body["format"] = "json"
print(json.dumps(body))
PY

curl -s -X POST http://localhost:11434/api/generate \
  -H 'Content-Type: application/json' \
  --data-binary "@$REQ" \
  -o ".orchestrator/tmp/$(basename "$OUT_FILE").envelope.json" \
  2>".orchestrator/logs/last_error.log"

python - ".orchestrator/tmp/$(basename "$OUT_FILE").envelope.json" "$OUT_FILE" <<'PY'
import json, sys
env = json.load(open(sys.argv[1], encoding="utf-8"))
if "error" in env:
    sys.exit(f"OLLAMA_ERROR: {env['error']}")
open(sys.argv[2], "w", encoding="utf-8").write(env.get("response", ""))
PY

END=$(date +%s)
echo "MODEL=$MODEL DURATION=$((END-START))s BYTES=$(wc -c < "$OUT_FILE")"
