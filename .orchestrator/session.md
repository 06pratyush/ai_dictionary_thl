## Session 2026-08-29 — CLI feature
Goal: ship the dictionary as an installable package with a `thl` command line.
Baseline: 0 pre-existing failures.
Protocol: CLAUDE_v3 (expert ensemble).

Roster built this session — `gemma4:e4b` and the old 9.6GB `orch-reader` were
replaced, so the v3 roster is now actually installed:

| Handle | Base | Placement |
|---|---|---|
| orch-reader | gemma4:e2b | GPU, resident |
| orch-coder | qwen2.5-coder:7b | GPU |
| orch-heavy | qwen2.5-coder:14b | GPU, escalation |
| orch-prose | llama3 | CPU-pinned, parallel audit lane |

### Units
| # | Task | Route | Expert | Attempts | Audit defects | Verify | Notes |
|---|------|-------|--------|----------|---------------|--------|-------|
| 1 | v3 harness | RETAIN | — | 1 | — | — | expert.py over HTTP API, not `ollama run` |
| 2 | Interface contract | RETAIN | — | 1 | — | — | packet would exceed the artefact (§7.6) |
| 3 | errors.py, __init__.py, plugin.py | RETAIN | — | 1 | — | PASS | under DELEGATION_FLOOR |
| 4 | corpus.py | DELEGATE | implementer | 1 | 4 fixed | PASS | 3 further defects found only by running it |
| 5 | tests/test_corpus.py | DELEGATE | tester | 4 → FAIL_GATE | — | PASS | finished by hand; 2 of 4 attempts wasted on a false-positive gate |
| 6 | search.py | DELEGATE | implementer | in progress | — | — | port of the JS engine |
| 7 | serve.py | RETAIN | — | 1 | — | — | network boundary (§7.6) |
| 8 | pyproject.toml, docs | RETAIN | — | 1 | — | — | packaging and written work |

### Failure patterns → folded into expert role files
- Implements the signature but not the docstring: `load()` read one corpus where
  the contract said both. → added to implementer.md.
- Indexes a contract field with `[]` without checking it exists in the sample
  data: `ngram` is build-derived and absent from the JSON. → added to
  implementer.md.
- Tester asserts against its own synthetic fixture — hard-coded counts and a
  fabricated gloss — after the packet explicitly forbade hard-coded totals.
- Tester invented `FrozenInstanceError` in our errors module; it lives in
  `dataclasses`.

### Harness defects found and fixed (these cost more than any model defect)
- **imports.py checked modules, not names.** `from x.errors import
  FrozenInstanceError` — real module, wrong name — passed the gate and failed at
  collection. Now imports first-party modules and checks the attribute.
- **imports.py had the wrong sys.path.** A script's `sys.path[0]` is its own
  directory, so the package under test was invisible and *every* gated file was
  reported as a hallucinated import. Two of four repair attempts on unit 5 were
  spent chasing that phantom. A false positive in a gate is worse than no gate:
  it sends the repairer to fix something that was never broken.
- **verify.sh matched its own success output.** It grepped `/failed/`, which
  matches the "0 failed" a green run prints, so a fully passing suite reported
  VERIFY_FAIL.

### Decisions
- Dispatch goes through Ollama's HTTP API. `ollama run` emits erase-line codes
  even when redirected; stripping them leaves duplicated word fragments. This
  cost a full generation batch in the previous session.
- Package name `thehallucinatedlab-dictionary`, console script `thl-dict`, and
  an entry point in the `thehallucinatedlab.commands` group so the main toolkit
  mounts the same parser as `thl dict`. The toolkit discovers this package
  rather than depending on it, so neither needs a release to know about the other.
- Bridge port 8788. 8787 is the toolkit's; colliding buys nothing.
- Zero runtime dependencies. Corpora ship in the wheel; the bridge is stdlib
  http.server. A dictionary that needs the network to define a word is a website
  with extra steps.
- `Entry` hashes by identity (`eq=False`). It carries dicts, so a value-based
  hash raises the moment the engine puts one in a set — which it does constantly.
