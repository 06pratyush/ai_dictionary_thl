#!/usr/bin/env python3
"""Run one expert from the registry.

Usage: python .orchestrator/expert.py <expert> <prompt-file> [max-lines]

Dispatches over Ollama's HTTP API rather than `ollama run`. The CLI is a TUI:
it emits cursor-movement and erase-line codes even when stdout is redirected,
and hard-wraps at the terminal width. Stripping those after the fact leaves
duplicated word fragments ("generaliz generalize"), because an erase-line is
semantic rather than decorative. This cost a full generation batch in an
earlier session; the API returns the completion untouched.

Temperature comes from the registry, applied per call, so the `temp` column is
live configuration rather than documentation of intent.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENDPOINT = "http://localhost:11434/api/generate"
REGISTRY = os.path.join(ROOT, ".orchestrator", "experts.tsv")
ROLES = os.path.join(ROOT, ".orchestrator", "experts")


def lookup(name: str) -> tuple[str, float, str]:
    with open(REGISTRY, encoding="utf-8") as fh:
        for line in fh:
            row = line.rstrip("\n").split("\t")
            if len(row) == 4 and row[0] == name:
                return row[1], float(row[2]), row[3]
    sys.exit(f"UNKNOWN_EXPERT: {name}")


def run(expert: str, prompt_path: str, max_lines: int = 0) -> str:
    model, temperature, role_file = lookup(expert)
    with open(os.path.join(ROLES, role_file), encoding="utf-8") as fh:
        role = fh.read()
    with open(prompt_path, encoding="utf-8") as fh:
        packet = fh.read()

    body = json.dumps({
        "model": model,
        "prompt": f"{role}\n\n{packet}",
        "stream": False,
        "keep_alive": "8h",
        "options": {"temperature": temperature},
    }).encode("utf-8")

    request = urllib.request.Request(
        ENDPOINT, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=1800) as response:
            envelope = json.load(response)
    except (urllib.error.URLError, TimeoutError) as exc:
        sys.exit(f"OLLAMA_UNREACHABLE: {exc}")
    if "error" in envelope:
        sys.exit(f"OLLAMA_ERROR: {envelope['error']}")

    text = envelope.get("response", "")
    if max_lines > 0:
        text = "\n".join(text.splitlines()[:max_lines])
    return text


if __name__ == "__main__":
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    sys.stdout.write(run(sys.argv[1], sys.argv[2], limit))
